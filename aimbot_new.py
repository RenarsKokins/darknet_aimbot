
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

#monitor = {"top": 56, "left": 336, "width": 608, "height": 608}
#monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
monitor = {"top": 236, "left": 656, "width": 608, "height": 608}

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


def get_frame():
    with mss.mss() as sct:
        while True:
            vid = np.array(sct.grab(monitor))
            img = cv2.resize(vid,
                                   (480,
                                    480),
                                   interpolation=cv2.INTER_LINEAR)

            img_in = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            q.put(img_in)


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
    elif toggle == False:
        toggle = True
    print('Toggled aim: ' + str(toggle))

def switchRecoil(event=None):
    global recoil_on
    if recoil_on == True:
        recoil_on = False
    elif recoil_on == False:
        recoil_on = True
    print('Toggled recoil: ' + str(recoil_on))

def switchTeam(event=None):
    global team
    if team == True:
        team = False
        print('Shooting at: T')
    elif team == False:
        team = True
        print('Shooting at: CT')

keyboard.on_release_key('c', switchToggle)
keyboard.on_release_key('v', switchRecoil)
keyboard.on_release_key('p', switchTeam)

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
                    " [" + str(round(detection[1] * 100, 2)) + "]",
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    [0, 255, 0], 2)
    return img

def AppendData(detection, head):
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
        if h > 35:
            aim_height = y - h/2.5
        else:
            aim_height = y - h/4

    objects.append(Object(int(x), aim_height, int(h), int(w), head))

def main():
    t = Thread(target=get_frame)
    t.start()
    global metaMain, netMain, altNames, recoil, recoil_on, toggle, lastShot, l_c, r_c, team, people_recognized
    time.sleep(1)
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
    pyautogui.PAUSE = 0.0

    while True:
        stime = time.time()
        img_in = q.get()

        #cv2.rectangle(img_in, (280, 280), (dn.network_width(netMain), dn.network_height(netMain)), (0,0,0), thickness=-1)

        dn.copy_image_from_bytes(darknet_image, img_in.tobytes())

        detections = dn.detect_image(netMain, metaMain, darknet_image, thresh=0.7, hier_thresh=.5, nms=.45)

        objects.clear()
        people_recognized = 0
        
        for detection in detections:
            #print(detection[0].decode())
            if((detection[0].decode() == "t_head") | (detection[0].decode() == "t")):
                if ((team == False) & (detection[0].decode() == "t_head")):
                    AppendData(detection, True)
                elif((team == False) & (detection[0].decode() == "t") & (detection[2][2] < detection[2][3])):
                    AppendData(detection, False)

            elif((detection[0].decode() == "ct_head") | (detection[0].decode() == "ct")):
                if ((team == True) & (detection[0].decode() == "ct_head")):
                    AppendData(detection, True)
                elif((team == True) & (detection[0].decode() == "ct") & (detection[2][2] < detection[2][3])):
                    AppendData(detection, False)

        is_head = []
        is_head_center = []
        s_center = []

        if people_recognized > 0:
            for types in objects:
                if types.head == True:
                    is_head.append(objects.index(types))
                    is_head_center.append(types.center)
                else:
                    s_center.append(types.center)

            if(len(is_head) > 0):
                aim_index_ = is_head_center.index(min(is_head_center))
                aim_index = is_head[aim_index_]
            else:
                aim_index = s_center.index(min(s_center))

            aim_multiplier = (objects[aim_index].center - net_w_half)*0.2
            #aim_multiplier = 0
            aim_compensation = 0

            if (objects[aim_index].center - net_w_half) > (objects[aim_index].enemy_w/20):
                #right
                r_c += 1
                l_c = 0
            elif (objects[aim_index].center - net_w_half) < -(objects[aim_index].enemy_w/20):
                #left
                l_c += 1
                r_c = 0
            else:
                l_c = 0
                r_c = 0

            if l_c > 4:
                aim_compensation = int(-objects[aim_index].enemy_w/2)
                #print('compensated left')
            elif r_c > 4:
                aim_compensation = int(objects[aim_index].enemy_w/2)
                #print('compensated right')

            #aim_compensation = 0
            #aim_multiplier = 0

            if toggle == True:
                if (len(is_head) > 0):
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2) + recoil)

                    if recoil_on == True:
                        if abs(objects[aim_index].center - net_w_half) < 7:
                            pyautogui.click()
                            recoil += 1
                    else:
                        if abs(objects[aim_index].center - net_w_half) < 7:
                            pyautogui.click()
                            recoil = 0
                        recoil = 0

                elif (objects[aim_index].enemy_h > 50):
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2) + recoil)
                    if recoil_on == True:
                        if abs(objects[aim_index].center - net_w_half) < 7:
                            pyautogui.click()
                            if recoil < objects[aim_index].enemy_h:
                                recoil += 1
                            else:
                                recoil = objects[aim_index].enemy_h
                    else:
                        if abs(objects[aim_index].center - net_w_half) < 7:
                            pyautogui.click()
                            recoil = 0
                        recoil = 0

                elif ((objects[aim_index].enemy_h < 50) & (len(is_head) == 0)):
                    pyautogui.moveTo(objects[aim_index].center + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-net_w)/2),
                                        objects[aim_index].aim_height + ((GetSystemMetrics(1)-net_w)/2))

                    if abs(objects[aim_index].center - net_w_half) < 7:
                        if time.time() - lastShot > 0.5:
                            pyautogui.click()
                            lastShot = time.time()
                    recoil = 0

                
        else:
            recoil = 0    
        
        img_show = cvDrawBoxes(detections, img_in)
        cv2.imshow('output', img_show)

        if cv2.waitKey(1) == ord('q'):
            print("BREAK!")
            cv2.destroyAllWindows()
            sys.exit()
            break

        #time.sleep(max(1./60 - (time.time() - stime), 0))

        once_every += 1
        if once_every > 60:
            print('FPS {:.1f}'.format(1 / (time.time() - stime)))
            once_every = 0

    sys.exit()


if __name__ == '__main__':
     main()