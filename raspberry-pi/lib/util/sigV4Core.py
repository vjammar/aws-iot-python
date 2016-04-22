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

# This class implements the sigV4 signing process and return the signed URL for connection

import os
import datetime
import hashlib
import hmac


class sigV4Core:

    def _createAmazonDate(self):
        amazonDate = []
        currentTime = datetime.datetime.utcnow()
        YMDHMS = currentTime.strftime('%Y%m%dT%H%M%SZ')
        YMD = YMDHMS[0:YMDHMS.index('T')]
        amazonDate.append(YMD)
        amazonDate.append(YMDHMS)
        return amazonDate

    def _sign(self, key, message):
        return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()

    def _getSignatureKey(self, key, dateStamp, regionName, serviceName):
        kDate = self._sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = self._sign(kDate, regionName)
        kService = self._sign(kRegion, serviceName)
        kSigning = self._sign(kService, 'aws4_request')
        return kSigning

    def _checkKeyInEnv(self):
        ret = []
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if aws_access_key_id is not None and aws_secret_access_key is not None:
            ret.append(aws_access_key_id)
            ret.append(aws_secret_access_key)
        return ret

    def createWebsocketEndpoint(self, host, port, region, method, awsServiceName, path):
        # Gather all the facts
        amazonDate = self._createAmazonDate()
        amazonDateSimple = amazonDate[0]
        amazonDateComplex = amazonDate[1]
        idKeyPair = self._checkKeyInEnv()
        if idKeyPair == []:
            return ""
        else:
            keyID = idKeyPair[0]
            secretKey = idKeyPair[1]
            queryParameters = "X-Amz-Algorithm=AWS4-HMAC-SHA256" + \
                "&X-Amz-Credential=" + keyID + "%2F" + amazonDateSimple + "%2F" + region + "%2F" + awsServiceName + "%2Faws4_request" + \
                "&X-Amz-Date=" + amazonDateComplex + \
                "&X-Amz-Expires=86400" + \
                "&X-Amz-SignedHeaders=host"
            hashedPayload = hashlib.sha256("").hexdigest()
            # Create the string to sign
            signedHeaders = "host"
            canonicalHeaders = "host:" + host + "\n"
            canonicalRequest = method + "\n" + path + "\n" + queryParameters + "\n" + canonicalHeaders + "\n" + signedHeaders + "\n" + hashedPayload
            hashedCanonicalRequest = hashlib.sha256(canonicalRequest).hexdigest()
            stringToSign = "AWS4-HMAC-SHA256\n" + amazonDateComplex + "\n" + amazonDateSimple + "/" + region + "/" + awsServiceName + "/aws4_request\n" + hashedCanonicalRequest
            # Sign it
            signingKey = self._getSignatureKey(secretKey, amazonDateSimple, region, awsServiceName)
            signature = hmac.new(signingKey, (stringToSign).encode("utf-8"), hashlib.sha256).hexdigest()
            # generate url
            url = "wss://" + host + ":" + str(port) + path + '?' + queryParameters + "&X-Amz-Signature=" + signature
            return url
