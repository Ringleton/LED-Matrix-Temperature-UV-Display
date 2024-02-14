import RPi.GPIO as GPIO
from time import sleep
import os
from datetime import datetime

monitor_pin = 19

GPIO.setmode(GPIO.BCM)

GPIO.setup(monitor_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

def Shutdown_or_Restart(channel):

    # Ignore false positives (static?)
    sleep(0.05)
    # If still showing pressed (state=0) after 50ms, then this is a real button press.
    if GPIO.input(monitor_pin) == 0:
        # We now wait two seconds then see what we've got.
        sleep(2)
        if GPIO.input(monitor_pin) == 1:  # not pressed now
            # Short press < 2 seconds so restart
            os.system("sudo shutdown -r now")
    
        else: # still pressed
            # Long press > 2 seconds so shutdown (halt)
            os.system("sudo shutdown -h now")
    
GPIO.add_event_detect(monitor_pin, GPIO.FALLING, callback = Shutdown_or_Restart, bouncetime = 50)

while True:
    sleep(1)