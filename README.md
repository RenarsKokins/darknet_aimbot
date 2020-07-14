# Darknet based aimbot (python 3)
AI based aimbot (mainly used for CS:GO) for testing purposes. This aimbot uses darkflow port to windows (darknet) and ~~coco_v3_tiny~~ coco_v4_tiny weights. Of course it isn't as good as a human in games, but it works as a concept preety well! It runs fast enough to detect in real-time, but lacks accuracy at range. I have created a custom dataset using images for T's and CT's and trained weights. It works better than before, but sometimes mistakes random objects as heads or enemies (because I trained it with only ~550 images). I should have labeled ~2000 images instead (in the future I will).  

I was testing it in CS:GO and it ran pretty well, but it doesnt recognize people in the distance and sometimes mistakes random objects (as guns, dead bodies, blood, etc.) as humans. As of update v0.6, it runs on custom CS:GO dataset and recognizes T from CT, but needs more labeled images. I also created a [labeling program](https://github.com/RenarsKokins/YOLO-gym) for this specific job in C#.

# How to install and run
1. Install Python 3!
2. Make sure you have installed [CUDA](https://developer.nvidia.com/cuda-10.0-download-archive) and [CUDNN](https://developer.nvidia.com/rdp/cudnn-archive) (must be v10.0 and requires NVIDIA GPU)!
3. Install all necessary libraries(mss, d3dshot, cv2, keyboard, etc.). Just check the aimbot_v2.py file imports.
4. Try to launch aimbot_v2.py and if it runs, good job!
5. If you use it for CS:GO, run the game on "windowed fullscreen" mode and disable "raw input" in the mouse settings.

# How to use
To toggle the aimbot, press 'c' and it should start aiming, press it again to disable. To switch which enemies will be shot at, press 'p' and look at python console (it will show T or CT). To switch recoil, press 'v' and check the console. To close it, press on the open window and then press 'q' on keyboard.

# What to improve
1. ~~Create~~ Improve CS:GO character dataset and train weights based on this dataset to improve accuracy and target only CT or T.
2. Improve aiming accuracy (it often misses the shot when character is moving, because there is a small delay between screen capture and real game. Needs some sort of prediction I guess).
3. ~~Create a GUI.~~
4. Create a faster screen capture (if even possible).
5. Code optimisation.

# Changelog
### v0.7
1. Added GUI with some basic features (keyboard keys are still binded).
### v0.6
1. Upgraded from yolo_v3_tiny to yolo_v4_tiny with custom labels.
2. Detection speed upgrades.
3. Small code optimizations.
### v0.5
1. Base aimbot script created.