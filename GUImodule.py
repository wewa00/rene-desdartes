import wx
import images
import time
from math import sin, cos, pi, sqrt, atan, pow
import threading
import thread
import random
import ScoreKeeper

CMD_EXIT = 0
CMD_RECAL = 1
CMD_CORRECT = 2
CMD_STARTGAME = 3



EVT_RESULT_ID = wx.NewId()
EVT_STARTGAME_ID = wx.NewId()
EVT_STOPGAME_ID = wx.NewId()
EVT_RECALLISTENER_ID = wx.NewId()

DARTBOARD_REFMAG = 380
DARTBOARD_REFANG = pi/20
#wire thickness 1.5 mm
DARTBOARD_RADII = [ 223.68,   170.0,   162.0,   107.0,   99.0,  31.8/2,  12.7/2] #in mm
        
DARTBOARD_TAN = '#F4E5C8'
DARTBOARD_BLACK = '#1C1D18'
DARTBOARD_RED = '#DD5035'
DARTBOARD_GREEN = '#03845B'

DARTS_HOME_POS = [ (10, 200), (10, 250), (10, 300), (760, 200), (760, 250), (760, 300)]
#starts at right most
DART_NUM = [6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10]

DART_CENTER_X = 500.0
DART_CENTER_Y = 250.0

def LISTEN_EVENT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, action, player, dartNum, dart, p1, p2):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.action = action
        self.player = player
        self.dartNum = dartNum
        self.dart = dart
        self.p1score = p1.score
        self.p2score = p2.score
        
