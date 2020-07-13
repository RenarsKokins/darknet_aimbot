
#from darkflow.net.build import TFNet
import numpy as np
import os
import time
import math
import mss
import keyboard
import d3dshot
from queue import Queue
import threading
from threading import Thread
import pyautogui
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from win32api import GetSystemMetrics
pyautogui.FAILSAFE = False

import cv2
import darknet as dn
from aimbot_gui import Ui_Dialog

#monitor = {"top": 56, "left": 336, "width": 608, "height": 608}
#monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
monitor = {"top": 236, "left": 656, "width": 608, "height": 608}
sensitivity = 1

print('Native monitor size: ' + 'w: ' + str(GetSystemMetrics(0)) + ' h: ' + str(GetSystemMetrics(1)))

q = Queue(maxsize=1)
netMain = None
metaMain = None
altNames = None
recoil = 0
lastShot = 0
toggle = False
recoil_on = True
team = False
show_fov = True
show_detection = True

l_c = 0     #right compensation
r_c = 0     #left compensation
people_recognized = 0

objects = []

class Object:
    def __init__(self, center, aim_height, enemy_w, enemy_h, head):
        self.center = center
        self.aim_height = aim_height
        self.enemy_w = enemy_w
        self.enemy_h = enemy_h
        self.head = head

############################################ Screen capture ########################################
def get_frame():
    sct = mss.mss()
    while True:
        vid = sct.grab(monitor)
        q.put(vid)

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax

def switchToggle(event=None):
    global toggle
    if toggle == True:
        toggle = False
        gui.updateEnabled(str(toggle), "color: rgb(255, 0, 0);")
    elif toggle == False:
        toggle = True
        gui.updateEnabled(str(toggle), "color: rgb(0, 255, 0);")
    print('Toggled aim: ' + str(toggle))

def switchRecoil(event=None):
    global recoil_on
    if recoil_on == True:
        recoil_on = False
        gui.updateRecoil(str(recoil_on), "color: rgb(255, 0, 0);")
    elif recoil_on == False:
        recoil_on = True
        gui.updateRecoil(str(recoil_on), "color: rgb(0, 255, 0);")

    print('Toggled recoil: ' + str(recoil_on))

def switchTeam(event=None):
    global team
    team_text = ""
    if team == True:
        team = False
        team_text = "T"
        gui.updateTeam(team_text, "color: rgb(255, 211, 135);")
        print('Shooting at: T')
    elif team == False:
        team = True
        team_text = "CT"
        gui.updateTeam(team_text, "color: rgb(105, 143, 181);")
        print('Shooting at: CT')

def showDetection():
    global show_detection
    if show_detection == True:
        show_detection = False
        gui.updateDetection(str(show_detection), "color: rgb(255, 0, 0);")
    elif show_detection == False:
        show_detection = True
        gui.updateDetection(str(show_detection), "color: rgb(0, 255, 0);")
    print('Toggled detection: ' + str(show_detection))

def showFOV():
    global show_fov
    if show_fov== True:
        show_fov = False
        gui.updateFov(str(show_fov), "color: rgb(255, 0, 0);")
    elif show_fov == False:
        show_fov = True
        gui.updateFov(str(show_fov), "color: rgb(0, 255, 0);")

    fov.update()
    print('Toggled fov: ' + str(show_fov))

def changeDPI(value):
    global sensitivity
    sensitivity = 2/value

keyboard.on_release_key('c', switchToggle)
keyboard.on_release_key('v', switchRecoil)
keyboard.on_release_key('p', switchTeam)

############################################ GUI functions ############################################
def cvDrawBoxes(detections, img):
    for detection in detections:
        x, y, w, h = detection[2][0],\
            detection[2][1],\
            detection[2][2],\
            detection[2][3]
        xmin, ymin, xmax, ymax = convertBack(
            float(x), float(y), float(w), float(h))
        pt1 = (xmin, ymin)
        pt2 = (xmax, ymax)
        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
        cv2.putText(img,
                    detection[0].decode() +
                    " [" + str(round(detection[1] * 100, 2)) + "] " + str(int(w)),
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    [0, 255, 0], 2)
    return img

################################################ Aim calculator #######################################
def AppendData(detection, head, img):
    global people_recognized
    x, y, w, h =    detection[2][0],\
                    detection[2][1],\
                    detection[2][2],\
                    detection[2][3]

    people_recognized = people_recognized + 1
    aim_height = 0

    if head == True:
        aim_height = y
    else:
        if h > 45:
            aim_height = y - h/2.6
        else:
            aim_height = y - h/3

    objects.append(Object(int(x), aim_height, int(w), int(h), head))

