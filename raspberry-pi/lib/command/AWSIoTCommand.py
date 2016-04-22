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


class AWSIoTCommand:
    _commandProtocolName = None
    _parameterList = None
    _serialCommServerHandler = None
    _desiredNumberOfParameters = 0
    _initSuccess = True

    def __init__(self, srcCommandProtocolName="x"):
        self._commandProtocolName = srcCommandProtocolName
        self._parameterList = []

    def _validateCommand(self):
        if self._parameterList is None:
            return False
        else:
            return len(self._parameterList) == self._desiredNumberOfParameters

    def getCommandProtocolName(self):
        return self._commandProtocolName

    def setInitSuccess(self, src):
        self._initSuccess = src

    def getInitSuccess(self):
        return self._initSuccess

    def execute(self):
        pass
