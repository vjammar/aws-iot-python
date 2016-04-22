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
sys.path.append("./lib/")
sys.path.append("../lib/")
import ssl
import time
import protocol.paho.client as mqtt
from threading import Lock
from exception.AWSIoTExceptions import connectError
from exception.AWSIoTExceptions import connectTimeoutException
from exception.AWSIoTExceptions import disconnectError
from exception.AWSIoTExceptions import disconnectTimeoutException
from exception.AWSIoTExceptions import publishError
from exception.AWSIoTExceptions import subscribeError
from exception.AWSIoTExceptions import subscribeTimeoutException
from exception.AWSIoTExceptions import unsubscribeError
from exception.AWSIoTExceptions import unsubscribeTimeoutException


class mqttCore:
    # Tool handler
    _pahoClient = None
    _log = None
    # Tool data structure
    _clientID = ""
    _connectResultCode = sys.maxint
    _disconnectResultCode = sys.maxint
    _subscribeSent = False
    _unsubscribeSent = False
    _connectdisconnectTimeout = 0  # Default connect/disconnect timeout set to 0 second
    _mqttOperationTimeout = 0  # Default MQTT operation timeout set to 0 second
    # Use websocket
    _useWebsocket = False
    # Broker information
    _host = ""
    _port = -1
    _cafile = ""
    _key = ""
    _cert = ""
    # Operation mutex
    _publishLock = Lock()
    _subscribeLock = Lock()
    _unsubscribeLock = Lock()

    def getClientID(self):
        return self._clientID

    def setConnectDisconnectTimeoutSecond(self, srcConnectDisconnectTimeout):
        self._connectdisconnectTimeout = srcConnectDisconnectTimeout
        self._log.writeLog("Set maximum connect/disconnect timeout to be " + str(self._connectdisconnectTimeout) + " second.")

    def getConnectDisconnectTimeoutSecond(self):
        return self._connectdisconnectTimeout

    def setMQTTOperationTimeoutSecond(self, srcMQTTOperationTimeout):
        self._mqttOperationTimeout = srcMQTTOperationTimeout
        self._log.writeLog("Set maximum MQTT operation timeout to be " + str(self._mqttOperationTimeout) + " second")

    def getMQTTOperationTimeoutSecond(self):
        return self._mqttOperationTimeout

    def setUserData(self, srcUserData):
        self._pahoClient.user_data_set(srcUserData)

    def createPahoClient(self, clientID, cleanSession, userdata, protocol, useWebsocket):
        return mqtt.Client(clientID, cleanSession, userdata, protocol, useWebsocket)  # Throw exception when error happens

    # Callbacks
    def on_connect(self, client, userdata, flags, rc):
        self._disconnectResultCode = sys.maxint
        self._connectResultCode = rc
        self._log.writeLog("Connect result code " + str(rc))

    def on_disconnect(self, client, userdata, rc):
        self._connectResultCode = sys.maxint
        self._disconnectResultCode = rc
        self._log.writeLog("Disconnect result code " + str(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        self._subscribeSent = True
        self._log.writeLog("Subscribe request " + str(mid) + " sent.")

    def on_unsubscribe(self, client, userdata, mid):
        self._unsubscribeSent = True
        self._log.writeLog("Unsubscribe request sent.")

    def on_message(self, client, userdata, message):
        # Generic message callback
        self._log.writeLog("Received (No custom callback registered) : message: " + str(message.payload) + " from topic: " + str(message.topic))

    ####### API starts here #######
    def __init__(self, clientID, cleanSession, protocol, srcLogManager, srcUseWebsocket=False):
        if clientID is None or cleanSession is None or protocol is None or srcLogManager is None:
            raise TypeError("None type inputs detected.")
        self._log = srcLogManager
        self._clientID = clientID
        self._pahoClient = self.createPahoClient(clientID, cleanSession, None, protocol, srcUseWebsocket)  # User data is set to None as default
        self._log.writeLog("Paho MQTT Client init.")
        self._pahoClient.on_connect = self.on_connect
        self._pahoClient.on_disconnect = self.on_disconnect
        self._pahoClient.on_message = self.on_message
        self._pahoClient.on_subscribe = self.on_subscribe
        self._pahoClient.on_unsubscribe = self.on_unsubscribe
        self._useWebsocket = srcUseWebsocket
        self._log.writeLog("Register Paho MQTT Client callbacks.")
        self._log.writeLog("mqttCore init.")

    def config(self, srcHost, srcPort, srcCAFile, srcKey, srcCert):
        if srcHost is None or srcPort is None or srcCAFile is None or srcKey is None or srcCert is None:
            raise TypeError("None type inputs detected.")
        self._host = srcHost
        self._port = srcPort
        self._cafile = srcCAFile
        self._key = srcKey
        self._cert = srcCert
        self._log.writeLog("Load CAFile, Key, Cert configuration.")

    # MQTT connection
    def connect(self, keepAliveInterval=60):
        if(keepAliveInterval is None):
            raise TypeError("None type inputs detected.")
        # Return connect succeeded/failed
        ret = False
        # TLS configuration
        if self._useWebsocket:
            self._pahoClient.tls_set(ca_certs=self._cafile, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_SSLv23)
        else:
            self._pahoClient.tls_set(self._cafile, self._cert, self._key, ssl.CERT_REQUIRED, ssl.PROTOCOL_SSLv23)  # Throw exception...
        # Connect
        self._pahoClient.connect(self._host, self._port, keepAliveInterval)  # Throw exception...
        self._pahoClient.loop_start()
        TenmsCount = 0
        while(TenmsCount != self._connectdisconnectTimeout * 100 and self._connectResultCode == sys.maxint):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._connectResultCode == sys.maxint):
            self._log.writeLog("Connect timeout.")
            self._pahoClient.loop_stop()
            raise connectTimeoutException()
        elif(self._connectResultCode == 0):
            ret = True
            self._log.writeLog("Connect time consumption: " + str(float(TenmsCount) * 10) + "ms.")
        else:
            self._log.writeLog("A connect error happened.")
            self._pahoClient.loop_stop()
            raise connectError(self._connectResultCode)
        return ret

    def disconnect(self):
        # Return disconnect succeeded/failed
        ret = False
        # Disconnect
        self._pahoClient.disconnect()  # Throw exception...
        TenmsCount = 0
        while(TenmsCount != self._connectdisconnectTimeout * 100 and self._disconnectResultCode == sys.maxint):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._disconnectResultCode == sys.maxint):
            self._log.writeLog("Disconnect timeout.")
            raise disconnectTimeoutException()
        elif(self._disconnectResultCode == 0):
            ret = True
            self._log.writeLog("Disconnect time consumption: " + str(float(TenmsCount) * 10) + "ms.")
            self._pahoClient.loop_stop()  # Do NOT maintain a background thread for socket communication since it is a successful disconnect
        else:
            self._log.writeLog("A disconnect error happened.")
            raise disconnectError(self._disconnectResultCode)
        return ret

    def publish(self, topic, payload, qos, retain):
        if(topic is None or payload is None or qos is None or retain is None):
            raise TypeError("None type inputs detected.")
        # Return publish succeeded/failed
        ret = False
        self._publishLock.acquire()
        # Publish
        (rc, mid) = self._pahoClient.publish(topic, payload, qos, retain)  # Throw exception...
        self._log.writeLog("Try to put a publish request " + str(mid) + " in the TCP stack.")
        ret = rc == 0
        if(ret):
            self._log.writeLog("Publish request " + str(mid) + " succeeded.")
        else:
            self._log.writeLog("Publish request " + str(mid) + " failed with code: " + str(rc))
            self._publishLock.release()  # Release the lock when exception is raised
            raise publishError(rc)
        self._publishLock.release()
        return ret

    def subscribe(self, topic, qos, callback):
        if(topic is None or qos is None):
            raise TypeError("None type inputs detected.")
        # Return subscribe succeeded/failed
        ret = False
        self._subscribeLock.acquire()
        # Subscribe
        # Register callback
        if(callback is not None):
            self._pahoClient.message_callback_add(topic, callback)
        (rc, mid) = self._pahoClient.subscribe(topic, qos)  # Throw exception...
        self._log.writeLog("Started a subscribe request " + str(mid))
        TenmsCount = 0
        while(TenmsCount != self._mqttOperationTimeout * 100 and not self._subscribeSent):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._subscribeSent):
            ret = rc == 0
            if(ret):
                self._log.writeLog("Subscribe request " + str(mid) + " succeeded. Time consumption: " + str(float(TenmsCount) * 10) + "ms.")
            else:
                if(callback is not None):
                    self._pahoClient.message_callback_remove(topic)
                self._log.writeLog("Subscribe request " + str(mid) + " failed with code: " + str(rc))
                self._log.writeLog("Callback cleaned up.")
                self._subscribeLock.release()  # Release the lock when exception is raised
                raise subscribeError(rc)
        else:
            # Subscribe timeout
            if(callback is not None):
                self._pahoClient.message_callback_remove(topic)
            self._log.writeLog("No feedback detected for subscribe request " + str(mid) + ". Timeout and failed.")
            self._log.writeLog("Callback cleaned up.")
            self._subscribeLock.release()  # Release the lock when exception is raised
            raise subscribeTimeoutException()
        self._subscribeSent = False
        self._log.writeLog("Recover subscribe context for the next request: subscribeSent: " + str(self._subscribeSent))
        self._subscribeLock.release()
        return ret

    def unsubscribe(self, topic):
        if(topic is None):
            raise TypeError("None type inputs detected.")
        # Return unsubscribe succeeded/failed
        ret = False
        self._unsubscribeLock.acquire()
        # Unsubscribe
        (rc, mid) = self._pahoClient.unsubscribe(topic)  # Throw exception...
        self._log.writeLog("Started an unsubscribe request " + str(mid))
        TenmsCount = 0
        while(TenmsCount != self._mqttOperationTimeout * 100 and not self._unsubscribeSent):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._unsubscribeSent):
            ret = rc == 0
            if(ret):
                self._log.writeLog("Unsubscribe request " + str(mid) + " succeeded. Time consumption: " + str(float(TenmsCount) * 10) + "ms.")
                self._pahoClient.message_callback_remove(topic)
                self._log.writeLog("Remove the callback.")
            else:
                self._log.writeLog("Unsubscribe request " + str(mid) + " failed with code: " + str(rc))
                self._unsubscribeLock.release()  # Release the lock when exception is raised
                raise unsubscribeError(rc)
        else:
            # Unsubscribe timeout
            self._log.writeLog("No feedback detected for unsubscribe request " + str(mid) + ". Timeout and failed.")
            self._unsubscribeLock.release()  # Release the lock when exception is raised
            raise unsubscribeTimeoutException()
        self._unsubscribeSent = False
        self._log.writeLog("Recover unsubscribe context for the next request: unsubscribeSent: " + str(self._unsubscribeSent))
        self._unsubscribeLock.release()
        return ret
