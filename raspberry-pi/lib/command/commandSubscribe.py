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
sys.path.append("../lib/exception/")
import AWSIoTCommand
from AWSIoTExceptions import subscribeError
from AWSIoTExceptions import subscribeTimeoutException


class commandSubscribe(AWSIoTCommand.AWSIoTCommand):
    # Target API: mqttCore.subscribe(topic, qos, callback)
    # Parameter list: <topic> <qos> <ino_id> <mqttSubscribeUnit>
    _mqttCoreHandler = None
    _mqttSubscribeUnit = None
    _mqttSubscribeTable = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore, srcMQTTSubscribeTable):
        self._commandProtocolName = "s"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._mqttSubscribeTable = srcMQTTSubscribeTable
        self._desiredNumberOfParameters = 4

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "S T"
        if not self._validateCommand():
            returnMessage = "S1F: " + "No setup."
        else:
            try:
                # Init the mqttSubscribeUnit
                self._mqttSubscribeUnit = self._parameterList[3]
                self._mqttSubscribeUnit.setTopicName(self._parameterList[0])
                self._mqttSubscribeUnit.setSketchSlotNumber(int(self._parameterList[2]))
                self._mqttSubscribeUnit.setSerialCommunicationServerHub(self._serialCommServerHandler)
                # Real subscription
                self._mqttCoreHandler.subscribe(self._parameterList[0], int(self._parameterList[1]), self._mqttSubscribeUnit.individualCallback)
                # Update mqttSubscribeTable
                self._mqttSubscribeTable[self._parameterList[0]] = self._mqttSubscribeUnit
            except TypeError as e:
                returnMessage = "S2F: " + str(e.message)
            except subscribeError as e:
                returnMessage = "S3F: " + str(e.message)
            except subscribeTimeoutException as e:
                returnMessage = "S4F: " + str(e.message)
            except Exception as e:
                returnMessage = "SFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
