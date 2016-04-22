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

import threading
import datetime


class logManager:
    _mutex = threading.Lock()
    _directory = None
    _fileHandler = None
    _fileName = None
    _enable = True
    _lastTimeStamp = None
    _consolePrint = True
    _fileOutput = False

    def __init__(self, srcFileName, srcDirectory):
        if srcFileName is None or srcDirectory is None:
            raise TypeError("None type inputs detected.")
        self._fileName = srcFileName + "_" + str(datetime.datetime.now()) + ".log"
        self._directory = srcDirectory

    def getFileName(self):
        return self._fileName

    def getDirectory(self):
        return self._directory

    def getLastTimeStamp(self):
        return self._lastTimeStamp

    def enable(self):
        self._enable = True

    def disable(self):
        self._enable = False

    def enableConsolePrint(self):
        self._consolePrint = True

    def disableConsolePrint(self):
        self._consolePrint = False

    def enableFileOutput(self):
        self._fileOutput = True

    def disableFileOutput(self):
        self._fileOutput = False

    def writeLog(self, log):
        if(self._enable):
            self._mutex.acquire()
            self._lastTimeStamp = str(datetime.datetime.now())
            newLog = "[" + self._lastTimeStamp + "] " + log
            if(self._fileOutput):
                self._fileHandler = open(self._directory + self._fileName, "a+")
                self._fileHandler.write(newLog + "\n")
                self._fileHandler.close()
            if(self._consolePrint):
                print newLog
            self._mutex.release()
        else:
            pass
