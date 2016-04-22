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
from AWSIoTExceptions import unsubscribeError
from AWSIoTExceptions import unsubscribeTimeoutException


class commandUnsubscribe(AWSIoTCommand.AWSIoTCommand):
    # Target API: mqttCore.unsubscribe(topic)
    _mqttCoreHandler = None
    _mqttSubscribeTable = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore, srcMQTTSubscribeTable):
        self._commandProtocolName = "u"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._mqttSubscribeTable = srcMQTTSubscribeTable
        self._desiredNumberOfParameters = 1

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "U T"
        if not self._validateCommand():
            returnMessage = "U1F: " + "No setup."
        else:
            try:
                thisSubscribeUnit = self._mqttSubscribeTable.get(self._parameterList[0])
                if thisSubscribeUnit is not None:
                    returnMessage = "U " + str(thisSubscribeUnit.getSketchSlotNumber())
                # Real unsubscription
                self._mqttCoreHandler.unsubscribe(self._parameterList[0])
                # Update mqttSubscribeTable
                del self._mqttSubscribeTable[self._parameterList[0]]
            except KeyError as e:
                pass  # Ignore unsubscribe to a topic that never been subscribed
            except TypeError as e:
                returnMessage = "U2F: " + str(e.message)
            except unsubscribeError as e:
                returnMessage = "U3F: " + str(e.message)
            except unsubscribeTimeoutException as e:
                returnMessage = "U4F: " + str(e.message)
            except Exception as e:
                returnMessage = "UFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
