from PIL import ImageDraw, ImageFont, Image
from oled.device import ssd1306, sh1106
from oled.render import canvas
from StringIO import StringIO
from ssl import *

import sys
sys.path.append("./lib/protocol/")
sys.path.append("./lib/util/")
sys.path.append("./lib/exception/")
sys.path.append("./lib/rfid/")

import RFID
import RPi.GPIO as GPIO
import datetime, pytz
import PIL.ImageOps
import signal
import time
import requests
import json
import glob

# define hosts
flaskHost              = "<FLASK WEBSITE HOST URL>"
thingHost              = "<THING HOST URL>"
publishTopic           = "<AWS IoT THING TOPIC>"

# global variables
rootCAPath             = "<PATH TO ROOT CA>"
thingCertificatePath   = "<PATH TO THING CERTIFICATE>"
thingPrivateKeyPath    = "<PATH TO THING PRIVATE KEY>"
timezone               = "US/Eastern"
maxRaceTime            = 15

# define gpio pins (board mode)
rfidPin                = 24
laserPin               = 35
redPin                 = 36
greenPin               = 40
bluePin                = 38

# setup gpio pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(laserPin, GPIO.IN)
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)

# setup rfid reader
rfid = RFID.RFID(pin_ce=rfidPin)

# setup display and fonts
disp         = ssd1306(port=1, address=0x3C)
defaultFont  = ImageFont.truetype("fonts/Tahoma.ttf", 15)
raceFont     = ImageFont.truetype("fonts/Tahoma.ttf", 35)
timerFont    = ImageFont.truetype("fonts/LCD-N.ttf", 30)

# setup all the led colors with an initial
# duty cycle of 0 which is off
Freq    = 100 #Hz
RED     = GPIO.PWM(redPin, Freq)
GREEN   = GPIO.PWM(greenPin, Freq)
BLUE    = GPIO.PWM(bluePin, Freq)
RED.start(0)
GREEN.start(0)
BLUE.start(0)

# setup AWS IoT
# check dependencies
libraryCheck = True
try:
    import paho.mqtt.client as mqtt
    import logManager
    import mqttCore
    import AWSIoTExceptions
except ImportError:
    libraryCheck = False
    print "paho-mqtt python package missing. Please install/reinstall it."

# setup credentials
rootCA      = glob.glob(rootCAPath)
certificate = glob.glob(thingCertificatePath)
privateKey  = glob.glob(thingPrivateKeyPath)
credentialCheck = len(rootCA) > 0 and len(certificate) > 0 and len(privateKey) > 0

# Function to display the welcome message.
# It uses the loopCount variable to determine which
# bmp to dispay to give a plusing effect.
def displayWelcome(loopCount):
    with canvas(disp) as draw:
        # display the welcome message
        draw.text((0, 0),  "Welcome!", font=defaultFont, fill=255)
        draw.text((0, 17), "Place RFID", font=defaultFont, fill=255)
        draw.text((0, 32), "card on", font=defaultFont, fill=255)
        draw.text((0, 47), "reader to begin.", font=defaultFont, fill=255)

        # display the rfid logo bmp
        img = Image.open('images/rfid-logo-' + str(loopCount) + '.bmp')
        invertedImg = PIL.ImageOps.invert(img)
        draw.bitmap((90, 15), invertedImg, fill=1)
    time.sleep(0.5)

# Function to display the user data on the oled screen.
# This function takes the hexUID and does a request to our flask web service to
# 'get' the user's information from the cloud.
def displayUserData(hexUID):
    r = requests.get(flaskHost + '/users/' + hexUID)
    userData = r.json()[u'user']
    with canvas(disp) as draw:
        draw.text((0, 0), userData[u'name'], font=defaultFont, fill=255)
        imageURLResponse = requests.get(userData[u'avatar'])
        img = Image.open(StringIO(imageURLResponse.content))
        draw.bitmap((0, 15), img, fill=1)
    time.sleep(2.5)
    setupRace(hexUID, userData[u'name'])

# Function to display READY->SET->GO!
# The RGB led allows changes from RED->YELLOW->GREEN
def setupRace(hexUID, name):
    # Display Red
    with canvas(disp) as draw:
        draw.text((0, 0), 'READY', font=raceFont, fill=255)
    color(100, 0, 0, 2.0)

    # Display Yellow
    with canvas(disp) as draw:
        draw.text((0, 0), 'SET', font=raceFont, fill=255)
    color(65, 100, 0, 2.0)

    # Disyplay Green
    with canvas(disp) as draw:
        draw.text((0, 0), 'GO!', font=raceFont, fill=255)
    color(0, 100, 0, 0)

    # Display stopwatch
    stopwatch(hexUID, name)

