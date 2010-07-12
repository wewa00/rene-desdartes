import sys
import urllib2
import cv
import threading
import thread
import pickle
import os.path

# just a sample class so I can "create" dartThrows with the get throw function
class dartThrow:
    def __init__(self):
        self.score = -1
        self.magnitude = -1
        self.angle = -1

    def printThrow(self):
        print "Score:" + self.score + ", Magnitude: " + self.magnitude + ", Angle: " + self.angle

#sample settings class
class settings:
    def __init__(self):
        self.playerOne = "One"
        self.playerTwo = "Two"
        self.gameType = 2 #1 is normal, 2 is practice
    
def getThrow():
    throw = dartThrow()
    throw.score = input("Enter Score: ")
    throw.magnitude = input("Enter Magnitude: ")
    throw.angle = input("Enter Angle: ")
    
    # my hack of triggering an event =P
    if throw.score == 1234:
        correctScore.set()
    return throw

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
        # game type 1 is a normal game of 501
        if self.gameType == 1:
            # Just temporary, because score keeper will handle this
            self.playerOne.score = 501
            self.playerTwo.score = 501
        self.currentPlayer = self.playerOne
        self.dartsLeft = 3
        self.stillPlaying = True
        self.winner = None
    
    def switchPlayer(self):
        if self.currentPlayer == self.playerOne:
            print "SWITCHED TO PLAYER TWO"
            self.currentPlayer = self.playerTwo
        elif self.currentPlayer == self.playerTwo:
            print "SWITCHED TO PLAYER ONE"
            self.currentPlayer = self.playerOne
        self.dartsLeft = 3
            
    def updateScoreGame(self, throwResult):
        print "Updating Score"
        # this will be sent to/handled by the score keeper in the future
        self.currentPlayer.score = self.currentPlayer.score - throwResult.score
        # if score is 0, the current player wins
        if self.currentPlayer.score == 0:
            self.winner = self.currentPlayer
            self.stillPlaying = False
            return
        # if score is less than 0, it means the player busts, and their score resets, switches players
        elif self.currentPlayer.score < 0:
            self.currentPlayer.score =+ throwResult.score
            self.switchPlayer()
            print self.currentPlayer.name + " BUSTED. Too bad!"
            return
        
        # Remove a dart and check if you need to switch players
        self.dartsLeft = self.dartsLeft - 1
        if self.dartsLeft == 0:
            self.switchPlayer()
        
        # this is just for debugging, this will obviously be in UI
        print self.currentPlayer.name + " has " + str(self.currentPlayer.score) + " remaining"
        print str(self.dartsLeft) + " darts left to throw"
        
        # Set the UPDATE UI event
        updateUI.set()
            
    def updateScorePractice(self, throwResult):
        print "Updating practice"
        
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
    print "Starting Game"
    game = DartGame(settings)
    while ( game.stillPlaying == True ):
        throwResult = getThrow()
        # uncomment to get it to print out dart throw
        #throwResult.printThrow()
        # check correctScore event
        if correctScore.isSet():
            # will figure this out later
            print "Correct the score!"
            correctScore.clear()
        else:
            # Update the score
            if game.gameType == 1:
                #print "====Normal mode===="
                game.updateScoreGame(throwResult)
            else:
                #print "====Practice mode===="
                game.updateScorePractice(throwResult)
    
    print "THE WINNER IS " + game.currentPlayer.name



def startEngine():
    print "START YOUR ENGINES!"
    setting = settings()
    playGame(setting)


if __name__ == "__main__":
    print "Main is running"
    correctScore = threading.Event()
    updateUI = threading.Event()
    # start the engine in a thread!
    # buggy, it crashes at various points, don't know why
    # thread.start_new_thread(startEngine,())
    setting = settings()
    playGame(setting)
    