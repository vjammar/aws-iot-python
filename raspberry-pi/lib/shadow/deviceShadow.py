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
sys.path.append("../lib/util/")
sys.path.append("../lib/exception/")
import json
import string
import random
from threading import Timer, Lock


class _shadowRequestToken:
    _shadowName = ""
    _clientID = ""
    _sequenceNumber = 0

    def __init__(self, srcShadowName, srcClientID):
        self._shadowName = srcShadowName
        self._clientID = srcClientID

    def getNextToken(self):
        ret = self._clientID + "_" + self._shadowName + "_" + str(self._sequenceNumber) + "_" + self._randomString(5)
        self._sequenceNumber += 1
        return ret

    def _randomString(self, lengthOfString):
        return "".join(random.choice(string.lowercase) for i in range(lengthOfString))


class _basicJSONParser:
    _rawString = ""
    _dictionObject = None

    def setString(self, srcString):
        self._rawString = srcString

    def regenerateString(self):
        return json.dumps(self._dictionObject)

    def getAttributeValue(self, srcAttributeKey):
        return self._dictionObject.get(srcAttributeKey)

    def setAttributeValue(self, srcAttributeKey, srcAttributeValue):
        self._dictionObject[srcAttributeKey] = srcAttributeValue

    def validateJSON(self):
        try:
            self._dictionObject = json.loads(self._rawString)
        except ValueError:
            return False
        return True


