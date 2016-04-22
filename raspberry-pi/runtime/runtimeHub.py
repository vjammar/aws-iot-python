'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

import sys
sys.path.append("../lib/")
from util.logManager import logManager
from protocol.mqttCore import *
from exception.AWSIoTExceptions import *
from comm.serialCommunicationServer import *
from shadow.deviceShadow import *
from shadow.shadowManager import *
from command.AWSIoTCommand import *
from command.commandConnect import *
from command.commandDisconnect import *
from command.commandConfig import *
from command.commandPublish import *
from command.commandSubscribe import *
from command.commandUnsubscribe import *
from command.commandShadowGet import *
from command.commandShadowDelete import *
from command.commandShadowUpdate import *
from command.commandShadowRegisterDeltaCallback import *
from command.commandShadowUnregisterDeltaCallback import *
from command.commandYield import *
from command.commandLockSize import *
from protocol.paho.client import *
# import traceback


# Object for each MQTT subscription to hold the sketch info (slot #)
class _mqttSubscribeUnit:
    _topicName = None
    _sketchSlotNumber = -1
    _formatPayloadForYield = None
    _serialCommunicationServerHub = None

    def __init__(self, srcFormatPayloadForYieldFunctionPointer):
        self._formatPayloadForYield = srcFormatPayloadForYieldFunctionPointer

    def setTopicName(self, srcTopicName):
        self._topicName = srcTopicName

    def setSketchSlotNumber(self, srcSketchSlotNumber):
        self._sketchSlotNumber = srcSketchSlotNumber

    def setSerialCommunicationServerHub(self, srcSerialCommunicationServerHub):
        self._serialCommunicationServerHub = srcSerialCommunicationServerHub

    def getTopicName(self):
        return self._topicName

    def getSketchSlotNumber(self):
        return self._sketchSlotNumber

    def individualCallback(self, client, userdata, message):
        # Process the incoming non-shadow messages for a specific MQTT subscription
        # Parse them into protocol-style chunks that can be transmitted over the serial
        # and understood by Atmega
        # Execution of this callback is ATOMIC (Guaranteed by paho)
        ####
        # Get the topic
        currentTopic = str(message.topic)
        # Find the sketch slot related to this topic name, ignore if not exist any more
        try:
            currentSketchSlotNumber = self._sketchSlotNumber
            # Refactor the payload by adding protocol head and dividing into reasonable chunks
            formattedPayload = self._formatPayloadForYield(str(message.payload), currentSketchSlotNumber)
            # Put it into the internal queue of serialCommunicationServer
            self._serialCommunicationServerHub.writeToInternalYield(formattedPayload)
            # This message will get to be transmitted in future Yield requests
        except KeyError:
            pass  # Ignore messages coming between callback and unsubscription


