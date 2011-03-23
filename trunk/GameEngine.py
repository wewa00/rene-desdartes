import sys
import urllib2
import cv
import threading
import thread
import pickle
import os.path
import ScoreKeeper
import GUImodule
import time
import random
import get_dart
import calibration
import AI
import time
from math import pi

CMD_EXIT = 0
CMD_RECAL = 1
CMD_CORRECT = 2
CMD_STARTGAME = 3

difficulty = 10
player_switch_wait_time = 2
ai_throw_wait_time = 1.7

# just a sample class so I can "create" dartThrows with the get throw function
class dartThrow:
    def __init__(self):
        self.base = -1
        self.multiplier = -1
        self.magnitude = -1
        self.angle = -1

    def printThrow(self):
        print "Score:" + `self.base*self.multiplier` + ", Magnitude: " + `self.magnitude` + ", Angle: " + `self.angle`

#sample settings class
class settings:
    def __init__(self):
        self.playerOne = "Player1"
        self.playerTwo = "Player2"
        self.gameType = 1 #1 is normal, 2 is practice

##Use get_dart.GetDart() instead
##def getThrow():
##    throw = dartThrow()
##    s = raw_input('--> ')
##    throw.base = 4 #input("Enter Base Region: ")
##    throw.multiplier = 1 #input("Enter Multiplier: ")
##    throw.magnitude = 380*random.random() #input("Enter Magnitude: ")
##    throw.angle = 2*pi*random.random() #input("Enter Angle: ")
##    
##    # my hack of triggering an event =P
##    if throw.base == 25:
##        correctScore.set()
##    return throw

# ====================== EVERYTHING ABOVE IS TEMPORARY ========================
class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        
class DartGame:
    def __init__(self, settings):
        self.playerOne = Player(settings.playerOne)
        self.playerTwo = Player(settings.playerTwo)
        self.gameType = settings.gameType
        ## game type 1 is a normal game of 501
        #if self.gameType == 1:
            ## Just temporary, because score keeper will handle this
            #self.playerOne.score = 501
            #self.playerTwo.score = 501
        self.currentPlayer = self.playerOne
        self.dartsLeft = 3
        self.stillPlaying = True
        self.winner = None
    
    def switchPlayer(self):
        # add the dart set to the current player
        self.currentPlayer.throwHistory.append(scoreKeeper.currentDartSet)
        # reset the current dart set
        scoreKeeper.currentDartSet = [None, None, None]
        # switch the current player
        if self.currentPlayer == self.playerOne:
            #print "SWITCHED TO PLAYER TWO"
            self.currentPlayer = self.playerTwo
            scoreKeeper.currentPlayer = self.playerTwo
        elif self.currentPlayer == self.playerTwo:
            #print "SWITCHED TO PLAYER ONE"
            self.currentPlayer = self.playerOne
            scoreKeeper.currentPlayer = self.playerOne
        self.dartsLeft = 3
        time.sleep(player_switch_wait_time)
            
    def updateScoreGame(self, throwResult):
        #print "Updating Score"
        # this will be sent to/handled by the score keeper in the future
        # you can update score based on current player because players are linked to scoreKeeper
        self.currentPlayer.score = self.currentPlayer.score - (throwResult.base * throwResult.multiplier)
        # add the dart to the current dart set in the score keeper
        scoreKeeper.currentDartSet[3-self.dartsLeft] = throwResult
        updateUI.set()
        
        while updateUI.isSet():
            pass
        
        time.sleep(0.1)
        
        # if score is 0, the current player wins
        if self.currentPlayer.score == 0 and throwResult.multiplier == 2:
            self.winner = self.currentPlayer
            self.stillPlaying = False
            return
        # if score is less than 0, it means the player busts, and their score resets, switches players
        # if the score is 0, it means the multiplier is NOT 2, they still bust
        # if the score is 1, it is still bust, there's no doubles to get a total of 1 point
        if self.currentPlayer.score <= 1:
            self.currentPlayer.score = self.currentPlayer.score + (throwResult.base * throwResult.multiplier)
            # switch player AFTER we print out " BUSTED. Too bad!"
            print self.currentPlayer.name + " BUSTED. Too bad!"
            self.switchPlayer()
            
            updateUI.set()
        
            while updateUI.isSet():
                pass
            
            return
        
        # Remove a dart and check if you need to switch players
        self.dartsLeft = self.dartsLeft - 1
        if self.dartsLeft == 0:
            self.switchPlayer()
        
        # this is just for debugging, this will obviously be in UI
        print self.currentPlayer.name + " has " + str(self.currentPlayer.score) + " remaining"
        #print str(self.dartsLeft) + " darts left to throw"
        
        # Set the UPDATE UI event
        updateUI.set()
        
        while updateUI.isSet():
            pass
            
    def updateScorePractice(self, throwResult):
        #print "Updating practice"
        
        # read from a file... checking if it exists
        filePath = os.getcwd()
        fileName = filePath + "/save/" + self.currentPlayer.name
        
        if os.path.isfile(fileName):            
            fileHandle = open(fileName, 'rb')
            data = pickle.load(fileHandle)
            fileHandle.close()
            data.append(throwResult)
        else:
            # create the save directory if it doesn't exist
            if not os.path.exists(filePath + "/save"):
                os.makedirs(filePath + "/save")
            data = [throwResult]
            
        # saving the score
        fileHandle = open(fileName, 'wb')       
        pickle.dump(data, fileHandle)
        fileHandle.close()
    
