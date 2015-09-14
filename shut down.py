#this script runs imgurbox and drivebox to sync stuff and then shuts down the computer

#running imgurbox
import imgurbox

 #running drivebox
import sys
sys.path.append("drivebox")
import drivebox

#play sound notification
from winsound import PlaySound, SND_FILENAME
PlaySound("Job's Done.wav", SND_FILENAME)

#shutting down
print("Shutting down...")
import subprocess
subprocess.call(["shutdown", "/s", "/c", '"Shutting down..."'])