class runtimeHub:
    # Objects
    _logManagerHub = None
    _serialCommunicationServerHub = None
    _mqttCoreHub = None  # Init when requested
    _shadowManagerHub = None  # Init when requested
    # Data structures
    # Keep the record of MQTT subscribe sketch info (slot #), in forms of individual object
    _mqttSubscribeTable = None
    # Keep the record of shadow subscribe sketch info (slot #)
    _shadowSubscribeRecord = None
    # Keep track of the deviceShadow instances for each individual deviceShadow name
    _shadowRegistrationTable = None

    #### Methods start here ####
    def __init__(self, srcFileName, srcDirectory):
        # Init with basic interface for logging and serial communication
        self._logManagerHub = logManager(srcFileName, srcDirectory)
        self._logManagerHub.disable()
        self._serialCommunicationServerHub = serialCommunicationServer(self._logManagerHub)
        self._serialCommunicationServerHub.setAcceptTimeout(10)
        self._serialCommunicationServerHub.setChunkSize(50)
        self._mqttSubscribeTable = dict()
        self._shadowSubscribeRecord = dict()
        self._shadowRegistrationTable = dict()

    def _findCommand(self, srcProtocolMessage):
        # Whatever comes out of this method should be an AWSIoTCommand
        # Invalid command will have a protocol name of "x"
        # Never raise exceptions
        retCommand = None
        if srcProtocolMessage is None:
            retCommand = AWSIoTCommand.AWSIoTCommand()
        else:
            # MQTT init
            if srcProtocolMessage[0] == "i":
                retCommand = AWSIoTCommand.AWSIoTCommand("i")
                if len(srcProtocolMessage[1:]) == 4:
                    clientID = srcProtocolMessage[1]
                    cleanSession = srcProtocolMessage[2] == "1"
                    protocol = MQTTv31
                    if srcProtocolMessage[3] == "4":
                        protocol = MQTTv311
                    useWebsocket = srcProtocolMessage[4] == "1"
                    try:
                        self._mqttCoreHub = mqttCore(clientID, cleanSession, protocol, self._logManagerHub, useWebsocket)
                        self._mqttCoreHub.setConnectDisconnectTimeoutSecond(10)
                        self._mqttCoreHub.setMQTTOperationTimeoutSecond(5)
                    except TypeError:
                        retCommand.setInitSuccess(False)  # Error in Init, set flag 
                else:
                    retCommand.setInitSuccess(False)  # Error in obtain parameters for Init
            # Config
            elif srcProtocolMessage[0] == "g":
                retCommand = commandConfig(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub)
            # Connect
            elif srcProtocolMessage[0] == "c":
                retCommand = commandConnect(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub)
            # Disconnect
            elif srcProtocolMessage[0] == "d":
                retCommand = commandDisconnect(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub)
            # Publish
            elif srcProtocolMessage[0] == "p":
                retCommand = commandPublish(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub)
            # Subscribe
            elif srcProtocolMessage[0] == "s":
                newMQTTSubscribeUnit = _mqttSubscribeUnit(self._formatPayloadForYield)  # Init an individual object for this subscribe
                newSrcProtocolMessage = srcProtocolMessage
                newSrcProtocolMessage.append(newMQTTSubscribeUnit)
                retCommand = commandSubscribe(newSrcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub, self._mqttSubscribeTable)
            # Unsubscribe
            elif srcProtocolMessage[0] == "u":
                retCommand = commandUnsubscribe(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._mqttCoreHub, self._mqttSubscribeTable)
            # Shadow init
            elif srcProtocolMessage[0] == "si":
                retCommand = AWSIoTCommand.AWSIoTCommand("si")
                if self._mqttCoreHub is None:
                    # Should have init a mqttCore and got it connected
                    retCommand.setInitSuccess(False)
                else:
                    # Init the shadowManager if needed
                    if self._shadowManagerHub is None:
                        self._shadowManagerHub = shadowManager(self._mqttCoreHub)
                    # Now register the requested deviceShadow name
                    if len(srcProtocolMessage[1:]) == 2:
                        srcShadowName = srcProtocolMessage[1]
                        srcIsPersistentSubscribe = srcProtocolMessage[2] == "1"
                        try:
                            newDeviceShadow = deviceShadow(srcShadowName, srcIsPersistentSubscribe, self._shadowManagerHub)
                            # Now update the registration table
                            self._shadowRegistrationTable[srcShadowName] = newDeviceShadow
                        except TypeError:
                            retCommand.setInitSuccess(False)
                    else:
                        retCommand.setInitSuccess(False)
            # Shadow get
            elif srcProtocolMessage[0] == "sg":
                newSrcProtocolMessage = srcProtocolMessage
                newSrcProtocolMessage.append(self._shadowCallback)
                retCommand = commandShadowGet(newSrcProtocolMessage[1:], self._serialCommunicationServerHub, self._shadowRegistrationTable, self._shadowSubscribeRecord)
            # Shadow update
            elif srcProtocolMessage[0] == "su":
                newSrcProtocolMessage = srcProtocolMessage
                newSrcProtocolMessage.append(self._shadowCallback)
                retCommand = commandShadowUpdate(newSrcProtocolMessage[1:], self._serialCommunicationServerHub, self._shadowRegistrationTable, self._shadowSubscribeRecord)
            # Shadow delete
            elif srcProtocolMessage[0] == "sd":
                newSrcProtocolMessage = srcProtocolMessage
                newSrcProtocolMessage.append(self._shadowCallback)
                retCommand = commandShadowDelete(newSrcProtocolMessage[1:], self._serialCommunicationServerHub, self._shadowRegistrationTable, self._shadowSubscribeRecord)
            # Shadow register delta
            elif srcProtocolMessage[0] == "s_rd":
                newSrcProtocolMessage = srcProtocolMessage
                newSrcProtocolMessage.append(self._shadowCallback)
                retCommand = commandShadowRegisterDeltaCallback(newSrcProtocolMessage[1:], self._serialCommunicationServerHub, self._shadowRegistrationTable, self._shadowSubscribeRecord)
            # Shadow unregister delta
            elif srcProtocolMessage[0] == "s_ud":
                retCommand = commandShadowUnregisterDeltaCallback(srcProtocolMessage[1:], self._serialCommunicationServerHub, self._shadowRegistrationTable, self._shadowSubscribeRecord)
            # Lock message size
            elif srcProtocolMessage[0] == "z":
                retCommand = commandLockSize(srcProtocolMessage[1:], self._serialCommunicationServerHub)
            # Oh the GREAT yield...
            elif srcProtocolMessage[0] == "y":
                retCommand = commandYield(srcProtocolMessage[1:], self._serialCommunicationServerHub)
            # Exit the runtimeHub
            elif srcProtocolMessage[0] == "~":
                retCommand = AWSIoTCommand.AWSIoTCommand("~")
            # Unsupported protocol
            else:
                retCommand = AWSIoTCommand.AWSIoTCommand()
        return retCommand

    def _formatPayloadForYield(self, srcPayload, srcSketchSlotNumber):
        # Generate the formatted payload for Yield requests
        ####
        # Generate the meta data
        hasMore = 1
        metaData = "Y " + str(srcSketchSlotNumber) + " " + str(hasMore) + " "
        # Get configured chunk size
        configuredChunkSize = self._serialCommunicationServerHub.getChunkSize()
        # Divide the payload into smaller chunks plus  meta data
        messageChunkSize = configuredChunkSize - len(metaData)
        chunks = [metaData + srcPayload[i:i+messageChunkSize] for i in range(0, len(srcPayload), messageChunkSize)]
        # Change hasMore flag for the last chunk
        chunks[len(chunks)-1] = "Y " + str(srcSketchSlotNumber) + " 0 " + chunks[len(chunks)-1][len(metaData):]
        # Concat them together
        return "".join(chunks)        

    # Callbacks
    def _shadowCallback(self, srcPayload, srcCurrentType, srcCurrentToken):
        # Process the incoming shadow messages
        # Parse them into protocol-style chunks that can be transimitted over the serial
        # and understood by Atmega
        # Execution of this callback is ATOMIC for each shadow action in ONE deviceShadow (Guaranteed by SDK)
        # All token/version controls are performed at deviceShadow level
        # Whatever comes in here should be delivered across serial, with care, of course
        ####
        # srcCurrentType: accepted//rejected//<deviceShadowName>/delta
        currentSketchSlotNumber = -1
        try:
            # Wait util internal data structure is updated
            if srcCurrentToken is not None:
                while srcCurrentToken not in self._shadowSubscribeRecord.keys():
                    pass
            # accepted//rejected: Find the sketch slot number by token
            if srcCurrentType in ["accepted", "rejected", "timeout"]:
                currentSketchSlotNumber = self._shadowSubscribeRecord[srcCurrentToken]
                del self._shadowSubscribeRecord[srcCurrentToken]  # Retrieve the memory in dict
            # delta/<deviceShadowName>: Find the sketch slot number by deviceShadowName
            else:
                fragments = srcCurrentType.split("/")
                deviceShadowNameForDelta = fragments[1]
                currentSketchSlotNumber = self._shadowSubscribeRecord[deviceShadowNameForDelta]
            # Refactor the payload by adding protocol head and dividing into reasonable chunks
            formattedPayload = self._formatPayloadForYield(srcPayload, currentSketchSlotNumber)
            # Put it into the internal queue of the serialCommunicationServer
            self._serialCommunicationServerHub.writeToInternalYield(formattedPayload)
            # This message will get to be transmitted in future Yield requests
        except KeyError as e:
            pass  # Ignore messages coming between callback and unregister delta 

    # Runtime function
    def run(self):
        while True:
            try:
                # Start the serialCommunicationServer and accepts protocol messages
                # Raises AWSIoTExceptions.acceptTimeoutException
                currentProtocolMessage = self._serialCommunicationServerHub.accept()
                # Find with command request this is
                currentCommand = self._findCommand(currentProtocolMessage)
                # See if the command is an init (MQTT/Shadow) that needs data structure operations
                currentCommandProtocolName = currentCommand.getCommandProtocolName()
                if currentCommandProtocolName == "x":
                    pass # Ignore invalid protocol command
                if currentCommandProtocolName == "i":  # MQTT init
                    if currentCommand.getInitSuccess():
                        self._serialCommunicationServerHub.writeToInternalProtocol("I T")
                    else:
                        self._serialCommunicationServerHub.writeToInternalProtocol("I F")
                    self._serialCommunicationServerHub.writeToExternalProtocol()
                elif currentCommandProtocolName == "si":  # Shadow init
                    if currentCommand.getInitSuccess():
                        self._serialCommunicationServerHub.writeToInternalProtocol("SI T")
                    else:
                        self._serialCommunicationServerHub.writeToInternalProtocol("SI F")
                    self._serialCommunicationServerHub.writeToExternalProtocol()
                elif currentCommandProtocolName == "~":  # Exit
                    break
                else:  # Other command
                    # Execute the command
                    currentCommand.execute()
                    # Write the result back through serial (detailed error code is transmitted here)
                    if currentCommandProtocolName == "y":
                        self._serialCommunicationServerHub.writeToExternalYield()
                    else:
                        self._serialCommunicationServerHub.writeToExternalProtocol()

            except AWSIoTExceptions.acceptTimeoutException as e:
                self._logManagerHub.writeLog(str(e.message))
                break
            except Exception as e:
                self._logManagerHub.writeLog("Exception in run: " + str(type(e)) + str(e.message))
                # traceback.print_exc(file, sys.stdout)
