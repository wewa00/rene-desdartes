import os
#! /usr/bin/env python
import sys
import urllib2
import cv
from threading import Thread
from threading import Event
import time
import math
import pickle
import os.path

# some definitions
window_name = "Capture from Cam!"
prev_calibration_window = "Previous Calibration"
debug = False
from_video = True
from_camera = True
videofile = 'video3.avi'
cascadefile = 'new_pos_1238.neg_boards_1927.cascade_17.xml'

def on_mouse(event, x, y, flags, param):
    if event==cv.CV_EVENT_LBUTTONDOWN:
        #events
        global points
        global e
        #counter
        #append user clicked points        
        points.append((x,y))
        e.set()

#shows the image with opencv highgui, exits by setting key from programming
def CalibrationWindowThread(im):
    cv.ShowImage(window_name, im)

    cv.SetMouseCallback(window_name, on_mouse)
    global key

    while True:
        if not key.is_set():
            cv.WaitKey(1)
        else:
            break

#shows the image with opencv highgui, exits by getting a keypress
def CalibrationWindowThread2(im):
    cv.ShowImage(prev_calibration_window, im)

    global keyPress
    #events for synchronization
    global keyPressEvent
    global windowReady
    global drawingFinished
    #initialize to no keys pressed
    keyPress = -1

    #this thread has now been setup
    windowReady.set()
    #now wait for drawings to be filled
    drawingFinished.wait()

    #waits indefinitely for a key press, -1 for no keys pressed
    while keyPress == -1:
        keyPress = cv.WaitKey(1)

    #grabbed a key press, signal and exit now
    keyPressEvent.set()
    

#For file IO
class CalibrationData:
    def __init__(self):
        #for perspective transform
        self.top = []
        self.bottom = []
        self.left = []
        self.right = []
        #for calculating the first angle
        self.init_point_arr = []
        self.center_dartboard = []
        #initial angle of the 20 / 1 points divider
        self.ref_angle = []
        #radii of the rings, there are 6 in total
        self.ring_radius = []

def Calibration():
    global image
    
    if from_video:
        if from_camera:
            capture = cv.CaptureFromCAM(0)
        else:
            capture = cv.CaptureFromFile(videofile)
##        image = 0
        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

        if from_camera:
    ##we wait for 40 frames...the picture at the very start is always kind of weird,
    ##wait for the picture to stabalize
            for n in range(40):
    ##            RetrieveFrame is just GrabFrame and RetrieveFrame combined into 1
    ##            function call
                image = cv.QueryFrame(capture)
    ##            cv.GrabFrame(capture)
    ##            image = cv.CloneImage(cv.RetrieveFrame(capture))
                
            ## need to clone this image...otherwise once the capture gets released we won't have access
            ## to the image anymore
            image = cv.CloneImage(cv.QueryFrame(capture))
        else:
