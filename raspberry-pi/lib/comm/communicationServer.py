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


# Base class of communicationServer that handles message traffic across a certain type of tunnel (Socket/Serial bridge)
class communicationServer:
    def __init__(self):
        pass

    # Accept a message from the other side of the tunnel
    def accept(self):
        pass

    # Other server object writes to the internal buffer of communicationServer
    def writeToInternal(self, srcContent):
        pass

    # Upon a remote request, communicationServer write whatever is in the internal buffer to the remote client
    def writeToExternal(self):
        pass
