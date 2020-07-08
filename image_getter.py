import numpy as np
import os
import random
import time
import mss
import keyboard
import sys
from win32api import GetSystemMetrics
import cv2
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

print('Native monitor size: ' + 'w: ' + str(GetSystemMetrics(0)) + ' h: ' + str(GetSystemMetrics(1)))

width = 608     # capture width
height = 608    # capture height

monitor = {"top": int((GetSystemMetrics(1)-height)/2), "left": int((GetSystemMetrics(0)-width)/2), "width": width, "height": height}

def get_screenshot(event=None):
    with mss.mss() as sct:
                img = np.array(sct.grab(monitor))

    if img is None:
        print("Empty Frame")
    else:
        print('is good')
        
        img_name = str(random.randint(0, 1000000))
        
        cv2.imwrite('training images/real_scale/' + img_name + '.jpg', img)
        
        img_end = cv2.resize(img, (480, 480), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite('training images/' + img_name + '.jpg', img_end)
        
        print('saved: ' + img_name)

keyboard.on_release_key('v', get_screenshot)

class Crosshair(QtWidgets.QWidget):
    def __init__(self, parent=None, windowSize=24, penWidth=2):
        QtWidgets.QWidget.__init__(self, parent)
        self.ws = windowSize
        self.resize(windowSize+1, windowSize+1)
        self.pen = QtGui.QPen(QtGui.QColor(0,255,0,255))                
        self.pen.setWidth(penWidth)                                            
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.move(QtWidgets.QApplication.desktop().screen().rect().center() - self.rect().center() + QtCore.QPoint(1,1))


    def paintEvent(self, event):
        global width, height
        ws = self.ws
        d = 6
        painter = QtGui.QPainter(self)
        painter.setPen(self.pen)
        # painter.drawLine( x1,y1, x2,y2 )
        painter.drawLine(   0, 0,               
                            ws, 0)   # Top
                            
        painter.drawLine(   0, ws,     
                            ws, ws)   # Bottom

        painter.drawLine(   0, 0,               
                            0, ws)   # Left

        painter.drawLine(   ws, 0,     
                            ws, ws)   # Right


app = QtWidgets.QApplication(sys.argv) 

widget = Crosshair(windowSize=610, penWidth=1)
widget.show()

sys.exit(app.exec_())