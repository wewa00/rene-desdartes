
import sys
import cv
import calibration
import GameEngine

def DartRegion(raw_dart_loc):
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


if __name__ == '__main__':
    print "Welcome to darts!"
    calibration.Calibration()

    print DartRegion(calibration.center_dartboard)