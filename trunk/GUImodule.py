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
        bmp = images.Test2.GetBitmap()
        mask = wx.Mask(bmp, wx.BLUE) #make transparent bg
        bmp.SetMask(mask)
        self.bmp = bmp
        
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
                r = self.pdc.GetIdBounds(self.dragid)
                self.pdc.TranslateId(self.dragid, dx, dy)
                r2 = self.pdc.GetIdBounds(self.dragid)
                r = r.Union(r2)
                r.Inflate(4,4)
                self.RefreshRect(r, False)
                self.lastpos = (event.GetX(),event.GetY())
            if event.LeftUp():
                self.dragid = -1

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  
        dc = wx.BufferedPaintDC(self)
        
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
    
        self.objids = []
        dc.BeginDrawing()
        for i in range(3):
            id = wx.NewId()
            dc.SetId(id)
            w,h = self.bmp.GetSize()
            x, y = 0, 0
            dc.DrawBitmap(self.bmp,x,y,True)
            dc.SetIdBounds(id,wx.Rect(x,y,w,h))
            self.objids.append(id)
        dc.EndDrawing()
        
    def DoDrawDartBoard(self, dc):
        dc.SetPen(wx.Pen('black', 1))
        
        #Centre of dartboard
        x = 500
        y = 250
        
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
        
class ListenerThread(threading.Thread):
    def __init__(self, parent_window):
        """init listener thread class"""
        threading.Thread.__init__(self)
        self.parent_window = parent_window
        self.DoClose = 0
        self.start()
        
    def run(self):
        """Start Listener Thread."""
        while 1:
            #REPLACE WITH DART LISTENER LOGIC
            time.sleep(1)
            dart = [190*random.random(), 2*pi*random.random()]
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
        
class MainGameFrame(wx.Frame): 
    """Main Frame"""
    def __init__(self, parent=None, id=-1, title=None): 
        wx.Frame.__init__(self, parent, id, title) 
        self.SetBackgroundColour('#D18B3D')
        
        #Create panel for painting on
        #self.panel = wx.Panel(self, size=(1000, 500)) 
        #self.panel.Bind(wx.EVT_PAINT, self.OnPaint) 
        #self.status = wx.StaticText(self, -1, '', pos=(0,100))
        self.SetTransparent(150)


    def OnPaint(self, event):
        # establish the painting surface
        dc = wx.PaintDC(self.panel)
        
        self.DoDrawDartBoard(dc)
        
        rect = wx.Rect(0, 0, 250,500)
        rect.SetPosition((0, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 1", 30, 40)
        rect.SetPosition((750, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 2", 780, 40)
        rect.SetPosition((20, 80))
        
   
        
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
        self.frame.Close()
        
    def OnListen(self, event):
        """Listened"""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            #self.status.SetLabel('Listening aborted')
            print 'aborted'
            self.listener = None
        else:
            # Need to add dart drawing logic
            # self.status.SetLabel('Heard: %s' % event.data)
            print 'received'
            print event.data
        
class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start() #Self starting thread
    
    def run(self):
        self.App = AppGUI()
        self.App.MainLoop()
        
        