# Function to display the stopwatch on the oled screen.
# It records when the function was called as the start time
# and loops until the maxRaceTime is met OR the laser is 
# interrupted (ie: laserPin is set to low)
def stopwatch(hexUID, name):
    start = time.time()
    time.clock()
    elapsed = 0
    while elapsed < maxRaceTime and GPIO.input(laserPin) != GPIO.LOW:
        elapsed = time.time() - start
        millis = int(round(elapsed * 1000))
        hours, millis = divmod(millis, 3600000)
        minutes, millis = divmod(millis, 60000)
        seconds, millis = divmod(millis, 1000)
        s = "%02i:%02i:%03i" % (minutes, seconds, millis)
        with canvas(disp) as draw:
                draw.text((0, 0), "Timer:", font=defaultFont, fill=255)
                draw.text((0, 20), s, font=timerFont, fill=255)
    color(100, 0, 0, 0)
    publishRaceTimes(hexUID, name, elapsed)

# Function to plubish the race times for the current user.
# It takes the hexUID, name and completionTime
# and publishes them to the AWS IoT topic.
def publishRaceTimes(hexUID, name, completionTime):
    try:
        # setup the log manager
        myLog = logManager.logManager("main.py", "./log/")
        myLog.disableFileOutput()
        myLog.enableConsolePrint()

        # setup the mqttCore variable
        myPythonMQTTCore = mqttCore.mqttCore("rfid-aws", True, mqtt.MQTTv311, myLog)
        myPythonMQTTCore.setConnectDisconnectTimeoutSecond(90)
        myPythonMQTTCore.setMQTTOperationTimeoutSecond(10)
        myPythonMQTTCore.config(thingHost, 8883, rootCA[0], privateKey[0], certificate[0])

        # connect to the IoT service
        myPythonMQTTCore.connect()

        # get the current date and time and set the publish payload
        now = datetime.datetime.now(pytz.timezone(timezone)).strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        payload = json.dumps({'uid' : hexUID, 'name' : name, 'raceTime' : completionTime, 'createdDateTime' : now })
        
        # publish to the topic
        myPythonMQTTCore.publish(publishTopic, payload, 0, False)

        # disconnect from the IoT service
        myPythonMQTTCore.disconnect()

        # display a success message
        displayPublishSuccess()
    except AWSIoTExceptions.publishTimeoutException:
        print "Syncing reported data: A Publish Timeout Exception happened."
    except AWSIoTExceptions.publishError:
        print "Syncing reported data: A Publish Error happened."
    except Exception as e:
        print e

# Function to display a success message to the user
# after the race time is published to the AWS IoT service.
def displayPublishSuccess():
    with canvas(disp) as draw:
         # display the success message
        draw.text((0, 0),  "Awesome Job!", font=defaultFont, fill=255)
        draw.text((0, 17), "Record is", font=defaultFont, fill=255)
        draw.text((0, 32), "safe in the", font=defaultFont, fill=255)
        draw.text((0, 47), "cloud!", font=defaultFont, fill=255)

        # display the AWS logo bmp
        img = Image.open('images/aws.bmp')
        invertedImg = PIL.ImageOps.invert(img)
        draw.bitmap((80, 25), invertedImg, fill=1)
    time.sleep(5)
            

# Define a simple function to turn on the LED colors
# Since the RGB led I am using is a common anode,
# setting the value closer to 0 will set the led to a higher intensity
# and setting the value closer to 1 will lower the intensity
def color(R, G, B, on_time):
    # Color brightness range is 0-100%
    RED.ChangeDutyCycle(100 - R)
    GREEN.ChangeDutyCycle(100 - G)
    BLUE.ChangeDutyCycle(100 - B)
    time.sleep(on_time)

# Main function
def main():
    try:
        # setup loop counter
        loopCount = 0

        # loop forever and check for the presence of a rfid card
        while True:

            # since I have three images that rotate as the screensaver
            # mod the loopCount by 3 to display the correct image.  This
            # give the screen a plusing look.
            loopCount %= 3
            displayWelcome(loopCount)
            
            # check if a rfid card is on the reader
            (error, tag_type) = rfid.request()
            if not error:
                print "Tag detected"

            # anti-collision detection
            (error, uid) = rfid.anticoll()
            if not error:

                # get the card's uid in hex format
                hexUID = ''  
                for num in uid:
                    hexUID += format(num, 'x')

                # call displayUserData passing the uid
                displayUserData(hexUID)

            # increase loopCount by 1
            loopCount += 1


    # If CTRL+C is pressed the main loop is broken
    except KeyboardInterrupt:
        print "\Quitting"

    # Actions under 'finally' will always be called
    # regardless of what stopped the program
    finally:
        # Stop and cleanup so the pins
        # are available to be used again
        GPIO.cleanup()

if __name__ == '__main__':
    main()