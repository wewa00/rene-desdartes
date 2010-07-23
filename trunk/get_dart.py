#! /usr/bin/env python
import cv
import time
from math import radians
from threading import Event
from optparse import OptionParser

import dartRegion
import calibration
import GameEngine

# some definitions
window_name = "Get Dart Location"
##debug = True
##from_video = False
##from_camera = False
videofile = 'darts.wmv'
cascadefile = 'crude.xml'
capture = 0
init_get_dart_wait = 40
initialized = False

CLOCKS_PER_SEC = 1.0
MHI_DURATION = 0.1

N = 4
buf = range(10) 
last = 0
mhi = None # MHI
mask = None # valid orientation mask

min_size = (23, 23)
image_scale = 2
haar_scale = 1.1
min_neighbors = 3
haar_flags = 0

pixels_lo_bound = 200
pixels_hi_bound = 2500
dart_tip_threshold = 3

def detect(img, cascade,found_rectangles):
    # allocate temporary images
    small_img = cv.CreateImage((cv.Round(img.width / image_scale),
			       cv.Round (img.height / image_scale)), 8, 1)

    # scale input image for faster processing
    cv.Resize(img, small_img, cv.CV_INTER_LINEAR)

    cv.EqualizeHist(small_img, small_img)

    if(cascade):
        dart = cv.HaarDetectObjects(small_img, cascade, cv.CreateMemStorage(0),
                                     haar_scale, min_neighbors, haar_flags, min_size)
        if dart:
            for ((x, y, w, h), n) in dart:
                found_rectangles.append((x*image_scale,y*image_scale, w*image_scale, h*image_scale))

def update_mhi(img, dst, diff_threshold):
    global last
    global mhi
    global mask
    timestamp = time.clock() / CLOCKS_PER_SEC # get current time in seconds
    size = cv.GetSize(img) # get current frame size
    idx1 = last
    if not mhi or cv.GetSize(mhi) != size:
        for i in range(N):
            buf[i] = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
            cv.Zero(buf[i])
        mhi = cv.CreateImage(size,cv. IPL_DEPTH_32F, 1)
        cv.Zero(mhi) # clear MHI at the beginning
        mask = cv.CreateImage(size,cv. IPL_DEPTH_8U, 1)
    
    cv.CvtColor(img, buf[last], cv.CV_BGR2GRAY) # convert frame to grayscale
    idx2 = (last + 1) % N # index of (last - (N-1))th frame
    last = idx2
    silh = buf[idx2]
    cv.AbsDiff(buf[idx1], buf[idx2], silh) # get difference between frames
    cv.Threshold(silh, silh, diff_threshold, 1, cv.CV_THRESH_BINARY) # and threshold it
    cv.UpdateMotionHistory(silh, mhi, timestamp, MHI_DURATION) # update MHI
    cv.CvtScale(mhi, mask, 255./MHI_DURATION,
                (MHI_DURATION - timestamp)*255./MHI_DURATION)
    cv.Zero(dst)
    cv.Merge(mask, None, None, None, dst)

def non_zero_in_conv_table(image, x, y):
    conv_table_length = 3
    shift = (conv_table_length -1) /2
    
    if x < shift:
        x_orig = 0
    else:
        x_orig = x - shift

    if y < shift:
        y_orig = 0
    else:
        y_orig = y - shift
        
    return cv.CountNonZero(cv.GetSubRect(image,(x_orig,y_orig,conv_table_length,conv_table_length)))

def on_mouse(event, x, y, flags, param):
    if event==cv.CV_EVENT_LBUTTONDOWN:
        global mouse_click_down
        global x_coordinate
        global y_coordinate
        x_coordinate = x
        y_coordinate = y
        mouse_click_down.set()

def InitGetDart():
    global image
    global initialized
    
    if calibration.from_video:
        global capture
        if capture == 0:
            if calibration.from_camera:
                capture = cv.CaptureFromCAM(0)
            else:
                capture = cv.CaptureFromFile(videofile)
                
            cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
            cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
##if we're capturing live from camera, wait a few frames until the feed stabilizes
            if calibration.from_camera:
                for n in range(init_get_dart_wait):
                    image = cv.QueryFrame(capture)
##        image = 0

##        cv.GrabFrame(capture)
##        image = cv.RetrieveFrame(capture)           
    else:            
        #image = cv.LoadImage(str(r"Dartboard Left.jpg"),cv.CV_LOAD_IMAGE_COLOR)
        image = calibration.image
        
    initialized = True

def GetRawDartXY():
    global capture
    global image
        
    if calibration.debug:
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
            if calibration.from_video:
                cv.GrabFrame(capture)
                image = cv.RetrieveFrame(capture)
            cv.ShowImage(window_name, image)
            cv.WaitKey(1)
        mouse_click_down.clear()

##        clone = cv.CloneImage(image)
##
##        cv.Circle(clone,(x_coordinate,y_coordinate),3,cv.CV_RGB(255, 0, 0),2)
##        cv.ShowImage(window_name, clone)
         
        return (x_coordinate,y_coordinate)
    
    else:
        motion = 0
##        capture = 0
        darts_found = list()
        detected_x = 0;
        detected_y = 0;
        no_dart_prev = True
        no_dart_prev_prev = True
##        draw = False

