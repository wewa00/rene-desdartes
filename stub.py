from GUImodule import GUIThread
import random
import threading
import time
import wx

dart = (0,0,0)

def updateUIfunction():
    for i in range(12):
        global dart
        time.sleep(1)
        dart = (0, random.random(),random.random())
        #print dart
        updateUI.set()

if __name__ == '__main__':
    updateUI = threading.Event()
    correctScore = threading.Event()
    
    #updateUIstub = threading.Thread(target=updateUIfunction)
    #updateUIstub.start()
    
    #app = AppGUI()
    #app.MainLoop()
    
    g = GUIThread()
    g.start()