class MyCanvas(wx.Panel):
    def __init__(self, parent, id,):
        wx.Panel.__init__(self, parent, id)

        self.SetBackgroundColour('#D18B3D')
        bmp = images.DartImage1.GetBitmap()
        mask = wx.Mask(bmp, '#010000') #make transparent bg
        bmp.SetMask(mask)
        self.bmp = bmp
        
        self.boardDartsFlag = "p1"
        self.boardDarts = [None, None, None]
        
        #score labels
        self.p1 = wx.StaticText(self, -1, str(0), (30, 60))
        self.p2 = wx.StaticText(self, -1, str(0), (780, 60))
        
        #score buttons
        self.buttons = []
        
        bp1ID = wx.NewId()
        bp1 = wx.Button(self, bp1ID, "previous", (30, 90))
        self.Bind(wx.EVT_BUTTON, self.OnClick, bp1)
        self.buttons.append(bp1ID)
        
        bp2ID = wx.NewId()
        bp2 = wx.Button(self, bp2ID, "previous", (780, 90))
        self.Bind(wx.EVT_BUTTON, self.OnClick, bp2)
        self.buttons.append(bp2ID)
        
        currID = wx.NewId()
        curr = wx.Button(self, currID, "current", (250, 0))
        self.Bind(wx.EVT_BUTTON, self.OnClick, curr) 
        self.buttons.append(currID)
        
        # dart ids
        self.objids = []
        self.objmovable = []
        
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
                if self.objmovable[self.objids.index(self.dragid)]:
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
                if self.dragid != -1 and self.objmovable[self.objids.index(self.dragid)]:
                    if self.boardDartsFlag == "p1":
                        dartIndex = self.objids.index(self.dragid)
                        
                        #Get the old score and add it (penalize) the current score
                        b = scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].base
                        mul = scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].multiplier
                        scoreKeeper.playerOne.score += b*mul
                        
                        #Calculate new dart parameters from the moved dart
                        x, y, w, h = self.pdc.GetIdBounds(self.dragid)
                        b, mul, m, a = self.GetDartParameters( (x, y) ) 

                        #Fix the scores
                        scoreKeeper.playerOne.score -= b*mul #add the new score
                        self.UpdateScore(scoreKeeper.playerOne.score, scoreKeeper.playerTwo.score)
                        
                        #Update the dart parameters
                        scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].base = b
                        scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].multiplier = mul
                        scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].magnitude = m
                        scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1][dartIndex].angle = a
                    elif self.boardDartsFlag == "p2":
                        dartIndex = self.objids.index(self.dragid) - 3
                        
                        #Get the old score and add it (penalize) the current score
                        b = scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].base
                        mul = scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].multiplier
                        scoreKeeper.playerTwo.score += b*mul
                        
                        #Calculate new dart parameters from the moved dart
                        x, y, w, h = self.pdc.GetIdBounds(self.dragid)
                        b, mul, m, a = self.GetDartParameters( (x, y) )  
                        
                        #Fix the scores
                        scoreKeeper.playerTwo.score -= b*mul
                        self.UpdateScore(scoreKeeper.playerOne.score, scoreKeeper.playerTwo.score)
                        
                        #Update the dart parameters
                        scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].base = b
                        scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].multiplier = mul
                        scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].magnitude = m
                        scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1][dartIndex].angle = a
                    else:
                        if scoreKeeper.currentPlayer == scoreKeeper.playerOne:
                            dartIndex = self.objids.index(self.dragid)
                        else:
                            dartIndex = self.objids.index(self.dragid) - 3
                        
                        #Get the old score and add it (penalize) the current score                        
                        b = scoreKeeper.currentDartSet[dartIndex].base
                        mul = scoreKeeper.currentDartSet[dartIndex].multiplier
                        scoreKeeper.currentPlayer.score += b*mul
                        
                        #Calculate new dart parameters from the moved dart
                        x, y, w, h = self.pdc.GetIdBounds(self.dragid)
                        b, mul, m, a = self.GetDartParameters( (x, y) )   

                        #Fix the scores
                        scoreKeeper.currentPlayer.score -= b*mul
                        self.UpdateScore(scoreKeeper.playerOne.score, scoreKeeper.playerTwo.score)
                        
                        #Update the dart parameters
                        scoreKeeper.currentDartSet[dartIndex].base = b
                        scoreKeeper.currentDartSet[dartIndex].multiplier = mul
                        scoreKeeper.currentDartSet[dartIndex].magnitude = m
                        scoreKeeper.currentDartSet[dartIndex].angle = a
                    uiCommandStream.set(CMD_CORRECT)
                self.dragid = -1
    
    def GetDartParameters(self, p ):
        x, y = p
        
        magnitude = sqrt(pow((x - DART_CENTER_X),2) + pow((DART_CENTER_Y - y),2))*DARTBOARD_REFMAG/190
        if (x - DART_CENTER_X) != 0:
            angle = atan((DART_CENTER_Y - y)/(x - DART_CENTER_X))
        else:
            if (DART_CENTER_Y - y) > 0:
                angle = pi/2
            else:
                angle = -pi/2
            
        if x - DART_CENTER_X < 0:
            angle+=pi
        
        angle = angle%(2*pi)
        
        #starting from the outer ring, check if the magnitude lies outside that ring
        #is not, go smaller.  Stop at the biggest ring that has lower radius than magnitude
        for radius in DARTBOARD_RADII:
            if magnitude/DARTBOARD_REFMAG*190 > radius*19.0/17.0:
                break
        
        base = -1
        
        if DARTBOARD_RADII.index(radius) == 0 or DARTBOARD_RADII.index(radius) == 1: #Outside dartboard play area
            multiplier = 0;
            base = 0
        elif DARTBOARD_RADII.index(radius) == 2: #double ring
            multiplier = 2;
        elif DARTBOARD_RADII.index(radius) == 4: #triple ring
            multiplier = 3;
        elif DARTBOARD_RADII.index(radius) == 3 or DARTBOARD_RADII.index(radius) == 5:
            multiplier = 1;
        #bull or double bull. either since the for loop above stops at 6 regardless...
        elif DARTBOARD_RADII.index(radius) == 6: 
            if magnitude < radius:
                base = 50
            else:
                base = 25
            multiplier = 1;
            
        if base == -1: #need to figure out regions
            for region in range(20):
                theta1 = region*pi/10 + DARTBOARD_REFANG
                theta2 = (region-1)*pi/10 + DARTBOARD_REFANG
                if angle <= theta1 and angle >= theta2:
                    base = DART_NUM[region]
                    break
        
        print base, multiplier, magnitude, angle
            
        return (base,multiplier,magnitude,angle)
                
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
            self.objmovable.append(False)
        dc.EndDrawing()
        
    def DoDrawDartBoard(self, dc):
        dc.SetPen(wx.Pen('black', 1))
        
        #Centre of dartboard
        x = DART_CENTER_X
        y = DART_CENTER_Y
        
        #Outer circle, full solid
        dc.SetBrush(wx.Brush(DARTBOARD_BLACK))
        dc.DrawCircle(x, y, 19.0/17.0*DARTBOARD_RADII[0])
        
        ringcolours = [DARTBOARD_GREEN, DARTBOARD_RED]
        areacolours = [DARTBOARD_TAN, DARTBOARD_BLACK]
        
        #Draw Sectors, outside in
        for circle in range(1,5):
            colourpair = ringcolours if circle % 2 == 1 else areacolours
            for sector in range(20):
                theta1 = (sector-1)*pi/10 + DARTBOARD_REFANG
                theta2 = sector*pi/10 + DARTBOARD_REFANG
                x1 = x+19.0/17.0*DARTBOARD_RADII[circle]*cos(theta1)
                y1 = y-19.0/17.0*DARTBOARD_RADII[circle]*sin(theta1)
                x2 = x+19.0/17.0*DARTBOARD_RADII[circle]*cos(theta2)
                y2 = y-19.0/17.0*DARTBOARD_RADII[circle]*sin(theta2)
                colour = colourpair[sector%2]
                dc.SetBrush(wx.Brush(colour))
                dc.DrawArc(x1, y1, x2, y2, x, y)
                #sector 15 is the top
        
        #Draw the numbers
        for sector in range(20):
            theta = (2*sector-1)*pi/20 + DARTBOARD_REFANG
            x1 = x+19.0/17.0*(DARTBOARD_RADII[0]+DARTBOARD_RADII[1])/2*cos(theta)
            y1 = y-19.0/17.0*(DARTBOARD_RADII[0]+DARTBOARD_RADII[1])/2*sin(theta)
            colour = '#FFFFFF'
            dc.SetTextForeground(colour)
            dc.DrawText(`DART_NUM[sector]`, x1, y1)
        
        dc.SetBrush(wx.Brush(DARTBOARD_GREEN))
        dc.DrawCircle(x, y, 19.0/17.0*DARTBOARD_RADII[5])
        dc.SetBrush(wx.Brush(DARTBOARD_RED))
        dc.DrawCircle(x, y, 19.0/17.0*DARTBOARD_RADII[6])    
    
    def MoveDart(self, dartNum, p, movable):
        dartID = self.objids[dartNum]
        self.objmovable[dartNum] = movable
        r = self.pdc.GetIdBounds(dartID)
        dx = p[0] - r[0]
        dy = p[1] - r[1]        
        self.pdc.TranslateId(dartID, dx, dy)
        r2 = self.pdc.GetIdBounds(dartID)
        r = r.Union(r2)
        r.Inflate(4,4)
        self.RefreshRect(r, False)
        
    def UpdateScore(self, p1, p2):
        self.p1.SetLabel(`p1`)
        self.p2.SetLabel(`p2`)
    
    def MakeCurrent(self):
        for i in range(6):
            self.MoveDart(i, DARTS_HOME_POS[i], False)
        self.boardDartsFlag = "c"
        self.boardDarts = scoreKeeper.currentDartSet
        for i in range(3):
            if self.boardDarts[i] != None:
                x = DART_CENTER_X + self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*cos(self.boardDarts[i].angle)
                y = DART_CENTER_Y - self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*sin(self.boardDarts[i].angle)
                if scoreKeeper.currentPlayer == scoreKeeper.playerOne:
                    self.MoveDart(i, (x,y),True)
                else:
                    self.MoveDart(i+3, (x,y),True)
    
    def OnClick(self, event):
        for i in range(6):
                self.MoveDart(i, DARTS_HOME_POS[i], False)
    
        if event.GetId() == self.buttons[0]:
            self.boardDartsFlag = "p1"
            self.boardDarts = scoreKeeper.playerOne.throwHistory[len(scoreKeeper.playerOne.throwHistory)-1]
            for i in range(3):
                x = DART_CENTER_X + self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*cos(self.boardDarts[i].angle)
                y = DART_CENTER_Y - self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*sin(self.boardDarts[i].angle)
                self.MoveDart(i, (x,y),True)            

        elif event.GetId() == self.buttons[1]:
            self.boardDartsFlag = "p2"
            self.boardDarts = scoreKeeper.playerTwo.throwHistory[len(scoreKeeper.playerTwo.throwHistory)-1]
            for i in range(3):
                x = DART_CENTER_X + self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*cos(self.boardDarts[i].angle)
                y = DART_CENTER_Y - self.boardDarts[i].magnitude/DARTBOARD_REFMAG*190*sin(self.boardDarts[i].angle)
                self.MoveDart(i+3, (x,y),True)        
        else:
            self.MakeCurrent()
            
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
            if updateUI.isSet():
                #Get last dart in current dart set
                lastDart = None;
                
                currentDartSet = scoreKeeper.currentDartSet
                
                i = -1
                
                for dart in currentDartSet:
                    if dart != None:
                        lastDart = dart
                        i += 1
                    else:
                        break
                
                if lastDart == None:
                    wx.PostEvent(self.parent_window, ResultEvent("reset", scoreKeeper.currentPlayer, i, lastDart, scoreKeeper.playerOne, scoreKeeper.playerTwo))
                else:
                    wx.PostEvent(self.parent_window, ResultEvent("update", scoreKeeper.currentPlayer, i, lastDart, scoreKeeper.playerOne, scoreKeeper.playerTwo))
                    
                updateUI.clear()
        
            #if self.DoClose:
            #    wx.PostEvent(self.parent_window, ResultEvent(None))
            #    return
            #wx.PostEvent(self.parent_window, ResultEvent(dart))
        
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
        
        fileMenu.Append(EVT_STARTGAME_ID, "&New Game", "Starts a new game")
        self.Bind(wx.EVT_MENU, self.StartGame, id=EVT_STARTGAME_ID)
        
        #fileMenu.Append(EVT_STOPLISTENER_ID, "&End Game", "Ends this game")
        #self.Bind(wx.EVT_MENU, self.StopGame, id=EVT_STOPLISTENER_ID)
        
        fileMenu.Append(EVT_RECALLISTENER_ID, "&Recalibrate", "Recalibrates the game")
        self.Bind(wx.EVT_MENU, self.OnRecalibrate, id=EVT_RECALLISTENER_ID)
        
        fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit Application")
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        
        menuBar.Append(fileMenu, "&File")
        frame.SetMenuBar(menuBar)

        frame.CreateStatusBar()
        
        #frame.SetTransparent(150)
        #----------------------------------------------------------
        #Create event handler for listening
        LISTEN_EVENT(self, self.OnListen)
        self.listener = ListenerThread(self)
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
        uiCommandStream.set(CMD_STARTGAME)
    
