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

import AWSIoTCommand


class commandConfig(AWSIoTCommand.AWSIoTCommand):
    # Target API: mqttCore.config(srcHost, srcPort, srcCAFile, srcKey, srcCert)
    _mqttCoreHandler = None

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "g"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 5

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "G T"
        if not self._validateCommand():
            returnMessage = "G1F: " + "No setup."
        else:
            try:
                self._mqttCoreHandler.config(self._parameterList[0], int(self._parameterList[1]), self._parameterList[2], self._parameterList[3], self._parameterList[4])
            except TypeError as e:
                returnMessage = "G2F: " + str(e.message)
            except Exception as e:
                returnMessage = "GFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