def main():
    t = Thread(target=get_frame)
    t.start()
    global metaMain, netMain, altNames, recoil, recoil_on, toggle, lastShot, l_c, r_c, team, people_recognized
    configPath = "./cfg/yolov4-tiny-CSGO.cfg"
    weightPath = "./yolov4-tiny-csgo.weights"
    metaPath = "./data/csgo.data"

    if not os.path.exists(configPath):
        raise ValueError("Invalid config path `" +
                         os.path.abspath(configPath)+"`")
    if not os.path.exists(weightPath):
        raise ValueError("Invalid weight path `" +
                         os.path.abspath(weightPath)+"`")
    if not os.path.exists(metaPath):
        raise ValueError("Invalid data file path `" +
                         os.path.abspath(metaPath)+"`")

    if netMain is None:
        netMain = dn.load_net_custom(configPath.encode(
            "ascii"), weightPath.encode("ascii"), 0, 1)  # batch size = 1
        print('Loaded netMain!')
    if metaMain is None:
        metaMain = dn.load_meta(metaPath.encode("ascii"))
        print('Loaded metaMain!')
    if altNames is None:
        try:
            with open(metaPath) as metaFH:
                metaContents = metaFH.read()
                import re
                match = re.search("names *= *(.*)$", metaContents,
                                  re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1)
                else:
                    result = None
                try:
                    if os.path.exists(result):
                        with open(result) as namesFH:
                            namesList = namesFH.read().strip().split("\n")
                            altNames = [x.strip() for x in namesList]
                except TypeError:
                    pass
        except Exception:
            pass
        print('Loaded altNames!')

    net_w = dn.network_width(netMain)
    net_w_half = dn.network_width(netMain)/2

    print('Passed initialization!')
    print('Network size x: ' + str(dn.network_width(netMain)) + ' y: ' + str(dn.network_height(netMain)))

    darknet_image = dn.make_image(dn.network_width(netMain),
                                    dn.network_height(netMain),3)
    
    once_every = 0
    aim_multiplier = 0
    pyautogui.PAUSE = 0.0

    while True:
        stime = time.time()
        vid = np.asarray(q.get())

        img = cv2.resize(vid,
                        (480,
                        480),
                        interpolation=cv2.INTER_LINEAR)
        img_in = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        dn.copy_image_from_bytes(darknet_image, img_in.tobytes())
        detections = dn.detect_image(netMain, metaMain, darknet_image, thresh=0.7, hier_thresh=.5, nms=.45)

        objects.clear()
        people_recognized = 0
        
        for detection in detections:
            if ((team == False) & (detection[0].decode() == "t_head")):
                AppendData(detection, True, img)
            elif((team == False) & (detection[0].decode() == "t") & (detection[2][2] < detection[2][3])):
                AppendData(detection, False, img)
            elif ((team == True) & (detection[0].decode() == "ct_head")):
                AppendData(detection, True, img)
            elif((team == True) & (detection[0].decode() == "ct") & (detection[2][2] < detection[2][3])):
                AppendData(detection, False, img)

        is_head = []
        is_head_center = []
        s_center = []

        if people_recognized > 0:
            for types in objects:
                if types.head == True:
                    is_head.append(objects.index(types))
                    is_head_center.append(types.center - net_w_half)
                else:
                    s_center.append(types.center - net_w_half)

            if(len(is_head) > 0):
                aim_index_ = is_head_center.index(min(is_head_center, key=abs))
                aim_index = is_head[aim_index_]
            else:
                aim_index = s_center.index(min(s_center, key=abs))

            aim_compensation = 0
            if (objects[aim_index].center - net_w_half) > (objects[aim_index].enemy_w/10):
                #right
                r_c += 1
                l_c = 0
            elif (objects[aim_index].center - net_w_half) < -(objects[aim_index].enemy_w/10):
                #left
                l_c += 1
                r_c = 0
            else:
                l_c = 0
                r_c = 0

            if l_c > 10:
                aim_compensation = int(-objects[aim_index].enemy_w)
            elif r_c > 10:
                aim_compensation = int(objects[aim_index].enemy_w)

            #aim_multiplier = (objects[aim_index].center - net_w_half)/sensitivity*0.2
            #aim_multiplier = 0

            sqrt_w = math.sqrt(objects[aim_index].enemy_w)
            
            x, y = pyautogui.position()

            if (toggle == True) & (y >= 0):
                if (len(is_head) > 0):
                    """
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2) + recoil, duration=0.1)
                    """
                    aim_compensation = aim_compensation * 2.5

                    pyautogui.moveRel((objects[aim_index].center - net_w_half + aim_multiplier + aim_compensation)/sensitivity,
                                        (objects[aim_index].aim_height - net_w_half)/sensitivity + recoil)

                    if recoil_on == True:
                        if abs(objects[aim_index].center - net_w_half) < objects[aim_index].enemy_w:
                            pyautogui.click()
                            recoil += 1
                    else:
                        if abs(objects[aim_index].center - net_w_half) < objects[aim_index].enemy_w:
                            pyautogui.click()
                            recoil = 0
                        recoil = 0

                elif (objects[aim_index].enemy_w > 40):
                    """
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2) + recoil, duration=0.1)
                    """
                    pyautogui.moveRel((objects[aim_index].center - net_w_half + aim_multiplier + aim_compensation)/sensitivity,
                                        (objects[aim_index].aim_height - net_w_half)/sensitivity + recoil)
                    if recoil_on == True:
                        if abs(objects[aim_index].center - net_w_half) < sqrt_w:
                            pyautogui.click()
                            if recoil < objects[aim_index].enemy_h:
                                recoil += 1
                            else:
                                recoil = objects[aim_index].enemy_h
                    else:
                        if abs(objects[aim_index].center - net_w_half) < sqrt_w:
                            pyautogui.click()
                            recoil = 0
                        recoil = 0

                elif (objects[aim_index].enemy_w < 40):
                    recoil = 0
                    """
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2), duration=0.1)
                    """
                    pyautogui.moveRel((objects[aim_index].center - net_w_half + aim_multiplier + aim_compensation)/sensitivity,
                                        (objects[aim_index].aim_height - net_w_half)/sensitivity + recoil)

                    if abs(objects[aim_index].center - net_w_half) < sqrt_w:
                        if time.time() - lastShot > 0.3:
                            pyautogui.click()
                            lastShot = time.time()
                    
        else:
            recoil = 0

        img_show = cvDrawBoxes(detections, img)
        cv2.imshow('output', img_show)

        if cv2.waitKey(1) == ord('q'):
            print("BREAK!")
            cv2.destroyAllWindows()
            sys.exit(app.exec_())
            sys.exit()
            break

        #time.sleep(max(1./1 - (time.time() - stime), 0))

        once_every += 1
        if once_every > 60:
            print('FPS {:.1f}'.format(1 / (time.time() - stime)))
            once_every = 0
    sys.exit()

