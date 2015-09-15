#this script runs imgurbox and drivebox to sync stuff and then shuts down the computer

#running imgurbox
import imgurbox

#running drivebox
import sys
sys.path.append("drivebox")
import drivebox

#set working directory back to this one (drivebox changed it)
import os
os.chdir(os.path.dirname(__file__)) 

#play sound notification
from winsound import PlaySound, SND_FILENAME
PlaySound("Job's Done.wav", SND_FILENAME)

#shutting down
import time
print("Press CTRL+C to abort turning off the computer.")

for t in range(9, 0, -1):
	print("\rShutting down in {}...".format(t), end="")
	time.sleep(1)

import subprocess
subprocess.call(["shutdown", "/s", "/t", "0", "/c", '"Shutting down."'])