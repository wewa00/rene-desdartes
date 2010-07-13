
import sys
import cv
import calibration

def DartRegion(x, y):
    try:
        if calibration.calibrationComplete:
            return calibration.points[0]
    #could not find calibratoinComplete
    except AttributeError:
        return "Miss!"


if __name__ == '__main__':
    print "Welcome to darts!"
    calibration.Calibration()

    print DartRegion(10, 10)