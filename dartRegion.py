
import sys
import cv
import calibration
import GameEngine
from random import randint, random

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
            print new_dart_loc
            return new_dart_loc

    #system not calibrated
    except AttributeError as err1:
        print err1
        return (-1, -1)

    except NameError as err2:
        #not calibrated error
        print err2
        return (-2, -2)


#Returns dartThrow (score, multiplier, angle, magnitude) based on x,y location
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
            if dart_angle_val < calibration.ref_angle:         #make sure dart's angle is always greater
                dart_angle_val += 360.0
                
            angleDiffMul = int((dart_angle_val - calibration.ref_angle) / 18.0)

            #starting from the 20 points
            if angleDiffMul == 0:
                dartInfo.base = 20
            elif angleDiffMul == 1:
                dartInfo.base = 5
            elif angleDiffMul == 2:
                dartInfo.base = 12
            elif angleDiffMul == 3:
                dartInfo.base = 9
            elif angleDiffMul == 4:
                dartInfo.base = 14
            elif angleDiffMul == 5:
                dartInfo.base = 11
            elif angleDiffMul == 6:
                dartInfo.base = 8
            elif angleDiffMul == 7:
                dartInfo.base = 16
            elif angleDiffMul == 8:
                dartInfo.base = 7
            elif angleDiffMul == 9:
                dartInfo.base = 19
            elif angleDiffMul == 10:
                dartInfo.base = 3
            elif angleDiffMul == 11:
                dartInfo.base = 17
            elif angleDiffMul == 12:
                dartInfo.base = 2
            elif angleDiffMul == 13:
                dartInfo.base = 15
            elif angleDiffMul == 14:
                dartInfo.base = 10
            elif angleDiffMul == 15:
                dartInfo.base = 6
            elif angleDiffMul == 16:
                dartInfo.base = 13
            elif angleDiffMul == 17:
                dartInfo.base = 4
            elif angleDiffMul == 18:
                dartInfo.base = 18
            elif angleDiffMul == 19:
                dartInfo.base = 1
            else:
                #something went wrong
                dartInfo.base = -300

            #Calculating multiplier (and special cases for Bull's Eye):
            for i in range(0, len(calibration.ring_radius)):
                print calibration.ring_radius[i]
                #Find the ring that encloses the dart
                if dartInfo.magnitude <= calibration.ring_radius[i]:
                    #Bull's eye, adjust base score
                    if i == 0:
                        dartInfo.base = 25
                        dartInfo.multiplier = 2
                    elif i == 1:
                        dartInfo.base = 25
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
            if dartInfo.magnitude > calibration.ring_radius[5]:
                dartInfo.base = 0
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


#Finds score and multiplier based on angle and magnitude
def LocationToRegion(angle, magnitude):
    try:
        if calibration.calibrationComplete:
            print "Finding dart throw information"

            dartInfo = GameEngine.dartThrow()

            angleDiffMul = int((angle - calibration.ref_angle) / 18.0)

            #starting from the 20 points
            if angleDiffMul == 0:
                dartInfo.base = 20
            elif angleDiffMul == 1:
                dartInfo.base = 5
            elif angleDiffMul == 2:
                dartInfo.base = 12
            elif angleDiffMul == 3:
                dartInfo.base = 9
            elif angleDiffMul == 4:
                dartInfo.base = 14
            elif angleDiffMul == 5:
                dartInfo.base = 11
            elif angleDiffMul == 6:
                dartInfo.base = 8
            elif angleDiffMul == 7:
                dartInfo.base = 16
            elif angleDiffMul == 8:
                dartInfo.base = 7
            elif angleDiffMul == 9:
                dartInfo.base = 19
            elif angleDiffMul == 10:
                dartInfo.base = 3
            elif angleDiffMul == 11:
                dartInfo.base = 17
            elif angleDiffMul == 12:
                dartInfo.base = 2
            elif angleDiffMul == 13:
                dartInfo.base = 15
            elif angleDiffMul == 14:
                dartInfo.base = 10
            elif angleDiffMul == 15:
                dartInfo.base = 6
            elif angleDiffMul == 16:
                dartInfo.base = 13
            elif angleDiffMul == 17:
                dartInfo.base = 4
            elif angleDiffMul == 18:
                dartInfo.base = 18
            elif angleDiffMul == 19:
                dartInfo.base = 1
            else:
                #something went wrong
                dartInfo.base = -300

            #Calculating multiplier (and special cases for Bull's Eye):
            for i in range(0, len(calibration.ring_radius)):
                print calibration.ring_radius[i]
                #Find the ring that encloses the dart
                if magnitude <= calibration.ring_radius[i]:
                    #Bull's eye, adjust base score
                    if i == 0:
                        dartInfo.base = 25
                        dartInfo.multiplier = 2
                    elif i == 1:
                        dartInfo.base = 25
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
            if magnitude > calibration.ring_radius[5]:
                dartInfo.base = 0
                dartInfo.multiplier = 0

            return (dartInfo.base, dartInfo.multiplier)
        

    #system not calibrated
    except AttributeError as err1:
        print err1
        return (-1, -1)

    except NameError as err2:
        print err2
        return (-2, -2)