class deviceShadow:
    # Tool handler
    _shadowManagerHandler = None
    _basicJSONParserHandler = _basicJSONParser()
    _tokenHandler = None
    # Properties
    _shadowName = ""
    _lastVersionInSync = -1  # -1 means not initialized
    _isPersistentSubscribe = False
    # Tool data structure
    _isGetSubscribed = False
    _isUpdateSubscribed = False
    _isDeleteSubscribed = False
    _shadowSubscribeCallbackTable = dict()
    _shadowSubscribeStatusTable = dict()
    _tokenPool = dict()
    _dataStructureLock = Lock()

    def __init__(self, srcShadowName, srcIsPersistentSubscribe, srcShadowManager):
        if srcShadowName is None or srcIsPersistentSubscribe is None or srcShadowManager is None:
            raise TypeError("None type inputs detected.")
        self._shadowName = srcShadowName
        self._isPersistentSubscribe = srcIsPersistentSubscribe
        self._shadowManagerHandler = srcShadowManager
        self._tokenHandler = _shadowRequestToken(self._shadowName, self._shadowManagerHandler.getClientID())
        self._shadowSubscribeCallbackTable["get"] = None
        self._shadowSubscribeCallbackTable["delete"] = None
        self._shadowSubscribeCallbackTable["update"] = None
        self._shadowSubscribeCallbackTable["delta"] = None
        self._shadowSubscribeStatusTable["get"] = 0
        self._shadowSubscribeStatusTable["delete"] = 0
        self._shadowSubscribeStatusTable["update"] = 0

    def _generalCallback(self, client, userdata, message):
        self._dataStructureLock.acquire()
        currentTopic = str(message.topic)
        currentAction = self._parseTopicAction(currentTopic)  # get/delete/update/delta
        currentType = self._parseTopicType(currentTopic)  # accepted/rejected/delta
        # get/delete/update: Need to deal with token, timer and unsubscribe
        if currentAction in ["get", "delete", "update"]:
            # Check for token
            self._basicJSONParserHandler.setString(str(message.payload))
            if self._basicJSONParserHandler.validateJSON():  # Filter out invalid JSON
                currentToken = self._basicJSONParserHandler.getAttributeValue(u"clientToken")
                if currentToken is not None and currentToken in self._tokenPool.keys():  # Filter out JSON without the desired token
                    # Sync local version when it is an accepted response
                    if currentType == "accepted":
                        incomingVersion = self._basicJSONParserHandler.getAttributeValue(u"version")
                        # If it is get/update accepted response, we need to sync the local version
                        if incomingVersion is not None and incomingVersion > self._lastVersionInSync and currentAction != "delete":
                            self._lastVersionInSync = incomingVersion
                        # If it is a delete accepted, we need to reset the version
                        else:
                            self._lastVersionInSync = -1  # The version will always be synced for the next incoming delta/GU-accepted response
                    # Cancel the timer and clear the token
                    self._tokenPool[currentToken].cancel()
                    del self._tokenPool[currentToken]
                    # Need to unsubscribe?
                    self._shadowSubscribeStatusTable[currentAction] -= 1
                    if not self._isPersistentSubscribe and self._shadowSubscribeStatusTable.get(currentAction) <= 0:
                        self._shadowSubscribeStatusTable[currentAction] = 0
                        self._shadowManagerHandler.basicShadowUnsubscribe(self._shadowName, currentAction)
                    # Custom callback
                    if self._shadowSubscribeCallbackTable.get(currentAction) is not None:
                        self._shadowSubscribeCallbackTable[currentAction](str(message.payload), currentType, currentToken)
        # delta: Watch for version
        else:
            currentType += "/" + self._parseTopicShadowName(currentTopic)
            # Sync local version
            self._basicJSONParserHandler.setString(str(message.payload))
            if self._basicJSONParserHandler.validateJSON():  # Filter out JSON without version
                incomingVersion = self._basicJSONParserHandler.getAttributeValue(u"version")
                if incomingVersion is not None and incomingVersion > self._lastVersionInSync:
                    self._lastVersionInSync = incomingVersion
                    # Custom callback
                    if self._shadowSubscribeCallbackTable.get(currentAction) is not None:
                        self._shadowSubscribeCallbackTable[currentAction](str(message.payload), currentType, None)
        self._dataStructureLock.release()

    def _parseTopicAction(self, srcTopic):
        ret = None
        fragments = srcTopic.split('/')
        if fragments[5] == "delta":
            ret = "delta"
        else:
            ret = fragments[4]
        return ret

    def _parseTopicType(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[5]

    def _parseTopicShadowName(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[2]

    def _timerHandler(self, srcActionName, srcToken):
        self._dataStructureLock.acquire()
        # Remove the token
        del self._tokenPool[srcToken]
        # Need to unsubscribe?
        self._shadowSubscribeStatusTable[srcActionName] -= 1
        if not self._isPersistentSubscribe and self._shadowSubscribeStatusTable.get(srcActionName) <= 0:
            self._shadowSubscribeStatusTable[srcActionName] = 0
            self._shadowManagerHandler.basicShadowUnsubscribe(self._shadowName, srcActionName)
        # Notify time-out issue
        if self._shadowSubscribeCallbackTable.get(srcActionName) is not None:
            self._shadowSubscribeCallbackTable[srcActionName]("REQUEST TIME OUT", "timeout", srcToken)
        self._dataStructureLock.release()

    def shadowGet(self, srcCallback, srcTimeout):
        self._dataStructureLock.acquire()
        # Update callback data structure
        self._shadowSubscribeCallbackTable["get"] = srcCallback
        # Update number of pending feedback
        self._shadowSubscribeStatusTable["get"] += 1
        # clientToken
        currentToken = self._tokenHandler.getNextToken()
        self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["get", currentToken])
        self._basicJSONParserHandler.setString("{}")
        self._basicJSONParserHandler.validateJSON()
        self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
        currentPayload = self._basicJSONParserHandler.regenerateString()
        self._dataStructureLock.release()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isGetSubscribed:
            self._shadowManagerHandler.basicShadowSubscribe(self._shadowName, "get", self._generalCallback)
            self._isGetSubscribed = True
        # One publish
        self._shadowManagerHandler.basicShadowPublish(self._shadowName, "get", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def shadowDelete(self, srcCallback, srcTimeout):
        self._dataStructureLock.acquire()
        # Update callback data structure
        self._shadowSubscribeCallbackTable["delete"] = srcCallback
        # Update number of pending feedback
        self._shadowSubscribeStatusTable["delete"] += 1
        # clientToken
        currentToken = self._tokenHandler.getNextToken()
        self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["delete", currentToken])
        self._basicJSONParserHandler.setString("{}")
        self._basicJSONParserHandler.validateJSON()
        self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
        currentPayload = self._basicJSONParserHandler.regenerateString()
        self._dataStructureLock.release()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isDeleteSubscribed:
            self._shadowManagerHandler.basicShadowSubscribe(self._shadowName, "delete", self._generalCallback)
            self._isDeleteSubscribed = True
        # One publish
        self._shadowManagerHandler.basicShadowPublish(self._shadowName, "delete", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def shadowUpdate(self, srcJSONPayload, srcCallback, srcTimeout):
        # Validate JSON
        JSONPayloadWithToken = None
        currentToken = None
        self._basicJSONParserHandler.setString(srcJSONPayload)
        if self._basicJSONParserHandler.validateJSON():
            self._dataStructureLock.acquire()
            # clientToken
            currentToken = self._tokenHandler.getNextToken()
            self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["update", currentToken])
            self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
            JSONPayloadWithToken = self._basicJSONParserHandler.regenerateString()
            # Update callback data structure
            self._shadowSubscribeCallbackTable["update"] = srcCallback
            # Update number of pending feedback
            self._shadowSubscribeStatusTable["update"] += 1
            self._dataStructureLock.release()
            # Two subscriptions
            if not self._isPersistentSubscribe or not self._isUpdateSubscribed:
                self._shadowManagerHandler.basicShadowSubscribe(self._shadowName, "update", self._generalCallback)
                self._isUpdateSubscribed = True
            # One publish
            self._shadowManagerHandler.basicShadowPublish(self._shadowName, "update", JSONPayloadWithToken)
            # Start the timer
            self._tokenPool[currentToken].start()
        else:
            raise ValueError("Invalid JSON file.")
        return currentToken

    def shadowRegisterDeltaCallback(self, srcCallback):
        self._dataStructureLock.acquire()
        # Update callback data structure
        self._shadowSubscribeCallbackTable["delta"] = srcCallback
        self._dataStructureLock.release()
        # One subscription
        self._shadowManagerHandler.basicShadowSubscribe(self._shadowName, "delta", self._generalCallback)

    def shadowUnregisterDeltaCallback(self):
        self._dataStructureLock.acquire()
        # Update callback data structure
        del self._shadowSubscribeCallbackTable["delta"]
        self._dataStructureLock.release()
        # One unsubscription
        self._shadowManagerHandler.basicShadowUnsubscribe(self._shadowName, "delta")
