# aws-iot-python
AWS Iot Python
Raspberry Pi 2 + OLED + RFID reader + RGB led + Waveshare laser transceiver
View demo here: [AWS IoT using Python and Raspberry Pi 2]

## Overview
AWS IoT project that utilizes several of AWS services to manage the flow of data and elastic infrastructure.

The usage for this sytem is as follows:
1. The user wants to record the time it takes for he/she to run a certain distance.

2. User has a personalized RFID card that they would take to the starting line.

3. User then places their card on he RFID reader.

4. At this point, the user's information is feteched from a web service hosted on Amazon's EC2 service.

5. The user information is then displayed on the oled screen.

6. After a short pause, the words READY->SET->GO! are displayed on the oled screen.

7. At this point, the user would begin their sprint and a timer is displayed on the oled screen.

8. To finish the race, the user would cross the laser at the finish line.

9. As soon as they break the laser, the timer stops and their time is published to an AWS IoT topic.

10. A rule is setup to automatically forward the payload of that topic toa lambda function that will update a chart in realtime using socket.io.

This repo is broken up into 4 folders:
1. 'raspberry-pi' - source code to put on the raspberry pi. Make a folder in your home folder called 'aws-iot-python' and place the contents of this folder in there.

2. 'flask-web-app' - source code for the flask app used to manage all web services.

3. 'lambda-function' - source code to upload to AWS's Lambda service. Simple function to pass the payload of a topic to a web service.

4. 'screenshots' - screenshots of the application.


## Prerequisites 
- AWS Account - See Amazon's "[Getting Started with AWS Iot on the Raspbery Pi]"
- AWS Iot SDK - https://github.com/aws/aws-iot-device-sdk-embedded-C
- AWS RDS MySQL instance running
- Git command line:
   
    ```sh
    $ sudo apt-get install git-core
    ```

## Materials Used (see screenshots folder for more info)
- Raspberry Pi 2 with wifi dongle
- Breadboard
- 128x64 Oled LCD Oled LED Module
- Mihappy RFID Sensor Module
- Waveshare Laser Receiver Module Laser Sensor Module Transmitter Module
- Single RGB LED (Common Anode)
- 270 OHM Resistor - Connected to the led
- Jumper Wires - Both male-to-male and male-to-female

## Installation

#### AWS Setup
Follow the guide on Amazon's "[Getting Started with AWS Iot on the Raspbery Pi]" to log into your AWS account, create your Iot "Thing" and generate the public, private, and device keys. You also need to download the [root certificate]. Once you have the "Thing" registered in AWS and all your keys, proceed on!

#### Basic Raspberry Pi Configuration
1. Install [raspbian] on the Raspberry Pi
2. Configure wifi on the Pi
    
    ```sh
    $ sudo /etc/wpa_supplicant/wpa_supplicant.conf 
    ```
    Edit the file to include your network details
    
    ```sh
    network={
        ssid="Your ssid"
        psk="Wifi pre-shared key"
    }
    ```
    Reboot and verify you are connected to the internet (ping www.google.com)
3. Update all packages that are currently installed:
    
    ```sh
    $ sudo apt-get update
    ```
4. Now that the Pi is connected to the internet and updated.

#### Setting up your flask web app
1. Log into your AWS account and navigate to the EC2 service.
2. Launch a new instance and select the default Ubuntu Amazon Image.
3. The size of this instance should be at least t2.medium (I tried micro but it kept running out of memory)
4. When the instance is up and running, ssh into it using your private key.
5. Follow this tutorial: [Launch Flask App on EC2 instance]
6. Once your 'hello world' app is running, you can replace the contents of the 'flaskapp' directory with the contents
of 'flask-web-app' from this repo.
7. You'll have to install several packages to get the flask up running. Run the following commands:
    
    ```sh
    $ sudo pip install flask-sqlalchemy
    $ sudo pip install flask-socketio
    $ sudo pip install PyMySQL
    ```

8. Edit 'flaskapp.py' and update line 15 with your MySQL connection string. Your database should have a table labled 'users' with 3 columns ('uid', 'name', and 'avatar').
9. Save your changes and restart the web app using the following command:

    ```sh
    $ sudo apachectl restart 
    ```

10. Test your web service by inserting a record into your database and calling one of the web services.


#### Setting up your lambda function
1. Go to 'lambda-function/lambda_function.py' and update line 19 with the url of your flask web app.
2. Highlight all 3 files/folders in that folder and make a zip file.
3. Log into your AWS account and navigate to the lambda service.
4. Make a new function and upload the zip file you created in step 2.

#### Raspberry Pi Configuration
1. Take the contents of the 'raspberry-pi' folder and upload them to a folder labled 'aws-iot-python' that is sitting in your home directory. The complete path should be /home/pi/aws-iot-python.
2. Place all your ceritifcates and private key in the folder labled 'certs'.
3. Edit main.py and update lines 24 to 40 with values that pretain to your environment. See below for my setup.
4. Run the main file using:

    ```sh
    $ python main.py
    ```

#### Wiring diagram (GPIO.BOARD)

| Waveshare laser |      Pi     |
| --------------- | ----------- | 
| DOUT            |      35     |     
| GND             |  GND (Any)  |
| 3.3V            |  3.3V (Any) |

| RFID Reader | Pi (SPI) |
| ----------- | -------- |
| SDA         |    24    |
| SCK         |    23    |
| MOSI        |    19    |
| MISO        |    21    |
| GND         |    9     |
| RST         |    22    |
| 3.3V        |    1     |

| OLED |    Pi (I2C)   |
| ---- | ------------- | 
| SDA  |      3        |
| SCL  |      5        |
| GND  |    GND (Any)  |
| 3.3V |   3.3V (Any)  |

| RGB led | Pi |
| ------- | -- |
| Red     | 36 |   
| Green   | 40 |
| Blue    | 38 |
| Cathode | 17 |

## Disclaimer
This project is in no way shape or form suitable for use commercial use. This project was purely for getting more familiar with Amazon's IoT service. Feel free to use this as a starting point for your own projects!

[AWS IoT using Python and Raspberry Pi 2]: https://youtu.be/GUXpuYni6zk
[Launch Flask App on EC2 instance]: <http://www.datasciencebytes.com/bytes/2015/02/24/running-a-flask-app-on-aws-ec2/>
[Getting Started with AWS Iot on the Raspbery Pi]: <http://docs.aws.amazon.com/iot/latest/developerguide/iot-device-sdk-c.html>
[raspbian]:<https://www.raspberrypi.org/downloads/raspbian/>
[root certificate]:<https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem>