#Given a score region, this function returns the ideal location to aim
def RegionToLocation(score, multiplier):
    try:
        if calibration.calibrationComplete:
            dart_mag = 0
            dart_angle = 0
            angle_increment = 18.0
            # this is the angle of the middle of the 20 point region
            ref_dart_angle = (calibration.ref_angle + (calibration.ref_angle + angle_increment)) / 2

            if score == 20:
                dart_angle = ref_dart_angle + 0*angle_increment
            elif score == 5:
                dart_angle = ref_dart_angle + 1*angle_increment
            elif score == 12:
                dart_angle = ref_dart_angle + 2*angle_increment
            elif score == 9:
                dart_angle = ref_dart_angle + 3*angle_increment
            elif score == 14:
                dart_angle = ref_dart_angle + 4*angle_increment
            elif score == 11:
                dart_angle = ref_dart_angle + 5*angle_increment
            elif score == 8:
                dart_angle = ref_dart_angle + 6*angle_increment
            elif score == 16:
                dart_angle = ref_dart_angle + 7*angle_increment
            elif score == 7:
                dart_angle = ref_dart_angle + 8*angle_increment
            elif score == 19:
                dart_angle = ref_dart_angle + 9*angle_increment
            elif score == 3:
                dart_angle = ref_dart_angle + 10*angle_increment
            elif score == 17:
                dart_angle = ref_dart_angle + 11*angle_increment
            elif score == 2:
                dart_angle = ref_dart_angle + 12*angle_increment
            elif score == 15:
                dart_angle = ref_dart_angle + 13*angle_increment
            elif score == 10:
                dart_angle = ref_dart_angle + 14*angle_increment
            elif score == 6:
                dart_angle = ref_dart_angle + 15*angle_increment
            elif score == 13:
                dart_angle = ref_dart_angle + 16*angle_increment
            elif score == 4:
                dart_angle = ref_dart_angle + 17*angle_increment
            elif score == 18:
                dart_angle = ref_dart_angle + 18*angle_increment
            elif score == 1:
                dart_angle = ref_dart_angle + 19*angle_increment
            else:
                dart_angle = -1

            #miss
            if multiplier == 1:
                #always aim at the bigger region
                dart_mag = calibration.ring_radius[3] + calibration.ring_radius[4]
            elif multiplier == 2:
                dart_mag = calibration.ring_radius[4] + calibration.ring_radius[5]
            elif multiplier == 3:
                dart_mag = calibration.ring_radius[2] + calibration.ring_radius[3]
            else:
                dart_mag = 0

            #special cases: bull's eye and double bull's eye
            if score == 25:
                if multiplier == 1:
                    dart_mag = calibration.ring_radius[0] + calibration.ring_radius[1]
                    dart_angle = randint(0, 360)
                elif multiplier == 2:
                    dart_mag = 0
                    dart_angle = 0

            return (dart_mag, dart_angle)
        

    #system not calibrated
    except AttributeError as err1:
        print err1
        return (-1, -1)

    except NameError as err2:
        print err2
        return (-2, -2)

if __name__ == '__main__':
    print "Welcome to darts!"
    calibration.Calibration()

    print DartRegion(calibration.center_dartboard)
