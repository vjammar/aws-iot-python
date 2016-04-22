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
from AWSIoTExceptions import disconnectError
from AWSIoTExceptions import disconnectTimeoutException


class commandDisconnect(AWSIoTCommand.AWSIoTCommand):
    # Target API: mqttCore.disconnect()
    _mqttCoreHandler = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "d"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 0

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "D T"
        if not self._validateCommand():
            returnMessage = "D1F: " + "No setup."
        else:
            try:
                self._mqttCoreHandler.disconnect()
            except disconnectError as e:
                returnMessage = "D2F: " + str(e.message)
            except disconnectTimeoutException as e:
                returnMessage = "D3F: " + str(e.message)
            except Exception as e:
                returnMessage = "DFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