##        parser = OptionParser(usage = "usage: %prog [options]")
##        parser.add_option("-c", "--cascade", action="store", dest="cascade", type="str", help="Haar cascade file, default %default", default = "default.xml")
##        parser.add_option("-f", "--videofile", action="store", dest="videofile", type="str", help="Video capture file, default is to capture from camera", default = None)
##        
##        (options, args) = parser.parse_args()
##
##        cascade = cv.Load(options.cascade)
##        videofile = options.videofile
##
##        if videofile == None:
##            capture = cv.CreateCameraCapture(0)
##        else:
##            capture = cv.CaptureFromFile(videofile)

        cascade = cv.Load(cascadefile)

##        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
##        cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT , 480)
            
        cv.NamedWindow("Motion")
        cv.NamedWindow('Original')
      
        while True:
            image = cv.QueryFrame(capture)
##            cv.GrabFrame(capture)
##            image = cv.RetrieveFrame(capture)
            image_clone = cv.CloneImage(image)
            if(image):
                if(not motion):
                    motion = cv.CreateImage((image.width, image.height), 8, 1)
                    cv.Zero(motion) 

                update_mhi(image, motion, 30)
                # no darts 2 frames ago
                no_dart_prev_prev = no_dart_prev
                # no darts 1 frame ago
                no_dart_prev = (len(darts_found) == 0)

                # when we transition from having a dart frame to not having a
                # dart frame, then the dart coordinates are stable and we can return
                if (no_dart_prev_prev == False) and (no_dart_prev == True):
                    # we can return here
##                    draw = True
##                    print 'Dart detected at ({0},{1})'.format(detected_x,detected_y)
##                    cv.Circle(image_clone,(detected_x,detected_y),3,cv.RGB(255,0,0),3)                           
##                    cv.ShowImage('Original',image_clone)

##                    print 'at',cv.GetCaptureProperty(capture,cv.CV_CAP_PROP_POS_FRAMES)
                    return (detected_x,detected_y)
                
                darts_found = []
                
                detect(motion,cascade,darts_found)
                # if the number of pixels that changed is outside of the accepted
                # bound, then we say this is not a dart throw
                # the bounds are determined experimentally
                if not(pixels_lo_bound < cv.CountNonZero(motion) < pixels_hi_bound):
                    darts_found = []

                for dart_rec in darts_found:
##                    draw = False
                    x_dart = dart_rec[0]
                    y_dart = dart_rec[1]
                    width_dart = dart_rec[2]
                    height_dart = dart_rec[3]
                        
                    cv.Rectangle(image_clone, (x_dart,y_dart), (x_dart+width_dart,y_dart+height_dart), cv.RGB(0,0,255), 3, 8, 0)
                                
                    done = False
                    for x in range(x_dart,x_dart+width_dart,1):
                        if done:
                            break
                        for y in range (y_dart + height_dart,y_dart, -1):
                            # Get2D looks at a matrix, so we have access the
                            # Yth row and the Xth column!!!
                            if cv.Get2D(motion,y,x) != cv.Scalar(0):
                                if non_zero_in_conv_table(motion,x,y) > dart_tip_threshold:                                                              
                                    if no_dart_prev:
                                        detected_x = x
                                        detected_y = y
                                    else:
                                        if x < detected_x:
                                            detected_x = x
                                            detected_y = y
                                    done = True
                                    break
##                if draw:
##                    cv.Circle(image,(detected_x,detected_y),3,cv.RGB(255,0,0),3)
##                            
                cv.ShowImage('Original',image_clone)
                cv.ShowImage("Motion", motion)
                key = cv.WaitKey(1)
                if (key == 27):
                    break
            else:
                break
   
        raise Exception('GetDart() failed unexpectedly')
##        cv.DestroyAllWindows()

def GetDart():
    global initialized
    if not initialized:
        ##    need to call this function first before you can use GetDart()!!!
        InitGetDart()
        
    raw_dart_location = GetRawDartXY()
    correct_dart_location = dartRegion.DartLocation(raw_dart_location)

##    show the dart throw in a seperate window
    new_image = cv.CloneImage(calibration.image)        
    cv.WarpPerspective(calibration.image, new_image, calibration.mapping)
    cv.Circle(new_image, correct_dart_location, 3,cv.CV_RGB(255, 0, 0),2, 8)
    cv.ShowImage("new dart location",new_image)

    dartThrowInfo = dartRegion.DartRegion(correct_dart_location)

    ##HACK!!!!! NORMALIZE dartThrowInfo
    
    ##Bryan's calibration code uses degrees; JP's UI uses radians
    ##(both have the centre line bisecting the base 6 region as '0'
    ##JP's UI scales magnitude to 380, where 380 is the outside of the triple ring
    ##so, we need to convert to radians, and we need to scale the magnitude by the factor 380/ring_radius[5]
    ##ring_radious[5] is the raw magnitude of the outside of the double ring

    dartThrowInfo.angle = radians(dartThrowInfo.angle)
    dartThrowInfo.magnitude = dartThrowInfo.magnitude * (380./calibration.ring_radius[5]) 

    return dartThrowInfo    

if __name__ == '__main__':
    #calibrate first
    calibration.Calibration()

    while True:
        dartThrowInfo = GetDart()      

        print "The dart's base region:"
        print dartThrowInfo.base
        print "The dart's multiplier:"
        print dartThrowInfo.multiplier
        print "The dart's magnitude:"
        print dartThrowInfo.magnitude
        print "The dart's angle:"
        print dartThrowInfo.angle

        # press ESC to quit
        if cv.WaitKey(0) == 27:
            break
        cv.DestroyAllWindows()
        
    cv.DestroyAllWindows()
