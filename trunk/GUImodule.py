# draw lines, a rounded-rectangle and a circle on a wx.PaintDC() surface
# tested with Python24 and wxPython26     vegaseat      06mar2007

import wx
import images
import time
from math import sin, cos, pi
import threading
import thread
import random

EVT_RESULT_ID = wx.NewId()
EVT_STARTLISTENER_ID = wx.NewId()
EVT_STOPLISTENER_ID = wx.NewId()

DARTBOARD_TAN = '#F4E5C8'
DARTBOARD_BLACK = '#1C1D18'
DARTBOARD_RED = '#DD5035'
DARTBOARD_GREEN = '#03845B'

DARTS_HOME_POS = [ (10, 200), (10, 250), (10, 300), (760, 200), (760, 250), (760, 300)]

DART_CENTER_X = 500
DART_CENTER_Y = 250

def LISTEN_EVENT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data
        
class MyCanvas(wx.Panel):
    def __init__(self, parent, id,):
        wx.Panel.__init__(self, parent, id)

        self.SetBackgroundColour('#D18B3D')
        bmp = images.DartImage1.GetBitmap()
        mask = wx.Mask(bmp, '#010000') #make transparent bg
        bmp.SetMask(mask)
        self.bmp = bmp
        
        # dart ids
        self.objids = []
        
        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.DoDrawing(self.pdc)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)

    def OnMouse(self, event):
        if event.LeftDown():
            x,y = event.GetX(), event.GetY()
            l = self.pdc.FindObjects(x, y, 5)
            for id in l:
                self.dragid = id
                self.lastpos = (event.GetX(),event.GetY())
                break
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                x,y = self.lastpos
                dx = event.GetX() - x
                dy = event.GetY() - y
                r = self.pdc.GetIdBounds(self.dragid)       #get the previous location
                self.pdc.TranslateId(self.dragid, dx, dy)   #find the new x,y
                r2 = self.pdc.GetIdBounds(self.dragid)      #get the new location
                r = r.Union(r2)                             #combine the two rectangles
                r.Inflate(4,4)                              #inflate to compensate
                self.RefreshRect(r, False)                  #repaint the rectangle
                self.lastpos = (event.GetX(),event.GetY())
            if event.LeftUp():
                self.dragid = -1

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  
        dc = wx.BufferedPaintDC(self)
        #print 'paint'
        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        
        rect = wx.Rect(0, 0, 250,500)
        rect.SetPosition((0, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 1", 30, 40)
        rect.SetPosition((750, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 2", 780, 40)
        rect.SetPosition((20, 80))
        
        rgn = self.GetUpdateRegion()
        r = rgn.GetBox()
        # repair only damaged window
        self.pdc.DrawToDCClipped(dc,r)

    def DoDrawing(self, dc):
        #Draw the dart board
        self.DoDrawDartBoard(dc)
    
        dc.BeginDrawing()
        for i in range(6):
            id = wx.NewId()
            dc.SetId(id)
            w,h = self.bmp.GetSize()
            x, y = DARTS_HOME_POS[i]
            dc.DrawBitmap(self.bmp,x,y,True)
            dc.SetIdBounds(id,wx.Rect(x,y,w,h))
            self.objids.append(id)
        dc.EndDrawing()
        
    def DoDrawDartBoard(self, dc):
        dc.SetPen(wx.Pen('black', 1))
        
        #Centre of dartboard
        x = DART_CENTER_X
        y = DART_CENTER_Y
        
        radii = [250, 190, 178, 120, 110, 18, 10]
        
        #Outer circle, full solid
        dc.SetBrush(wx.Brush(DARTBOARD_BLACK))
        dc.DrawCircle(x, y, radii[0])
        
        ringcolours = [DARTBOARD_RED, DARTBOARD_GREEN]
        areacolours = [DARTBOARD_BLACK, DARTBOARD_TAN]
        
        #Draw Sectors, outside in
        for circle in range(1,5):
            colourpair = ringcolours if circle % 2 == 1 else areacolours
            for sector in range(20):
                theta1 = sector*pi/10+pi/20
                theta2 = sector*pi/10-pi/20
                x1 = x+radii[circle]*cos(theta1)
                y1 = y+radii[circle]*sin(theta1)
                x2 = x+radii[circle]*cos(theta2)
                y2 = y+radii[circle]*sin(theta2)
                colour = colourpair[sector%2]
                dc.SetBrush(wx.Brush(colour))
                dc.DrawArc(x1, y1, x2, y2, x, y)
        
        dc.SetBrush(wx.Brush(DARTBOARD_GREEN))
        dc.DrawCircle(x, y, radii[5])
        dc.SetBrush(wx.Brush(DARTBOARD_RED))
        dc.DrawCircle(x, y, radii[6])    
    
    def MoveDart(self, dartNum, p):
        dartID = self.objids[dartNum]
        r = self.pdc.GetIdBounds(dartID)
        dx = p[0] - r[0]
        dy = p[1] - r[1]        
        self.pdc.TranslateId(dartID, dx, dy)
        r2 = self.pdc.GetIdBounds(dartID)
        r = r.Union(r2)
        r.Inflate(4,4)
        self.RefreshRect(r, False)
    
class ListenerThread(threading.Thread):
    def __init__(self, parent_window):
        """init listener thread class"""
        threading.Thread.__init__(self)
        self.parent_window = parent_window
        self.DoClose = 0
        self.start()
        
    def run(self):
        """Start Listener Thread."""
        player = 1
        dartnum = 1
        while 1:
            #REPLACE WITH DART LISTENER LOGIC
            time.sleep(1)
            dart = [player, dartnum, 190*random.random(), 2*pi*random.random()]
            dartnum = dartnum + 1
            
            if dartnum == 4:
                dartnum = 1
                if player == 1:
                    player = 2
                else:
                    player = 1
            
            print 'sent'
            print dart
            if self.DoClose:
                wx.PostEvent(self.parent_window, ResultEvent(None))
                return
            wx.PostEvent(self.parent_window, ResultEvent(dart))
        
    def close(self):
        """Close Listener Thread."""
        self.DoClose = 1
        print 'Listener Terminated'
        
#AppGUI is instance of application.  This initializes all the widgets
class AppGUI(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)
        
    def OnInit(self):
    
        #----------------------------------------------------------
        #Create a frame
        frame = wx.Frame(None, -1, title='Rene Desdartes', size=(1000, 580),
                        style=wx.DEFAULT_FRAME_STYLE)
        #----------------------------------------------------------
        #Create menubar and status bar and bind events
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        
        fileMenu.Append(EVT_STARTLISTENER_ID, "&New Game", "Starts a new game")
        self.Bind(wx.EVT_MENU, self.StartGame, id=EVT_STARTLISTENER_ID)
        
        fileMenu.Append(EVT_STOPLISTENER_ID, "&End Game", "Starts a new game")
        self.Bind(wx.EVT_MENU, self.StopGame, id=EVT_STOPLISTENER_ID)
        
        fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit Application")
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        
        menuBar.Append(fileMenu, "&File")
        frame.SetMenuBar(menuBar)

        frame.CreateStatusBar()
        #----------------------------------------------------------
        #Create event handler for listening
        LISTEN_EVENT(self, self.OnListen)
        self.listener = None
        #----------------------------------------------------------
        #Create panel as drawing surface
        panel = MyCanvas(frame, wx.ID_ANY)
        panel.SetFocus()
        self.panel = panel
        
        #----------------------------------------------------------
        frame.Show(True)
        frame.Fit()
        
        self.SetTopWindow(frame)
        self.frame = frame 
        return True
               
    def StartGame (self, event):
        """Start second thread for listening to events"""
        if not self.listener: #only have one listener
            #self.status.SetLabel('Listening')
            print 'listening'
            self.listener = ListenerThread(self)
    
    def StopGame (self, event):
        """Stop second thread for listening to events"""
        if self.listener:
            #self.status.SetLabel('Game Stopped')
            print 'Stop'
            self.listener.close()
    
    def OnClose (self, event):
        if self.listener:
            self.listener.close() #close the listener thread
            print 'Close'
        self.frame.Close()
        
    def OnListen(self, event):
        """Listened"""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            print 'aborted'
            self.listener = None
        else:
            # Need to add dart drawing logic
            print 'received'
            dart = event.data
            dartNum = dart[1] - 1 if dart[0] == 1 else dart[1] + 2
            x = DART_CENTER_X + dart[2]*cos(dart[3])
            y = DART_CENTER_Y + dart[2]*sin(dart[3])
            
            if dart[1] == 1: #Reset dart positions after every turn
                for i in range(0,6):
                    self.panel.MoveDart(i, DARTS_HOME_POS[i])
                    
            self.panel.MoveDart(dartNum, (x, y))
        
class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        self.App = AppGUI()
        self.App.MainLoop()
        
        