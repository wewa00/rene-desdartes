#! /usr/bin/env python
#import sys
#import urllib2
import cv
from threading import Thread
from threading import Event
#import time
#import math
import dartRegion
import calibration

# some definitions
window_name = "Get Dart Location"

def on_mouse(event, x, y, flags, param):
    if event==cv.CV_EVENT_LBUTTONDOWN:
##        print "x-pos: %d" % x
##        print "y-pos: %d" % y

        #events
        #global points
        global mouse_click_down
        global x_coordinate
        global y_coordinate
        x_coordinate = x
        y_coordinate = y
        #counter
        #append user clicked points
        #points.append((x,y))
        mouse_click_down.set()


def GetDartWindowThread(im):
    cv.ShowImage(window_name, im)

    cv.SetMouseCallback(window_name, on_mouse)
    global done_clicking

    while True:
        if not done_clicking.is_set():
            cv.WaitKey(1)
        else:
            break

    global x_coordinate
    global y_coordinate
    cv.Circle(im,(x_coordinate,y_coordinate),3,cv.CV_RGB(255, 0, 0),2)
    cv.ShowImage(window_name, im)
    cv.WaitKey(0)

def GetDart():
        #capture = cv.CaptureFromCAM(0)
    #image = 0

    #cv.GrabFrame(capture)
    #image = cv.RetrieveFrame(capture)
    #cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
    #cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 720)
    image = cv.LoadImage(str(r"Dartboard Left.jpg"),cv.CV_LOAD_IMAGE_COLOR)

    # the coordinates
    global x_coordinate
    global y_coordinate
    x_coordinate = 0
    y_coordinate = 0

    #use two events to emulate wait for mouse click event
    global mouse_click_down
    global done_clicking
    mouse_click_down = Event()
    done_clicking = Event()
    t = Thread(target=GetDartWindowThread,args=(image,));
    t.start()

    mouse_click_down.wait()
    mouse_click_down.clear()
    #cv.Circle(image,(x_coordinate,y_coordinate),1,cv.CV_RGB(255, 0, 0),5)
    #cv.ShowImage(window_name,image)


    #destroy GetDart window
    done_clicking.set()

    #wait a key pressed to end
    #cv.WaitKey(0)
    return (x_coordinate,y_coordinate)

if __name__ == '__main__':
    #calibrate first
    calibration.Calibration()

    print "Click on a location to simulate a dart throw!"

    raw_dart_location = []
    raw_dart_location = GetDart()
    
    print raw_dart_location

    correct_dart_location = dartRegion.DartRegion(raw_dart_location)

    print correct_dart_location

    new_image = cv.CloneImage(calibration.image)
    cv.WarpPerspective(calibration.image, new_image, calibration.mapping)
    cv.Circle(new_image, correct_dart_location, 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage("new dart location",new_image)
    
    cv.WaitKey(0)