#    def StopGame (self, event):
#        """Stop second thread for listening to events"""
#        if self.listener:
#            #self.status.SetLabel('Game Stopped')
#            print 'Stop'
#            self.listener.close()
#            self.listener = None
    def OnRecalibrate(self, event):
        """Recalibrate the camera"""
        uiCommandStream.set(CMD_RECAL)
            
    
    def OnClose (self, event):
        uiCommandStream.set(CMD_EXIT)
        
    def OnListen(self, event):
        """Listened"""
        if event.action is None:
            # Thread aborted (using our convention of None return)
            print 'aborted'
            self.listener = None
        elif event.action == "update":
            if event.player == scoreKeeper.playerOne:
                dartNum  = event.dartNum
            else:
                dartNum = event.dartNum + 3
            
            x = DART_CENTER_X + event.dart.magnitude/DARTBOARD_REFMAG*190*cos(event.dart.angle)
            y = DART_CENTER_Y - event.dart.magnitude/DARTBOARD_REFMAG*190*sin(event.dart.angle)
            
            self.panel.MakeCurrent()
            self.panel.MoveDart(dartNum, (x, y), True)
            self.panel.UpdateScore(event.p1score, event.p2score)
            
        elif event.action == "reset":
            self.panel.MakeCurrent()
            for i in range(6):
                self.panel.MoveDart(i, DARTS_HOME_POS[i], False)
        
class GUIThread(threading.Thread):    
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        self.App = AppGUI()
        self.App.MainLoop()
    
    def initUIEvent(self, event):
        global updateUI
        updateUI = event
        
    def initUICommandStream(self, object):
        global uiCommandStream
        uiCommandStream = object
    
    def initScoreKeeper(self, object):
        global scoreKeeper
        scoreKeeper = object