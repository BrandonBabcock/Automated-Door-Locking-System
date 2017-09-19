import bluetooth
import time
import Adafruit_ADS1x15
import threading
from multiprocessing import Process, Value
import RPi.GPIO as GPIO

bluetoothAddress = "00:00:00:00:00:00"

doorLocked = True
correctNumberOfKnocks = 4
correctKnockTimings = [1, 2, 1]

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 100)
pwm.start(5)

def unlockDoor():
    print("Door unlocked!")
    pwm.ChangeDutyCycle(14)
    global doorLocked
    doorLocked = False

def lockDoor():
    print("Door locked!")
    pwm.ChangeDutyCycle(2.5)
    global doorLocked;
    doorLocked = True

def locateDevice(deviceLocated):    
    while (True):
        print("Locating Device....")
        if (bluetooth.lookup_name(bluetoothAddress, timeout = 5) != None):
            print("User found.")
            deviceLocated.value = True
        else:
            print("User not found.")
            deviceLocated.value = False
        time.sleep(10)

def isCorrectKnockTimings(detectedKnockTimings):
    for i in range(0, correctNumberOfKnocks - 1):
        if (detectedKnockTimings[i + 1] - detectedKnockTimings[i] > correctKnockTimings[i] + 0.5
            or detectedKnockTimings[i+1] - detectedKnockTimings[i] < correctKnockTimings[i] - 0.5):
            return False
    return True

def detectKnocking(correctKnock):
    detectedNumberOfKnocks = 0
    detectedKnockTimings = [None] * correctNumberOfKnocks
    knockDetectionTime = None
    
    adc = Adafruit_ADS1x15.ADS1015()
    
    while (True):
        if (knockDetectionTime != None and time.time() - knockDetectionTime > 3):
            detectedNumberOfKnocks = 0
            detectedKnockTimings = [None] * correctNumberOfKnocks
            knockDetectionTime = None

        volts = adc.read_adc(0, gain = 1)

        if (volts > 20):
            print("Knock detected!")
            time.sleep(0.5)
            detectedNumberOfKnocks += 1
            knockDetectionTime = time.time()
            detectedKnockTimings[detectedNumberOfKnocks - 1] = knockDetectionTime
            
            print("Number: ", detectedNumberOfKnocks)
            print("Time: ", knockDetectionTime)
                
            if (detectedNumberOfKnocks == correctNumberOfKnocks):
                print("Correct number of knocks!")

                if (isCorrectKnockTimings(detectedKnockTimings) == True):
                    print("Correct knocking pattern!")
                    correctKnock.value = True
                    time.sleep(60)
                    correctKnock.value = False

                detectedNumberOfKnocks = 0
                detectedKnockTimings = [None] * correctNumberOfKnocks
            
        time.sleep(0.1)

def main():    
    deviceLocated = Value("b", 0)
    correctKnock = Value("b", 0)
    
    deviceLocatorProcess = Process(target = locateDevice, args = (deviceLocated,))
    knockDetectionProcess = Process(target = detectKnocking, args = (correctKnock,))
    deviceLocatorProcess.start()
    knockDetectionProcess.start()
    
    while (True):
        if (doorLocked == True):
            if (deviceLocated.value == True or correctKnock.value == True):
                unlockDoor()
        else:
            if (deviceLocated.value == False and correctKnock.value == False):
                lockDoor()
        time.sleep(5)

main()