class drawFOV(QtWidgets.QWidget):
    def __init__(self, parent=None, windowSize_x=608, windowSize_y=608, penWidth=1):
        QtWidgets.QWidget.__init__(self, parent)
        self.ws = windowSize_x
        self.resize(windowSize_x+1, windowSize_y+1)
        self.pen = QtGui.QPen(QtGui.QColor(0,255,0,40))                
        self.pen.setWidth(penWidth)                                            
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.move(QtWidgets.QApplication.desktop().screen().rect().center() - self.rect().center())

    def paintEvent(self, event):
        if show_fov == True:
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtGui.QColor(0,255,0,40)))
            ws = self.ws
            painter.drawLine(   0, 0,               
                                ws, 0)   # Top
                                
            painter.drawLine(   0, ws,     
                                ws, ws)   # Bottom

            painter.drawLine(   0, 0,               
                                0, ws)   # Left

            painter.drawLine(   ws, 0,     
                                ws, ws)   # Right

            print("painted")

class drawGUI(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(switchToggle)
        self.pushButton_2.clicked.connect(switchTeam)
        self.pushButton_3.clicked.connect(switchRecoil)
        self.pushButton_5.clicked.connect(showFOV)
        self.doubleSpinBox.valueChanged.connect(changeDPI)

    def updateEnabled(self, text, color):
        self.enabled_text.setText(text)
        self.enabled_text.setStyleSheet(color)
    
    def updateTeam(self, text, color):
        self.aiming_text.setText(text)
        self.aiming_text.setStyleSheet(color)

    def updateRecoil(self, text, color):
        self.recoil_text.setText(text)
        self.recoil_text.setStyleSheet(color)

    def updateFov(self, text, color):
        self.fov_text.setText(text)
        self.fov_text.setStyleSheet(color)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    fov = drawFOV(windowSize_x=monitor.get("width"), windowSize_y=monitor.get("height"), penWidth=1)
    gui = drawGUI()
    fov.show()
    gui.show()
    main()
    sys.exit()