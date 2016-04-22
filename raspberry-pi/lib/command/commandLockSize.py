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


class commandLockSize(AWSIoTCommand.AWSIoTCommand):
    # Target API: None

    def __init__(self, srcParameterList, srcSerialCommuteServer):
        self._commandProtocolName = "z"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._desiredNumberOfParameters = 0

    def _validateCommand(self):
        ret = self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "Z T"
        if not self._validateCommand():
            returnMessage = "Z F: " + "Invalid information."
        else:
            try:
                self._serialCommServerHandler.updateLockedQueueSize()
            except Exception as e:
                returnMessage = "Z F: " + "Unknown Error " + str(type(e))
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