def playGame (settings):
    global scoreKeeper
    
    print "Starting Game"
    game = DartGame(settings)
    AIPlayer = AI.AIOpponent(difficulty)
    scoreKeeper.reset(game)
    
    # this call loads the camera capture and waits a few frames for the picture to stabilize
    get_dart.InitGetDart()
    
    while ( game.stillPlaying == True ):
##        Now uses get_dart.GetDart()
        if game.currentPlayer.name == "CPU1" or game.currentPlayer.name == "CPU2":
            throwResult = AIPlayer.generateThrow(game.currentPlayer.score, game.dartsLeft)
        else:
            throwResult = get_dart.GetDart()#getThrow()
            time.sleep(0.1)

        # uncomment to get it to print out dart throw
        throwResult.printThrow()
        # check correctScore event
        if uiCommandStream.Event.isSet():
            if uiCommandStream.Command == CMD_RECAL:
                print "RECAL"
            elif uiCommandStream.Command == CMD_CORRECT:
                print "Correct the score!"
            elif uiCommandStream.Command == CMD_EXIT:
                print "EXITING"
                exit()
            uiCommandStream.clear()
        else:
            # Update the score
            if game.gameType == 1:
                #print "====Normal mode===="
                game.updateScoreGame(throwResult)
                if game.currentPlayer.name == "CPU1" or game.currentPlayer.name == "CPU2":
                    time.sleep(ai_throw_wait_time)
            else:
                #print "====Practice mode===="
                game.updateScorePractice(throwResult)
    
    print "THE WINNER IS " + game.currentPlayer.name

def startEngine():
    print "START YOUR ENGINES!"
    setting = settings()
    playGame(setting)

class UICommandStream(object):
    def __init__ (self):
        self.Event = threading.Event()
        self.Command = -1
        
    def clear(self):
        self.Event.clear()
        self.Command = -1
        
    def set(self, command):
        self.Event.set()
        self.Command = command
        
if __name__ == "__main__":
    print "Main is running"
    commandStream = threading.Event()
    updateUI = threading.Event()
    
    g = GUImodule.GUIThread()
    
    global uiCommandStream
    uiCommandStream = UICommandStream()
    g.initUICommandStream(uiCommandStream)
    
    g.initUIEvent(updateUI)

    #passing the score keeper instance to the GUI
    global scoreKeeper
    scoreKeeper = ScoreKeeper.ScoreKeeper()
    g.initScoreKeeper(scoreKeeper)

    
    g.start()
    
    # don't know where's a good place to put this, but will put it here for now
    calibration.Calibration()
    
    while 1:  
        while 1:
            if uiCommandStream.Event.isSet():
                if uiCommandStream.Command == CMD_STARTGAME:
                    uiCommandStream.clear()
                    break
    
        setting = settings()
        playGame(setting)
    
