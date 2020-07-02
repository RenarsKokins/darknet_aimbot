# Darknet based aimbot (python)
AI based aimbot (mainly used for CS:GO) for testing purposes (isn't good enough for real usage yet). This aimbot uses darkflow port to windows (darknet) and coco_v3_tiny weights. Of course it isn't as good as a human in games, but it works as a concept preety well! It runs fast enough to detect in real-time, but lacks accuracy. That is because i just used it's default weights even though I should've trained it myself (maybe I will do it in future :D). 

I was testing it in CS:GO and it ran pretty well, but it doesnt recognize people in the distance and sometimes mistakes random objects (as guns, dead bodies, blood, etc.) as humans. **The code is very crude and might be hard to understand for now!**
# How to use
1. Make sure you have installed [CUDA](https://developer.nvidia.com/cuda-10.0-download-archive) and [CUDNN](https://developer.nvidia.com/rdp/cudnn-archive) (must be v10.0 and requires NVIDIA GPU)!
2. Install all necessary libraries(mss, d3dshot, cv2, keyboard, etc.). Just check the aimbot_v2.py file imports.
3. Try to launch aimbot_v2.py and if it runs, good job!
4. If you use it for CS:GO, run the game on "windowed fullscreen" mode and disable "raw input" in the mouse settings. 

To toggle the aimbot, press 'v' and it should start aiming, press it again to disable. To close it, press on the open window and then press 'q' on keyboard.

# What to improve
1. Create a CS:GO character dataset and train weights based on this dataset to improve accuracy and target only CT or T.
2. Improve aiming accuracy (it often misses the shot when character is moving, because there is a small delay between screen capture and real game).
3. Create a GUI.
4. Code optimisation.
