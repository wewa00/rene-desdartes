#! /usr/bin/env python
import sys
import urllib2
import cv
from threading import Thread
from threading import Event
import time
import math

# some definitions
window_name = "Capture from Cam!"
from_video = True
from_camera = False

def on_mouse(event, x, y, flags, param):
    if event==cv.CV_EVENT_LBUTTONDOWN:
        #events
        global points
        global e
        #counter
        #append user clicked points        
        points.append((x,y))
        e.set()


def CalibrationWindowThread(im):
    cv.ShowImage(window_name, im)

    cv.SetMouseCallback(window_name, on_mouse)
    global key

    while True:
        if not key.is_set():
            cv.WaitKey(1)
        else:
            break

def Calibration():
    global image
    
    if from_video:
        if from_camera:
            capture = cv.CaptureFromCAM(0)
        else:
            capture = cv.CaptureFromFile('darts.wmv')
        image = 0
        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
        cv.GrabFrame(capture)
        image = cv.CloneImage(cv.RetrieveFrame(capture))
    else:
        image = cv.LoadImage(str(r"dartboard_cam1.bmp"),cv.CV_LOAD_IMAGE_COLOR)
        
    new_image = cv.CloneImage(image)

    global points
    points = []

    #use two events to emulate wait for mouse click event
    global e
    global key
    e = Event()
    key = Event()
    t = Thread(target=CalibrationWindowThread,args=(new_image,));
    t.start()

    print "Please select the center of the 20 points outermost rim."
    e.wait()
    e.clear()

    cv.Circle(new_image, points[0], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the center of the 3 points outermost rim."
    e.wait()
    e.clear()

    cv.Circle(new_image, points[1], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the center of the 11 points outermost rim."
    e.wait()
    e.clear()

    cv.Circle(new_image, points[2], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the center of the 6 points outermost rim."
    e.wait()
    e.clear()

    cv.Circle(new_image, points[3], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    #calculate the desired circle dimensions
    newtop = (round(new_image.height/2), round(new_image.height * 0.20))
    newbottom = (round(new_image.height/2), round(new_image.height * 0.80))
    #Note: the height is smaller than the width
    newleft = (round(new_image.height * 0.20), round(new_image.height/2))
    newright = (round(new_image.height * 0.80), round(new_image.height/2))

    global mapping
    mapping = cv.CreateMat(3, 3, cv.CV_32FC1)

    #get a fresh new image
    new_image = cv.CloneImage(image)

    cv.GetPerspectiveTransform([points[0],points[1],points[2],points[3]],[newtop, newbottom, newleft, newright],mapping)
    cv.WarpPerspective(image,new_image,mapping)
    cv.ShowImage(window_name,new_image)

    print "The dartboard image has now been normalized."
    print ""

    global center_dartboard
    center_dartboard = []
    print "Please select the middle of the dartboard. i.e. the middle of the double bull's eye"
    e.wait()
    e.clear()
    center_dartboard = points[4]
    center_dartboard = (int(round(center_dartboard[0])), int(round(center_dartboard[1])))

    cv.Circle(new_image, center_dartboard, 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    init_point_arr = []
    print "Please select the outermost intersection of the 20 points and 1 ponit line."
    e.wait()
    e.clear()
    init_point_arr = points[5]

    cv.Circle(new_image, init_point_arr, 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    #find initial angle of the 20-1 divider
    tempX_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
    #correct the point with respect to the center
    cv.mSet( tempX_mat, 0, 0, init_point_arr[0] - center_dartboard[0] )
    tempY_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
    #adjust the origin of y
    cv.mSet( tempY_mat, 0, 0, init_point_arr[1] - (new_image.height - center_dartboard[1]) )
    init_mag_mat = cv.CreateMat(1, 1, cv.CV_32FC1)
    init_angle_reversed_mat = cv.CreateMat(1, 1, cv.CV_32FC1)

    #each point region is 360/12 = 18 degrees large
    cv.CartToPolar(tempX_mat, tempY_mat, init_mag_mat, init_angle_reversed_mat, angleInDegrees=True)

    global ref_angle
    ref_angle = 360.0 - cv.mGet(init_angle_reversed_mat, 0, 0)
    global ref_mag
    ref_mag = cv.mGet(init_mag_mat, 0, 0)

    #print cv.mGet(init_mag_mat, 0, 0)
    #print "Initial angle"
    #print init_angle_val

    #display dividers
    current_point = (int(round(init_point_arr[0])), int(round(init_point_arr[1])))
    next_angle = cv.CreateMat(1, 1, cv.CV_32FC1)
    cv.mSet( next_angle, 0, 0, 360 - ref_angle )
    temp_angle = 360.0 - ref_angle
    #draw point dividers counterclockwise, just like how angle is calculated, arctan(y/x)
    for i in range(0, 20):
        cv.Line(new_image, center_dartboard, current_point, cv.CV_RGB(0, 0, 255), 1, 8)
        #calculate the cartesian coordinate of the next point divider
        temp_angle = 360.0 - temp_angle
        temp_angle += 18.0
        if temp_angle >= 360.0:
            temp_angle -= 360.0
        #make temp_angle reversed
        temp_angle = 360.0 - temp_angle
        #print temp_angle
        cv.mSet( next_angle, 0, 0, temp_angle )
        
        cv.PolarToCart(init_mag_mat, next_angle, tempX_mat, tempY_mat, angleInDegrees=True)

        #current_point = []
        #adjust the cartesian points
        current_point = ( int(round( cv.mGet( tempX_mat, 0, 0) + center_dartboard[0] )), int(round( cv.mGet( tempY_mat, 0, 0) + (new_image.height - center_dartboard[1]) ) ))
        #print current_point
        
    cv.ShowImage(window_name,new_image)
    
    ring_arr = []
    print "Please select the first ring (any point). i.e. the ring that encloses the double bull's eye."
    e.wait()
    e.clear()
    ring_arr.append(points[6])

    cv.Circle(new_image, points[6], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the second ring (any point). i.e. the ring that encloses the bull's eye."
    e.wait()
    e.clear()
    ring_arr.append(points[7])

    cv.Circle(new_image, points[7], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the third ring (any point). i.e. the closer ring that encloses the triple score region."
    e.wait()
    e.clear()
    ring_arr.append(points[8])

    cv.Circle(new_image, points[8], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the fourth ring (any point). i.e. the further ring that encloses the triple score region."
    e.wait()
    e.clear()
    ring_arr.append(points[9])

    cv.Circle(new_image, points[9], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the fifth ring (any point). i.e. the closer ring that encloses the double score region."
    e.wait()
    e.clear()
    ring_arr.append(points[10])

    cv.Circle(new_image, points[10], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    print "Please select the sixth ring (any point). i.e. the further ring that encloses the double score region."
    e.wait()
    e.clear()
    ring_arr.append(points[11])

    cv.Circle(new_image, points[11], 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage(window_name, new_image)

    global ring_radius
    ring_radius = []
    for i in range(0,6):
        #find the radius of the ring
        ring_radius.append(int(math.sqrt(( ring_arr[i][0] - center_dartboard[0] )** 2 + (ring_arr[i][1] - center_dartboard[1] )** 2)))
        #display the rings
        cv.Circle(new_image, center_dartboard, ring_radius[i], cv.CV_RGB(0, 255, 0), 1, 8)
        
    cv.ShowImage(window_name,new_image)
    
    e.wait()

    #destroy calibration window
    key.set()

    global calibrationComplete
    calibrationComplete = True

    #wait a key pressed to end
    # cv.WaitKey(0)

if __name__ == '__main__':
    print "Welcome to darts!"
    Calibration()

