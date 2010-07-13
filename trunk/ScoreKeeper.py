class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None
 
    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
 
        return cls.instance
        
class ScoreKeeper(object):
    __metaclass__ = Singleton
    def __init__ (self, game):
        self.playerOne = game.playerOne
        self.playerTwo = game.playerTwo
        self.playerOne.throwHistory = [] 
        self.playerTwo.throwHistory = []
        self.currentDartSet = [None, None, None] 
        if game.gameType == 1:
            self.playerOne.score = 501
            self.playerTwo.score = 501
        else:
            self.playerOne.score = -1
            self.playerTwo.score = -1
        game.scoreKeeper = self