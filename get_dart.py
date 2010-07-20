#! /usr/bin/env python
import cv
from threading import Thread
from threading import Event

import dartRegion
import calibration
import GameEngine

# some definitions
window_name = "Get Dart Location"
debug = True
from_camera = True

def on_mouse(event, x, y, flags, param):
    if event==cv.CV_EVENT_LBUTTONDOWN:
        global mouse_click_down
        global x_coordinate
        global y_coordinate
        x_coordinate = x
        y_coordinate = y
        mouse_click_down.set()

def GetDart():
    if debug:
        if from_camera:
            capture = cv.CaptureFromCAM(0)
            cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
            cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
            image = 0

            cv.GrabFrame(capture)
            image = cv.RetrieveFrame(capture)           
        else:            
            #image = cv.LoadImage(str(r"Dartboard Left.jpg"),cv.CV_LOAD_IMAGE_COLOR)
            image = calibration.image   

        # the coordinates
        global x_coordinate
        global y_coordinate
        x_coordinate = 0
        y_coordinate = 0

        #use this events wait for mouse click
        global mouse_click_down
        mouse_click_down = Event()

        cv.NamedWindow(window_name, 1)
        cv.SetMouseCallback(window_name, on_mouse)
        
        while not mouse_click_down.is_set():
            if from_camera:
                cv.GrabFrame(capture)
                image = cv.RetrieveFrame(capture)
            cv.ShowImage(window_name, image)
            cv.WaitKey(1)
        mouse_click_down.clear()

        cv.Circle(image,(x_coordinate,y_coordinate),3,cv.CV_RGB(255, 0, 0),2)
        cv.ShowImage(window_name, image)

        return (x_coordinate,y_coordinate)
    else: 
        pass

if __name__ == '__main__':
    #calibrate first
    calibration.Calibration()

    print "Click on a location to simulate a dart throw!"

    raw_dart_location = []
    raw_dart_location = GetDart()
    
    print raw_dart_location

    correct_dart_location = dartRegion.DartLocation(raw_dart_location)

    print correct_dart_location

    new_image = cv.CloneImage(calibration.image)
    
    cv.WarpPerspective(calibration.image, new_image, calibration.mapping)
    cv.Circle(new_image, correct_dart_location, 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage("new dart location",new_image)

    dartThrowInfo = GameEngine.dartThrow()
    dartThrowInfo = dartRegion.DartRegion(correct_dart_location)

    print "The dart's score:"
    print dartThrowInfo.score
    print "The dart's multiplier:"
    print dartThrowInfo.multiplier
    print "The dart's magnitude:"
    print dartThrowInfo.magnitude
    print "The dart's angle:"
    print dartThrowInfo.angle
    
    cv.WaitKey(0)
