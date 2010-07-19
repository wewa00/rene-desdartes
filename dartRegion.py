
import sys
import cv
import calibration
import GameEngine

def DartLocation(raw_dart_loc):
    try:
        if calibration.calibrationComplete:
            print "Raw dart location:"
            print raw_dart_loc

#            temp_raw_loc = cv.CreateMat(3, 3, cv.CV_32FC1)
#            cv.mSet(temp_raw_loc, 0, 0, float(raw_dart_loc[0]))
#            cv.mSet(temp_raw_loc, 0, 1, float(raw_dart_loc[1]))
#            cv.mSet(temp_raw_loc, 0, 2, 1.0)
#
#            temp_new_loc = cv.CreateMat(3, 3, cv.CV_32FC1)
#
#            cv.Mul(calibration.mapping, temp_raw_loc, temp_new_loc, 1)
#
#            new_dart_loc = []
#            new_dart_loc = (int( cv.mGet(temp_new_loc, 0, 0)/cv.mGet(temp_new_loc, 0, 2) ), int( cv.mGet(temp_new_loc, 0, 1)/cv.mGet(temp_new_loc, 0, 2) ))

            raw_loc_mat = cv.CreateMat(calibration.image.height, calibration.image.width, cv.CV_32FC1)
            new_loc_mat = cv.CreateMat(calibration.image.height, calibration.image.width, cv.CV_32FC1)
            #y comes before x
            cv.mSet( raw_loc_mat, raw_dart_loc[1], raw_dart_loc[0], 1.0 )
            cv.WarpPerspective(raw_loc_mat, new_loc_mat, calibration.mapping)

            for i in range (0, calibration.image.width):
                for j in range(0, calibration.image.height):
                    if not (cv.mGet(new_loc_mat, j, i) == 0.0):
                        new_dart_loc = (i, j)
                        break

            print "New dart location:"
            return new_dart_loc

    #system not calibrated
    except AttributeError as err1:
        print err1
        return (-1, -1)

    except NameError as err2:
        #not calibrated error
        print err2
        return (-2, -2)

def DartRegion(dart_loc):
    try:
        if calibration.calibrationComplete:
            print "Finding dart throw information"
            dartInfo = GameEngine.dartThrow()

            #find the magnitude and angle of the dart
            tempX_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
            cv.mSet( tempX_mat, 0, 0, dart_loc[0] - calibration.center_dartboard[0] )
            tempY_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
            #adjust the origin of y to fit a Cartesian plane
            cv.mSet( tempY_mat, 0, 0, dart_loc[1] - (calibration.image.height - calibration.center_dartboard[1]) )
            dart_mag_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
            dart_angle_reversed_mat = cv.CreateMat(1, 1, cv.CV_32FC1)

            #each point region is 360/12 = 18 degrees large
            cv.CartToPolar(tempX_mat, tempY_mat, dart_mag_mat, dart_angle_reversed_mat, angleInDegrees=True)

            dart_angle_val = 360.0 - cv.mGet(dart_angle_reversed_mat, 0, 0)

            dartInfo.magnitude = cv.mGet(dart_mag_mat, 0, 0)
            dartInfo.angle = dart_angle_val

            #Calculating score:
            #Find base point
            if dart_angle_val < calibration.init_angle_val:         #make sure dart's angle is always greater
                dart_angle_val += 360.0
                
            angleDiffMul = int((dart_angle_val - calibration.init_angle_val) / 18.0)

            #starting from the 20 points
            if angleDiffMul == 0:
                dartInfo.score = 20
            elif angleDiffMul == 1:
                dartInfo.score = 5
            elif angleDiffMul == 2:
                dartInfo.score = 12
            elif angleDiffMul == 3:
                dartInfo.score = 9
            elif angleDiffMul == 4:
                dartInfo.score = 14
            elif angleDiffMul == 5:
                dartInfo.score = 11
            elif angleDiffMul == 6:
                dartInfo.score = 8
            elif angleDiffMul == 7:
                dartInfo.score = 16
            elif angleDiffMul == 8:
                dartInfo.score = 7
            elif angleDiffMul == 9:
                dartInfo.score = 19
            elif angleDiffMul == 10:
                dartInfo.score = 3
            elif angleDiffMul == 11:
                dartInfo.score = 17
            elif angleDiffMul == 12:
                dartInfo.score = 2
            elif angleDiffMul == 13:
                dartInfo.score = 15
            elif angleDiffMul == 14:
                dartInfo.score = 10
            elif angleDiffMul == 15:
                dartInfo.score = 9
            elif angleDiffMul == 16:
                dartInfo.score = 13
            elif angleDiffMul == 17:
                dartInfo.score = 4
            elif angleDiffMul == 18:
                dartInfo.score = 18
            elif angleDiffMul == 19:
                dartInfo.score = 1
            else:
                #something went wrong
                dartInfo.score = -300

            #Calculating multiplier (and special cases for Bull's Eye):

            tempX_mat = cv.CreateMat(1, len(calibration.ring_arr), cv.CV_32FC1)
            tempY_mat = cv.CreateMat(1, len(calibration.ring_arr), cv.CV_32FC1)
            for i in range(0, len(calibration.ring_arr)):
                #the magnitude is in reference to the center
                cv.mSet( tempX_mat, 0, i, calibration.ring_arr[i][0] - calibration.center_dartboard[0])
                cv.mSet( tempY_mat, 0, i, calibration.ring_arr[i][1] - calibration.center_dartboard[1])

            ring_mag = cv.CreateMat(1, len(calibration.ring_arr), cv.CV_32FC1)
            ring_angle = cv.CreateMat(1, len(calibration.ring_arr), cv.CV_32FC1)        #not needed

            cv.CartToPolar(tempX_mat, tempY_mat, ring_mag, ring_angle, angleInDegrees=True)

            for i in range(0, len(calibration.ring_arr)):
                print cv.mGet( ring_mag, 0, i )
                #Find the ring that encloses the dart
                if dartInfo.magnitude <= cv.mGet( ring_mag, 0, i ):
                    #Bull's eye, adjust base score
                    if i == 0:
                        dartInfo.score = 25
                        dartInfo.multiplier = 2
                    elif i == 1:
                        dartInfo.score = 25
                        dartInfo.multiplier = 1
                    #triple ring
                    elif i == 3:
                        dartInfo.multiplier = 3
                    #double ring
                    elif i == 5:
                        dartInfo.multiplier = 2
                    #single
                    elif i == 2 or i == 4:
                        dartInfo.multiplier = 1
                    #finished calculation
                    break

            #miss
            if dartInfo.magnitude > cv.mGet( ring_mag, 0, 5 ):
                dartInfo.score = 0
                dartInfo.multiplier = 0

            return dartInfo


    #system not calibrated
    except AttributeError as err1:
        print err1
        dartInfo = GameEngine.dartThrow()
        return dartInfo

    except NameError as err2:
        #not calibrated error
        print err2
        dartInfo = GameEngine.dartThrow()
        return dartInfo
    

if __name__ == '__main__':
    print "Welcome to darts!"
    calibration.Calibration()

    print DartRegion(calibration.center_dartboard)