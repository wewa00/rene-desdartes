import random
import dartRegion
import GameEngine
import math
import calibration

# difficulty changes variance
easy = 20
medium = 10
hard = 5

class AIOpponent:
    def __init__(self, difficulty):
        self.difficulty = difficulty

    def selectTarget(self, scoreLeft, dartsLeft):
        # default target is the triple 20
        score = 20
        multiplier = 3
        
        # ========== BASED ON: http://ricksmith.ca/Darts/dartsouts.htm
        # ========== 2 - 40 ==========
        if scoreLeft <= 40:
            # at this point, aim at singles unless you can checkout
            multiplier = 1
            if scoreLeft % 2 == 0:
                score = scoreLeft / 2
                multiplier = 2
            elif scoreLeft == 3 or scoreLeft == 5 or scoreLeft == 9 or scoreLeft == 33:
                score = 1
            elif scoreLeft == 7 or scoreLeft == 11 or scoreLeft == 35:
                score = 3
            elif scoreLeft == 13 or scoreLeft == 19:
                score = 11
            elif scoreLeft == 15 or scoreLeft == 17:
                score = 13
            elif scoreLeft == 21 or scoreLeft == 25 or scoreLeft == 29:
                score = 17
            elif scoreLeft == 23 or scoreLeft == 27:
                score = 19
            elif scoreLeft == 31 or scoreLeft == 39:
                score = 7
            elif scoreLeft == 37:
                score = 5
        # ========== 41 - 48 ==========
        elif scoreLeft <= 48:
            score = scoreLeft - 32
            multiplier = 1
        # ========== 49 ==========
        elif scoreLeft == 49:
            score = 9
            multiplier = 1
        # ========== 50 ==========
        elif scoreLeft == 50:
            if dartsLeft == 1:
                score = 25
                multiplier = 2
            else:
                score = 10
                multiplier = 3
        # ========== 51 - 60 ==========        
        elif scoreLeft <= 60:
            score = scoreLeft - 40
            multiplier = 1
        # ========== 61 - 70 ==========
        elif scoreLeft <= 70:
            # aim at triple unless otherwise stated
            multiplier = 3
            # 2 darts left
            if dartsLeft == 2:
                score = scoreLeft - 50
            # 3 or 1 darts left
            else:
                if scoreLeft == 61 or scoreLeft == 65:
                    score = 25
                    multiplier = 1
                elif scoreLeft == 62 or scoreLeft == 66 or scoreLeft == 70:
                    score = 10
                elif scoreLeft == 63:
                    score = 13
                elif scoreLeft == 64:
                    score = 16
                elif scoreLeft == 67:
                    score = 9
                elif scoreLeft == 68:
                    score = 20
                elif scoreLeft == 69:
                    score = 11
        # ========== 71 - 80 ==========
        elif scoreLeft <= 80:
            multiplier = 3
            if scoreLeft == 71:
                if dartsLeft == 2:
                    score = 19
                else:
                    score = 13
            elif scoreLeft == 72 or scoreLeft == 76:
                if scoreLeft == 76 and dartsLeft == 2:
                    score = 20
                else:
                    score = 16
            elif scoreLeft == 73 or scoreLeft == 77:
                score = 19
            elif scoreLeft == 74 or scoreLeft == 78:
                if scoreLeft == 74 and dartsLeft == 2:
                    score = 16
                else:
                    score = 14
            elif scoreLeft == 75:
                if dartsLeft == 2:
                    score = 25
                    multiplier = 1
                else:
                    score = 17
            elif scoreLeft == 76 or scoreLeft == 79:
                if scoreLeft == 79 and dartsLeft == 2:
                    score = 13
                else:
                    score = 19
            elif scoreLeft == 80:
                if dartsLeft == 2:
                    score = 16
                else:
                    score = 20
        # ========== 81 - 95 ==========
        elif scoreLeft <= 95:
            multiplier = 3
            if scoreLeft == 86:
                score = 18
            elif scoreLeft == 87:
                score = 17
            elif scoreLeft == 88:
                score = 20
            elif scoreLeft == 89:
                score = 19
            else:
                if dartsLeft == 2:
                    if scoreLeft == 81 or scoreLeft == 93 or scoreLeft == 95:
                        score = 19
                    elif scoreLeft == 82:
                        score = 14
                    elif scoreLeft == 83 or scoreLeft == 91:
                        score = 17
                    elif scoreLeft == 84 or scoreLeft == 92:
                        score = 20
                    elif scoreLeft == 85:
                        score = 15
                    elif scoreLeft == 90 or scoreLeft == 94:
                        score = 18
                else:
                    score = 25
                    if scoreLeft == 82 or scoreLeft == 90:
                        multiplier = 2
                    else:
                        multiplier = 1
        # ========== 96 - 110 ==========
        elif scoreLeft <= 110:
            multiplier = 3
            score = 20
            # aim at triple 19 for these ones
            if scoreLeft == 97 or scoreLeft == 99 or scoreLeft == 103 or scoreLeft == 104 or scoreLeft == 107 or scoreLeft == 110:
                score = 19
            # if 2 darts left, aim differently
            if dartsLeft == 2:
                if scoreLeft == 101:
                    score = 17
                elif scoreLeft == 104:
                    score = 18
                elif scoreLeft == 107:
                    score = 19
                elif scoreLeft == 110:
                    score = 20
        # ========== 111 - 119 ==========
        elif scoreLeft <= 119:
            multiplier = 3
            score = 19
            if scoreLeft == 112 or scoreLeft == 115 or scoreLeft == 118:
                score = 20
        # ========== 120+ ==========
        elif scoreLeft == 122 or scoreLeft == 126 or scoreLeft == 129 or scoreLeft == 131:
            multiplier = 3
            score = 19
        elif scoreLeft == 123 or scoreLeft == 128:
            multiplier = 3
            score = 18
        elif scoreLeft == 125:
            multipler = 1
            score = 25
        elif scoreLeft == 132 or scoreLeft == 135:
            multiplier = 2
            score = 25
        else:
            multiplier = 3
            score = 20
            # if one dart left, aim for something that will give you an out
            if dartsLeft == 1:
                if scoreLeft == 179 or scoreLeft == 183 or scoreLeft == 186 or scoreLeft == 189:
                    score = 19
                elif scoreLeft == 182 or scoreLeft == 185 or scoreLeft == 188:
                    score = 18
                elif scoreLeft == 195:
                    score = 25
                    multiplier = 2
                # numbers to avoid 112, 118, 125, 128, 129
                elif scoreLeft == 132 or scoreLeft == 138 or scoreLeft == 145 or scoreLeft == 149:
                    score = 19
                elif scoreLeft == 148:
                    score = 18
            
        return (score, multiplier)
        
    #def generateThrow(self, game):
    def generateThrow(self, scoreLeft, dartsLeft):
        # normally get score remaining and dart remaining for player
        # scoreLeft = game.currentPlayer.score
        # dartLeft = game.dartsLeft 
        (score, multiplier) = self.selectTarget(scoreLeft, dartsLeft)
        # pass target (score, multipler) to bryan
        # ======= dart = getTarget (score, multiplier) ======
        (magnitude, angle) = dartRegion.RegionToLocation(score, multiplier)
        print "The mag: " + str(magnitude) + " and the angle: " + str(angle)
        magnitude = random.gauss(magnitude, self.difficulty)
        angle = random.gauss(angle, self.difficulty)
        
        (score, multiplier) = dartRegion.LocationToRegion(angle, magnitude)
        print "The score: " + str(score) + " and the multi: " + str(multiplier)
        
        # scale the angle and magnitude
        angle = math.radians(angle)
        magnitude = magnitude * (380./calibration.ring_radius[5]) 
        #if multiplier == 3:
            #multiplierWord = "triple "
        #elif multiplier == 2:
            #multiplierWord = "double "
        #else:
            #multiplierWord = "single "
        #print "aim at " + multiplierWord + str(score) + " when " + str(scoreLeft) + " Left"
        dartThrow = GameEngine.dartThrow()
        dartThrow.base = score
        
        dartThrow.multiplier = multiplier
        dartThrow.magnitude = magnitude
        dartThrow.angle = angle
        return dartThrow
    
    
if __name__ == "__main__":
    AI = AIOpponent(hard)
    test = "C"
    if test == "A":
        while (True):
            scoreLeft = input("Score Left: ")
            dartsLeft = input("Darts Left: ") 
            dart = AI.generateThrow(scoreLeft, dartsLeft)
    elif test == "C":
        AI.generateThrow(501,3)
        AI.generateThrow(441,2)
        AI.generateThrow(381,1)
        AI.generateThrow(321,3)
        AI.generateThrow(261,2)
        AI.generateThrow(201,1)
        AI.generateThrow(141,3)
        AI.generateThrow(81,2)
        AI.generateThrow(24,1)
    else:
        dartsLeft = 3
        for i in range(2, 200):
            AI.generateThrow(i, dartsLeft)