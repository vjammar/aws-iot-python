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
from AWSIoTExceptions import publishError
from AWSIoTExceptions import publishTimeoutException


class commandShadowGet(AWSIoTCommand.AWSIoTCommand):
    # Target API: deviceShadow.shadowGet(srcCallback, srcTimeout)
    # Parameters: deviceShadowName, sketchSubscribeSlot, srcTimeout, callback
    _shadowRegistrationTable = None
    _shadowSubscribeRecord = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcShadowRegistrationTable, srcShadowSubscribeRecord):
        self._commandProtocolName = "sg"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        # To get the corresponding registered deviceShadow instance
        self._shadowRegistrationTable = srcShadowRegistrationTable
        # To get update the sketch slot information
        self._shadowSubscribeRecord = srcShadowSubscribeRecord
        self._desiredNumberOfParameters = 4

    def _validateCommand(self):
        isNumberOfParameterMatched = AWSIoTCommand.AWSIoTCommand._validateCommand(self)
        isDataStructureExist = self._shadowRegistrationTable is not None and self._serialCommServerHandler is not None
        isDeviceShadowNameRegistered = False
        if isNumberOfParameterMatched and isDataStructureExist:
            isDeviceShadowNameRegistered = self._shadowRegistrationTable.get(self._parameterList[0]) is not None
        return isNumberOfParameterMatched and isDataStructureExist and isDeviceShadowNameRegistered

    def execute(self):
        returnMessage = "SG T"
        if not self._validateCommand():
            returnMessage = "SG1F: " + "No shadow init."
        else:
            try:
                currentDeviceShadow = self._shadowRegistrationTable.get(self._parameterList[0])  # By this time, currentDeviceShadow should never be None
                # Real shadow get
                tokenForThisRequest = currentDeviceShadow.shadowGet(self._parameterList[3], int(self._parameterList[2]))
                # Update sketch subscribe slot number
                self._shadowSubscribeRecord[tokenForThisRequest] = int(self._parameterList[1])
                # A waiting will be performed in the callback to wait until the data structure is ready for device shadow name registration
            except TypeError as e:
                returnMessage = "SG2F: " + str(e.message)
            # 2 subscriptions and 1 publish
            except subscribeError as e:
                returnMessage = "SG3F: " + str(e.message)
            except subscribeTimeoutException as e:
                returnMessage = "SG4F: " + str(e.message)
            except publishError as e:
                returnMessage = "SG5F: " + str(e.message)
            except publishTimeoutException as e:
                returnMessage = "SG6F: " + str(e.message)
            except Exception as e:
                returnMessage = "SGFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
