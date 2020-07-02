
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
l_c = 0     #right compensation
r_c = 0     #left compensation

def get_frame():
    while True:
        with mss.mss() as sct:
            vid = np.array(sct.grab(monitor))
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

keyboard.on_release_key('c', switchToggle)
keyboard.on_release_key('v', switchRecoil)

def cvDrawBoxes(detections, img):
    for detection in detections:
        if (detection[0].decode() == "person"):
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


def main():
    t = Thread(target=get_frame)
    t.start()

    global metaMain, netMain, altNames, recoil, recoil_on, toggle, lastShot, l_c, r_c
    

    configPath = "./cfg/yolov4-tiny.cfg"
    weightPath = "./yolov4-tiny.weights"
    metaPath = "./cfg/coco.data"

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
    
    print('Passed initialization!')
    print('Network size x: ' + str(dn.network_width(netMain)) + ' y: ' + str(dn.network_height(netMain)))

    darknet_image = dn.make_image(dn.network_width(netMain),
                                    dn.network_height(netMain),3)

    once_every = 0
    while True:
        stime = time.time()
        img = q.get()

        if img is None:
            print("Empty Frame")
            continue
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_in = cv2.resize(img,
                                   (dn.network_width(netMain),
                                    dn.network_height(netMain)),
                                   interpolation=cv2.INTER_LINEAR)

        cv2.rectangle(img_in, (280, 280), (dn.network_width(netMain), dn.network_height(netMain)), (0,0,0), thickness=-1)

        dn.copy_image_from_bytes(darknet_image, img_in.tobytes())
        detections = dn.detect_image(netMain, metaMain, darknet_image, thresh=0.38, hier_thresh=.5, nms=.55)

        center = []
        aim_height = [] 
        closest = []
        enemy_h = []
        enemy_w = []
        people_recognized = 0
        
        for detection in detections:
            if(detection[0].decode() == "person"):
                x, y, w, h =    detection[2][0],\
                                detection[2][1],\
                                detection[2][2],\
                                detection[2][3]

                if w > h:
                    break

                people_recognized = people_recognized + 1
                center.append(int(x))
                if h > 35:
                    aim_height.append(y - h/2.5)
                    #print('is more')
                else:
                    aim_height.append(y - h/2.65)
                    #print('isnt more')

                #closest.append(int(w+h))
                closest.append(int(x))
                enemy_h.append(int(h))
                enemy_w.append(int(w))

        ###################### AIM AT CLOSEST ONE ########################

        if people_recognized >= 1:
            aim_index = closest.index(min(closest))
            aim_multiplier = (center[aim_index] - 208)*0.523

            aim_compensation = 0
            if (center[aim_index] - 208) > (enemy_w[aim_index]/20):
                #right
                r_c += 1
                l_c = 0
            elif (center[aim_index] - 208) < -(enemy_w[aim_index]/20):
                #left
                l_c += 1
                r_c = 0
            else:
                l_c = 0
                r_c = 0

            if l_c > 4:
                aim_compensation = int(-enemy_w[aim_index]/2)
                #print('compensated left')
            elif r_c > 4:
                aim_compensation = int(enemy_w[aim_index]/2)
                #print('compensated right')

            if ((toggle == True) & (enemy_h[aim_index] > 50) & (recoil_on == True)):
                pyautogui.moveTo(center[aim_index] + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-416)/2),
                                    aim_height[aim_index] + ((GetSystemMetrics(1)-416)/2) + recoil)
                if abs(center[aim_index] - 208) < 5:
                    pyautogui.click()
                    if recoil < enemy_h[aim_index]:
                        recoil += 1
                    else:
                        recoil = enemy_h[aim_index]
                pyautogui.PAUSE = 0.0

            elif ((toggle == True) & (enemy_h[aim_index] > 50) & (recoil_on == False)):
                pyautogui.moveTo(center[aim_index] + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-416)/2),
                                    aim_height[aim_index] + ((GetSystemMetrics(1)-416)/2))
                if abs(center[aim_index] - 208) < 5:
                    pyautogui.click()
                pyautogui.PAUSE = 0.0
                recoil = 0

            elif ((toggle == True) & (enemy_h[aim_index] < 50)):
                pyautogui.moveTo(center[aim_index] + aim_multiplier + aim_compensation + ((GetSystemMetrics(0)-416)/2),
                                    aim_height[aim_index] + ((GetSystemMetrics(1)-416)/2))

                if abs(center[aim_index] - 208) < 10:
                    if time.time() - lastShot > 0.5:
                        pyautogui.click()
                        pyautogui.PAUSE = 0.0
                        lastShot = time.time()
                recoil = 0
        else:
            recoil = 0    
        
        img_show = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB)
        img_show = cvDrawBoxes(detections, img_show)
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

#input("Press Enter to exit...")
