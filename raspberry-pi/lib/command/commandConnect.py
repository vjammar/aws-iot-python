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
from ssl import SSLError
from AWSIoTExceptions import connectError
from AWSIoTExceptions import connectTimeoutException


class commandConnect(AWSIoTCommand.AWSIoTCommand):
    # Target API: mqttCore.connect(keepAliveInterval)
    _mqttCoreHandler = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "c"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 1

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "C T"
        if not self._validateCommand():
            returnMessage = "C1F: " + "No setup."
        else:
            try:
                self._mqttCoreHandler.connect(int(self._parameterList[0]))
            except TypeError as e:
                returnMessage = "C2F: " + str(e.message)
            except SSLError as e:
                returnMessage = "C3F: " + "Mutual Auth issues."
            except connectError as e:
                returnMessage = "C4F: " + str(e.message)
            except connectTimeoutException as e:
                returnMessage = "C5F: " + str(e.message)
            except IOError as e:
                returnMessage = "C6F: " + "Credentials not found."
            except ValueError as e:
                returnMessage = "C7F: " + "Key/KeyID not in $ENV."
            except Exception as e:
                returnMessage = "CFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
