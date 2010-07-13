# draw lines, a rounded-rectangle and a circle on a wx.PaintDC() surface
# tested with Python24 and wxPython26     vegaseat      06mar2007

import wx 
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
        self.SetMenuBar(menuBar)
        
        self.CreateStatusBar()
        
        # event handler for listening
        LISTEN_EVENT(self, self.OnListen)
        
        #Create panel for painting on
        self.panel = wx.Panel(self, size=(1000, 500)) 
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint) 
        self.status = wx.StaticText(self, -1, '', pos=(0,100))
        #self.SetTransparent(150)
        self.Fit() 
        
        self.listener = None

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
        
    def DoDrawDartBoard(self, dc):
        dc.SetPen(wx.Pen('black', 1))
        
        #Centre of dartboard
        x = 500
        y = 250
        
        radii = [250, 190, 178, 120, 110, 18, 10]
        
        #Outer circle, full solid
        dc.SetBrush(wx.Brush(DARTBOARD_BLACK))
        dc.DrawCircle(x, y, radii[0])
        
        ringcolours = [DARTBOARD_GREEN, DARTBOARD_RED]
        areacolours = [DARTBOARD_TAN, DARTBOARD_BLACK]
        
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
    
    def StartGame (self, event):
        """Start second thread for listening to events"""
        if not self.listener: #only have one listener
            self.status.SetLabel('Listening')
            self.listener = ListenerThread(self)
    
    def StopGame (self, event):
        """Stop second thread for listening to events"""
        if self.listener:
            self.status.SetLabel('Game Stopped')
            self.listener.close()
    
    def OnListen(self, event):
        """Listened"""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            self.status.SetLabel('Listening aborted')
            self.listener = None
        else:
            # Need to add dart drawing logic
            self.status.SetLabel('Heard: %s' % event.data)
    
    def OnClose (self, event):
        if self.listener:
            self.listener.close() #close the listener thread
        self.Close()

class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.gameGrame = MainGameFrame(title='Title Goes Here')
        self.start()
    
    def run(self):
        self.gameGrame.Center() 
        self.gameGrame.Show()