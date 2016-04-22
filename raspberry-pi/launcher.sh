#!/bin/bash
# launcher.sh
# navigate to home directory, then to this direcotry, then execute program

STATE="error";

while [ $STATE = "error" ]
 do
    #do a ping and check that its not a default message or change to grep for something else
    STATE=$(ping -q -w 1 -c 1 `ip r | grep default | cut -d ' ' -f 3` > /dev/null && echo ok || echo error)

    #sleep for 2 seconds and try again
    sleep 2
 done

cd /
cd home/pi/aws-iot-python
sudo python main.py