##            if we're capturing from a video file, then just take the first frame
            image = cv.QueryFrame(capture)
    else:
        image = cv.LoadImage(str(r"dartboard_cam1.bmp"),cv.CV_LOAD_IMAGE_COLOR)
        

    #data we need for calibration:
    #mapping for a perspective transform
    global mapping
    #center of the dartboard in x, y form
    global center_dartboard
    #initial angle of the 20 - 1 points divider
    global ref_angle
    #the radii of the rings, there are 6 of them
    global ring_radius
    global calibrationComplete
    calibrationComplete = False

    #for grabbing the user's clicks
    global points

    #either grab data from file or user
    while calibrationComplete == False:
        #Read calibration file, if exists
        if os.path.isfile("calibrationData.pkl"):
            try:
                #for grabbing key presses in the python window showing the image
                global keyPressEvent
                keyPressEvent = Event()
                global keyPress
                #for synchronizing the image window thread
                global windowReady
                windowReady = Event()
                #for synchronizing the drawing
                global drawingFinished
                drawingFinished = Event()

                #start a fresh set of points
                points = []
                
                calFile = open('calibrationData.pkl', 'rb')
                calData = CalibrationData()
                calData = pickle.load(calFile)
                #load the data into the global variables
                points.append(calData.top)
                points.append(calData.bottom)
                points.append(calData.left)
                points.append(calData.right)    #index of 3
                init_point_arr = calData.init_point_arr
                center_dartboard = calData.center_dartboard
                ref_angle = calData.ref_angle
                ring_radius = []
                ring_radius.append(calData.ring_radius[0])
                ring_radius.append(calData.ring_radius[1])
                ring_radius.append(calData.ring_radius[2])
                ring_radius.append(calData.ring_radius[3])
                ring_radius.append(calData.ring_radius[4])
                ring_radius.append(calData.ring_radius[5])      #append the 6 ring radii
                #close the file once we are done reading the data
                calFile.close()

                #copy image for old calibration data
                new_image = cv.CloneImage(image)

                #have the image in another window and thread
                t = Thread(target=CalibrationWindowThread2,args=(new_image,));
                t.start()
                #wait for the image window to setup
                windowReady.wait()
                
                #now draw them out:
                #*******************1. Transform image******************************
                newtop = (round(new_image.height/2), round(new_image.height * 0.20))
                newbottom = (round(new_image.height/2), round(new_image.height * 0.80))
                #Note: the height is smaller than the width
                newleft = (round(new_image.height * 0.20), round(new_image.height/2))
                newright = (round(new_image.height * 0.80), round(new_image.height/2))

                mapping = cv.CreateMat(3, 3, cv.CV_32FC1)

                #get a fresh new image
                new_image = cv.CloneImage(image)

                cv.GetPerspectiveTransform([points[0],points[1],points[2],points[3]],[newtop, newbottom, newleft, newright],mapping)
                cv.WarpPerspective(image,new_image,mapping)
                cv.ShowImage(prev_calibration_window,new_image)
                #*******************************************************************


                #********************2.Draw points dividers*************************
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

                cv.ShowImage(prev_calibration_window,new_image)
                #*************************************************************************


                #**********************3. Draw rings**************************************
                for i in range(0,6):
                    #display the rings
                    cv.Circle(new_image, center_dartboard, ring_radius[i], cv.CV_RGB(0, 255, 0), 1, 8)

                cv.ShowImage(prev_calibration_window,new_image)
                #*************************************************************************

                #we are finished drawing, signal
                drawingFinished.set()

                #wait for key press
                print "Previous calibration data detected. Would you like to keep this calibration data? Press 'y' for yes"
                #wait indefinitely for a key press
                keyPressEvent.wait()

                #ASCII 121 is character 'y'
                if keyPress == 121:
                    #we are good with the previous calibration data
                    calibrationComplete = True
                else:
                    calibrationComplete = False
                    #delete the calibration file and start over
                    os.remove("calibrationData.pkl")

            #corrupted file
            except EOFError as err:
                print err

        #Manual calibration
        else:
            #use two events to emulate wait for mouse click event
            global e
            global key
            e = Event()
            key = Event()

            #start a fresh set of points
            points = []

            #copy image for manual calibration
            new_image = cv.CloneImage(image)

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

            mapping = cv.CreateMat(3, 3, cv.CV_32FC1)

            #get a fresh new image
            new_image = cv.CloneImage(image)

            cv.GetPerspectiveTransform([points[0],points[1],points[2],points[3]],[newtop, newbottom, newleft, newright],mapping)
            cv.WarpPerspective(image,new_image,mapping)
            cv.ShowImage(window_name,new_image)

            print "The dartboard image has now been normalized."
            print ""

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

            #save valuable calibration data into a structure
            calData = CalibrationData()
            calData.top = points[0]
            calData.bottom = points[1]
            calData.left = points[2]
            calData.right = points[3]
            calData.center_dartboard = center_dartboard
            calData.init_point_arr = init_point_arr
            calData.ref_angle = ref_angle
            calData.ring_radius = ring_radius

            #write the calibration data to a file
            calFile = open("calibrationData.pkl", "wb")
            pickle.dump(calData, calFile, 0)
            calFile.close()

            calibrationComplete = True

        #wait a key pressed to end
        # cv.WaitKey(0)

if __name__ == '__main__':
    print "Welcome to darts!"
    Calibration()

