import RPi.GPIO as GPIO
from time import sleep
import os

monitor_pin = 19

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

GPIO.setup(monitor_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

def Shutdown_or_Restart(channel):
    sleep(2)
    if GPIO.input(monitor_pin) == 1:
        # Short press < 2 seconds so restart
        os.system("sudo shutdown -r now")
    else:
        # Long press > 2 seconds so shutdown
        os.system("sudo shutdown -h now")

    GPIO.cleanup()
 
GPIO.add_event_detect(monitor_pin, GPIO.FALLING, callback = Shutdown_or_Restart, bouncetime = 200)

while True:
    sleep(1)