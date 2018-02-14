#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
BlueIris Indigo Plugin
First draft

"""
import logging
import sys
import requests
import json
import hashlib
import datetime
import time as t
import urllib2
import os
import shutil

try:
    import indigo
except:
    pass

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuPollInterval': "300",  # Frequency of refreshes.
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    # u'refreshFreq': 300,  # Device-specific update frequency
    u'showDebugInfo': False,  # Verbose debug logging?
    u'configUpdaterForceUpdate': False,
    u'configUpdaterInterval': 24,
    u'showDebugLevel': "1",  # Low, Medium or High debug output.
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.startingUp = True
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False
        self.prefsUpdated = False
        self.system_name = ''
        self.session =''
        self.logger.info(u"")
        self.logger.info(u"{0:=^130}".format(" Initializing New Plugin Session "))
        self.logger.info(u"{0:<30} {1}".format("Plugin name:", pluginDisplayName))
        self.logger.info(u"{0:<30} {1}".format("Plugin version:", pluginVersion))
        self.logger.info(u"{0:<30} {1}".format("Plugin ID:", pluginId))
        self.logger.info(u"{0:<30} {1}".format("Indigo version:", indigo.server.version))
        self.logger.info(u"{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        self.logger.info(u"{0:<30} {1}".format("Python Directory:", sys.prefix.replace('\n', '')))
        self.logger.info(u"{0:=^130}".format(""))

        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)

        try:
            self.logLevel = int(self.pluginPrefs[u"showDebugLevel"])
        except:
            self.logLevel = logging.INFO

        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.debug(u"logLevel = " + str(self.logLevel))
        self.triggers = {}

        self.serverip = self.pluginPrefs.get('serverip', '')
        self.serverport = int(self.pluginPrefs.get('serverport', '80'))
        self.serverusername = self.pluginPrefs.get('serverusername', '')
        self.serverpassword = self.pluginPrefs.get('serverpassword', '')

        self.debugLevel = self.pluginPrefs.get('showDebugLevel', "20")
        self.debugextra = self.pluginPrefs.get('debugextra', False)

        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.configUpdaterInterval = self.pluginPrefs.get('configUpdaterInterval', 24)
        self.configUpdaterForceUpdate = self.pluginPrefs.get('configUpdaterForceUpdate', False)

        self.pluginIsInitializing = False
        indigo.variables.subscribeToChanges()

    def createupdatevariable(self, variable, result):

        self.logger.debug(u'createupdate variable called.')
        if 'BlueIris' not in indigo.variables.folders:
            indigo.variables.folder.create('BlueIris')

        if variable not in indigo.variables:
            indigo.variable.create(variable, str(result), folder='BlueIris')
            return
        else:
            indigo.variable.updateValue(str(variable), str(result))

        return

    def __del__(self):
        if self.debugLevel >= 2:
            self.debugLog(u"__del__ method called.")
        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if self.debugLevel >= 2:
            self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debugLevel = valuesDict.get('showDebugLevel', "10")
            self.debugLog(u"User prefs saved.")

            try:
                self.logLevel = int(valuesDict[u"showDebugLevel"])
            except:
                self.logLevel = logging.INFO

            self.indigo_log_handler.setLevel(self.logLevel)
            self.logger.debug(u"logLevel = " + str(self.logLevel))
            self.logger.debug(u"User prefs saved.")
            self.logger.debug(u"Debugging on (Level: {0})".format(self.debugLevel))
            self.serverip = valuesDict.get('serverip', False)
            self.serverport = int(valuesDict.get('serverport', '80'))
            self.serverusername = valuesDict.get('serverusername', '')
            self.serverpassword = valuesDict.get('serverpassword','')
            self.prefsUpdated = True
            self.debugextra = valuesDict.get('debugextra', False)
            # Attempt to connnect to BlueIris and get sesion
            if self.connectServer():
                self.logger.debug(u'Connection established to Blueiris Server:'+unicode(self.system_name))
            else:
                self.logger.info(u'Cannot connect to Blue Iris Server.  Check Username/Password/Server Details')
                return False
        return True

    def validatePrefsConfigUi(self, valuesDict):
        """ docstring placeholder """
        self.logger.debug(u"--- validatePrefsConfigUi() method called.")

        errorDict = indigo.Dict()

        if 'serverip' in valuesDict:
            iFail = False
            if len(valuesDict['serverip']) == 0:
                # Blank username!
                iFail = True
                errorDict["serverip"] = "No Server IP entered"
                errorDict[
                    "showAlertText"] = "You must enter valid BlueIris Server IP address e.g. 192.168.1.208"
            if iFail:
                return (False, valuesDict, errorDict)
        else:
            return False, valuesDict

        if 'serverport' in valuesDict:
            iFail = False
            if len(valuesDict['serverport']) == 0:
                # Blank password!
                iFail = True
                errorDict["serverport"] = "No port entered"
                errorDict["showAlertText"] = "You must enter a valid BlueIris Port"
            if iFail:
                self.logger.info("Server Port failed")
                return (False, valuesDict, errorDict)

        if 'serverusername' in valuesDict:
            iFail = False
            if len(valuesDict['serverusername']) == 0:
                # Blank username!
                iFail = True
                errorDict["serverusername"] = "No Server Username entered"
                errorDict[
                    "showAlertText"] = "You must enter valid BlueIris Server Username"
            if iFail:
                return (False, valuesDict, errorDict)
        else:
            return False, valuesDict

        if 'serverpassword' in valuesDict:
            iFail = False
            if len(valuesDict['serverpassword']) == 0:
                # Blank password!
                iFail = True
                errorDict["serverpassword"] = "No password entered"
                errorDict["showAlertText"] = "You must enter a valid BlueIris Password"

            if iFail:
                self.logger.info("Server Password failed")
                return (False, valuesDict, errorDict)

        if 'serverip' in valuesDict and 'serverport' in valuesDict and 'serverusername' in valuesDict  and 'serverpassword' in valuesDict:

            # Validate login
            return True, valuesDict

        return True, valuesDict


    # Start 'em up.
    def deviceStartComm(self, dev):

        self.debugLog(u"deviceStartComm() method called.")
        dev.stateListOrDisplayStateIdChanged()

    # Shut 'em down.
    def deviceStopComm(self, dev):

        self.debugLog(u"deviceStopComm() method called.")
        indigo.server.log(u"Stopping device: " + dev.name)

    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    def generateCameras(self, valuesDict):
        self.logger.debug(u'generate Cameras called')
        # Generate Cameras - main check will not create cameras if deleted

        camlist = {}
        results = self.sendccommand('camlist')
        x = 0
        for i in range(len(results)):
            if 'ManRecLimit' in results[i]:
                camlist[x] = []
                camlist[x].append(results[i])
                x = x + 1
        # send camera list to check devices
        try:
            if camlist is not None:
                x = 1
                for i in range(len(camlist)):
                     deviceName = 'BlueIris Camera '+str(camlist[i][0]['optionDisplay'])
                     FoundDevice = False
                     for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                         if dev.name == deviceName:
                             self.logger.debug(u'Found BlueIris Camera Device Matching:'+unicode(deviceName))
                             FoundDevice = True
                             stateList = [
                                 {'key': 'ManRecLimit', 'value': camlist[i][0]['ManRecLimit']},
                                 {'key': 'FPS', 'value': camlist[i][0]['FPS']},
                                 {'key': 'color', 'value': camlist[i][0]['color']},
                                 {'key': 'nClips', 'value': camlist[i][0]['nClips']},
                                 {'key': 'nAlerts', 'value': camlist[i][0]['nAlerts']},
                                 {'key': 'height', 'value': camlist[i][0]['height']},
                                 {'key': 'active', 'value': camlist[i][0]['active']},
                                 {'key': 'isAlerting', 'value': camlist[i][0]['isAlerting']},
                                 {'key': 'ptz', 'value': camlist[i][0]['ptz']},
                                 {'key': 'isYellow', 'value': camlist[i][0]['isYellow']},
                                 {'key': 'isNoSignal', 'value': camlist[i][0]['isNoSignal']},
                                 {'key': 'lastalert', 'value': camlist[i][0]['lastalert']},
                                 {'key': 'isEnabled', 'value': camlist[i][0]['isEnabled']},
                                 {'key': 'nTriggers', 'value': camlist[i][0]['nTriggers']},
                                 {'key': 'width', 'value': camlist[i][0]['width']},
                                 {'key': 'alertutc', 'value': camlist[i][0]['alertutc']},
                                 {'key': 'hidden', 'value': camlist[i][0]['hidden']},
                                 {'key': 'type', 'value': camlist[i][0]['type']},
                                 {'key': 'profile', 'value': camlist[i][0]['profile']},
                                 {'key': 'isOnline', 'value': camlist[i][0]['isOnline']},
                                 {'key': 'isManRec', 'value': camlist[i][0]['isManRec']},
                                 {'key': 'isRecording', 'value': camlist[i][0]['isRecording']},
                                 {'key': 'pause', 'value': camlist[i][0]['pause']},
                                 {'key': 'optionDisplay', 'value': camlist[i][0]['optionDisplay']},
                                 {'key': 'webcast', 'value': camlist[i][0]['webcast']},
                                 {'key': 'optionValue', 'value': camlist[i][0]['optionValue']},
                                 {'key': 'isTriggered', 'value': camlist[i][0]['isTriggered']},
                                 {'key': 'isMotion', 'value': camlist[i][0]['isMotion']},
                                 {'key': 'newalerts', 'value': camlist[i][0]['newalerts']},
                                 {'key': 'isPaused', 'value': camlist[i][0]['isPaused']},
                                 {'key': 'error', 'value': camlist[i][0]['error']},
                                 {'key': 'audio', 'value': camlist[i][0]['audio']},
                                 {'key': 'nNoSignal', 'value': camlist[i][0]['nNoSignal']}
                             ]
                             dev.updateStatesOnServer(stateList)
                             if camlist[i][0]['isOnline'] == True and camlist[i][0]['isEnabled']:
                                 dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
                                 dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
                                 dev.updateStateOnServer('Motion', value=False )
                             else:
                                 dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
                                 dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                                 dev.updateStateOnServer('Motion', value=False, uiValue='Disabled')
                             update_time = t.strftime('%c')
                             dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))

                     if FoundDevice == False:
                         self.logger.info(u'No matching Camera Device Found - creating one:')
                         self.logger.info(unicode(deviceName)+'  created Device')
                         device = indigo.device.create(address=deviceName, deviceTypeId='BlueIrisCamera',name=deviceName,protocol=indigo.kProtocol.Plugin, folder='BlueIris')
                         self.sleep(0.2)
                         stateList = [
                             {'key': 'ManRecLimit', 'value': camlist[i][0]['ManRecLimit']},
                             {'key': 'FPS', 'value': camlist[i][0]['FPS']},
                             {'key': 'color', 'value': camlist[i][0]['color']},
                             {'key': 'nClips', 'value': camlist[i][0]['nClips']},
                             {'key': 'nAlerts', 'value': camlist[i][0]['nAlerts']},
                             {'key': 'height', 'value': camlist[i][0]['height']},
                             {'key': 'active', 'value': camlist[i][0]['active']},
                             {'key': 'isAlerting', 'value': camlist[i][0]['isAlerting']},
                             {'key': 'ptz', 'value': camlist[i][0]['ptz']},
                             {'key': 'isYellow', 'value': camlist[i][0]['isYellow']},
                             {'key': 'isNoSignal', 'value': camlist[i][0]['isNoSignal']},
                             {'key': 'lastalert', 'value': camlist[i][0]['lastalert']},
                             {'key': 'isEnabled', 'value': camlist[i][0]['isEnabled']},
                             {'key': 'nTriggers', 'value': camlist[i][0]['nTriggers']},
                             {'key': 'width', 'value': camlist[i][0]['width']},
                             {'key': 'alertutc', 'value': camlist[i][0]['alertutc']},
                             {'key': 'hidden', 'value': camlist[i][0]['hidden']},
                             {'key': 'type', 'value': camlist[i][0]['type']},
                             {'key': 'profile', 'value': camlist[i][0]['profile']},
                             {'key': 'isOnline', 'value': camlist[i][0]['isOnline']},
                             {'key': 'isManRec', 'value': camlist[i][0]['isManRec']},
                             {'key': 'isRecording', 'value': camlist[i][0]['isRecording']},
                             {'key': 'pause', 'value': camlist[i][0]['pause']},
                             {'key': 'optionDisplay', 'value': camlist[i][0]['optionDisplay']},
                             {'key': 'webcast', 'value': camlist[i][0]['webcast']},
                             {'key': 'optionValue', 'value': camlist[i][0]['optionValue']},
                             {'key': 'isTriggered', 'value': camlist[i][0]['isTriggered']},
                             {'key': 'isMotion', 'value': camlist[i][0]['isMotion']},
                             {'key': 'newalerts', 'value': camlist[i][0]['newalerts']},
                             {'key': 'isPaused', 'value': camlist[i][0]['isPaused']},
                             {'key': 'error', 'value': camlist[i][0]['error']},
                             {'key': 'audio', 'value': camlist[i][0]['audio']},
                             {'key': 'nNoSignal', 'value': camlist[i][0]['nNoSignal']}
                         ]
                         device.updateStatesOnServer(stateList)
                         if camlist[i][0]['isOnline']==True and camlist[i][0]['isEnabled']:
                            device.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
                            device.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
                            device.updateStateOnServer('Motion', value=False)
                         else:
                             device.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
                             device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                         update_time = t.strftime('%c')
                         device.updateStateOnServer('deviceLastUpdated', value=str(update_time))

                     #create motion variable in folder
                     self.createupdatevariable(str(camlist[i][0]['optionValue']).replace(' ',''), camlist[i][0]['isTriggered'])
                x=x+1
            #now fill with data
                self.sleep(0.1)

            self.logger.info(u'generate Cameras complete.')



        except:
            self.logger.exception('Exception in generate Cameras')


        return valuesDict



    def loginServer(self, valuesDict):
        self.logger.debug(u'loginServer Called.')

        #self.logger.debug(unicode(valuesDict))
        statusresults = self.sendccommand('status','')
        #result = statusresults['mem']
        #self.logger.info(unicode(result))
        # update BlueIris Server Device
        FoundDevice = False

        for dev in indigo.devices.itervalues('self.BlueIrisServer'):
            FoundDevice = True
        try:
            if FoundDevice == False:
            # Create New Server Device
                deviceName = 'Blue Iris Server Device'
                dev = indigo.device.create(address=deviceName, deviceTypeId='BlueIrisServer', name=deviceName,
                                              protocol=indigo.kProtocol.Plugin, folder='BlueIris')
                FoundDevice = True
        except:
            self.logger.exception(u'Exception creating Server Device')
            valuesDict['loginOK'] = False
            return

        if self.updateBIServerdevice(dev, statusresults):
            valuesDict['loginOK'] = True
        else:
            valuesDict['loginOK'] = False

        self.logger.info(u'Login to Server, Create BI Server Device Complete.')
        return valuesDict

    def updateStatus(self):
        self.logger.debug(u'Update Status called')

        statusresults = self.sendccommand('status', '')
        FoundDevice = False
        for dev in indigo.devices.itervalues('self.BlueIrisServer'):
            FoundDevice = True
            self.logger.debug(u'Found Device:'+unicode(dev.name))

        if FoundDevice==False:
            self.logger.error(u'Please use Plugin Config Settings to Login/Create Main BI server Device')
            return

        if self.updateBIServerdevice(dev, statusresults):
            self.logger.debug(u'Updated BI Server')
        else:
            self.logger.error(u'Failed to update BI Server Device')

        return


    def updateBIServerdevice(self, dev, statusresults):
        self.logger.debug(u' updateBIServerdevice called')

        try:
            #dev = indigo.devices[devId]
            stateList = [
                                 {'key': 'cxns', 'value': statusresults['cxns']},
                                 {'key': 'profile', 'value': statusresults['profile']},
                                 {'key': 'uptime', 'value': statusresults['uptime']},
                                 {'key': 'schedule', 'value': statusresults['schedule']},
                                 {'key': 'mem', 'value': statusresults['mem']},
                                 {'key': 'lock', 'value': statusresults['lock']},
                                 {'key': 'signal', 'value': statusresults['signal']},
                                 {'key': 'alerts', 'value': statusresults['alerts']},
                                 {'key': 'tzone', 'value': statusresults['tzone']},
                                 {'key': 'clips', 'value': statusresults['clips']},
                                 {'key': 'memload', 'value': statusresults['memload']},
                                 {'key': 'memfree', 'value': statusresults['memfree']},
                                 {'key': 'warnings', 'value': statusresults['warnings']},
                                 {'key': 'cpu', 'value': statusresults['cpu']}
            ]
            dev.updateStatesOnServer(stateList)
            update_time = t.strftime('%c')
            deviceState = str('Cpu :')+str(statusresults['cpu'])+'% MemFree :'+str(statusresults['memfree'])
            dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))
            dev.updateStateOnServer('deviceTimestamp', value=str(t.time()))
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
            dev.updateStateOnServer('deviceState', value=str(deviceState))
            return True
        except:
            self.logger.exception(u'Exception in updateBIServer Device')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Offline")
            return False


    def getCameraList(self):
        self.logger.debug(u'get CameraList called')
        camlist = {}
        results = self.sendccommand('camlist')

        x =0
        for i in range(len(results)):
            if 'ManRecLimit' in results[i]:
                camlist[x] = []
                camlist[x].append(results[i])
                x=x+1
        # send camera list to check devices
        self.checkCamDevices(camlist)

    def checkCamDevices(self, camlist):
        self.logger.debug(u'checkCamDevices Called')

        try:
            if camlist is not None:
                x = 1
                for i in range(len(camlist)):
                     deviceName = 'BlueIris Camera '+str(camlist[i][0]['optionDisplay'])
                     FoundDevice = False
                     for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                         if dev.name == deviceName:
                             self.logger.debug(u'Found BlueIris Camera Device Matching:')
                             FoundDevice = True
                             stateList = [
                                 {'key': 'ManRecLimit', 'value': camlist[i][0]['ManRecLimit']},
                                 {'key': 'FPS', 'value': camlist[i][0]['FPS']},
                                 {'key': 'color', 'value': camlist[i][0]['color']},
                                 {'key': 'nClips', 'value': camlist[i][0]['nClips']},
                                 {'key': 'nAlerts', 'value': camlist[i][0]['nAlerts']},
                                 {'key': 'height', 'value': camlist[i][0]['height']},
                                 {'key': 'active', 'value': camlist[i][0]['active']},
                                 {'key': 'isAlerting', 'value': camlist[i][0]['isAlerting']},
                                 {'key': 'ptz', 'value': camlist[i][0]['ptz']},
                                 {'key': 'isYellow', 'value': camlist[i][0]['isYellow']},
                                 {'key': 'isNoSignal', 'value': camlist[i][0]['isNoSignal']},
                                 {'key': 'lastalert', 'value': camlist[i][0]['lastalert']},
                                 {'key': 'isEnabled', 'value': camlist[i][0]['isEnabled']},
                                 {'key': 'nTriggers', 'value': camlist[i][0]['nTriggers']},
                                 {'key': 'width', 'value': camlist[i][0]['width']},
                                 {'key': 'alertutc', 'value': camlist[i][0]['alertutc']},
                                 {'key': 'hidden', 'value': camlist[i][0]['hidden']},
                                 {'key': 'type', 'value': camlist[i][0]['type']},
                                 {'key': 'profile', 'value': camlist[i][0]['profile']},
                                 {'key': 'isOnline', 'value': camlist[i][0]['isOnline']},
                                 {'key': 'isManRec', 'value': camlist[i][0]['isManRec']},
                                 {'key': 'isRecording', 'value': camlist[i][0]['isRecording']},
                                 {'key': 'pause', 'value': camlist[i][0]['pause']},
                                 {'key': 'optionDisplay', 'value': camlist[i][0]['optionDisplay']},
                                 {'key': 'webcast', 'value': camlist[i][0]['webcast']},
                                 {'key': 'optionValue', 'value': camlist[i][0]['optionValue']},
                                 {'key': 'isTriggered', 'value': camlist[i][0]['isTriggered']},
                                 {'key': 'isMotion', 'value': camlist[i][0]['isMotion']},
                                 {'key': 'newalerts', 'value': camlist[i][0]['newalerts']},
                                 {'key': 'isPaused', 'value': camlist[i][0]['isPaused']},
                                 {'key': 'error', 'value': camlist[i][0]['error']},
                                 {'key': 'audio', 'value': camlist[i][0]['audio']},
                                 {'key': 'nNoSignal', 'value': camlist[i][0]['nNoSignal']}
                             ]
                             dev.updateStatesOnServer(stateList)
                             if camlist[i][0]['isOnline'] == True and camlist[i][0]['isEnabled']:
                                 dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
                                 dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
                                 dev.updateStateOnServer('Motion', value=False )
                             else:
                                 dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
                                 dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                                 dev.updateStateOnServer('Motion', value=False, uiValue='Disabled')
                             update_time = t.strftime('%c')
                             dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))

                     if FoundDevice == False:
                         self.logger.debug(u'No matching Camera Device Found - Ignoring one..')
                         #self.logger.debug(unicode(deviceName)+'  created Device')
                         #device = indigo.device.create(address=deviceName, deviceTypeId='BlueIrisCamera',name=deviceName,protocol=indigo.kProtocol.Plugin, folder='BlueIris')
                         #self.sleep(2)
                     #create motion variable in folder
                     self.createupdatevariable(str(camlist[i][0]['optionValue']).replace(' ',''), camlist[i][0]['isTriggered'])
                x=x+1
            #now fill with data
                self.sleep(1)




        except:
            self.logger.exception('Exception in checkcamDevices')


    def sendccommand(self, cmd, params=dict()):

        self.logger.debug(u'sendcommand called')

        self.connectServer()  #this commands updates session key before command called


        if len(self.session)==0:
            self.logger.debug(u'No self.session cannot run command')
            return
        if len(self.response)<=0:
            self.logger.debug(u'No self.response cannot run command')
            return

        args = {"session": self.session, "response": self.response, "cmd": cmd}
        args.update(params)

        self.logger.debug('Command to be sent:'+unicode(args))

        # print self.url
        # print "Sending Data: "
        # print json.dumps(args)
        r = requests.post(self.url, data=json.dumps(args))

        if r.status_code != 200:
            self.logger.debug(u'Status code'+unicode(r.status_code) )
            self.logger.debug(u'Text :'+unicode(r.text))  #r.text
            self.logger.debug(u'Error Running command')
        else:
            pass
            self.logger.debug(u'SUCCESS Text :' + unicode(r.text))

        self.logger.debug( unicode(r.json()))

        try:
            return r.json()["data"]
        except:
            return r.json()


    def connectServer(self):

        self.logger.debug(u'connect Server started')
        try:
            self.url = "http://" + str(self.serverip) + ':'+str(self.serverport)+'/json'

            if self.debugextra:
                self.logger.debug(u'Attempting Connection to:'+unicode(self.url) )
            r = requests.post(self.url, data=json.dumps({"cmd": "login"}))
            if r.status_code != 200:
                if self.debugextra:
                    self.logger.debug( r.status_code)
                    self.logger.debug( r.text)
                return False
            if self.debugextra:
                self.logger.debug(u'Status code returned:'+unicode(r.status_code)+' Text result:'+unicode(r.text))
            self.session = r.json()["session"]

            if self.debugextra:
                self.logger.debug(u'Session returned:'+unicode(self.session))
            self.response = hashlib.md5("%s:%s:%s" % (self.serverusername, self.session, self.serverpassword)).hexdigest()

            if self.debugextra:
                self.logger.debug( "session: %s response: %s" % (self.session, self.response))

            r = requests.post(self.url,data=json.dumps({"cmd": "login", "session": self.session, "response": self.response}))

            if r.status_code != 200 or r.json()["result"] != "success":
                if self.debugextra:
                    self.logger.debug( r.status_code)
                    self.logger.debug( r.text)
                return False
            if self.debugextra:
                self.logger.debug(u'Session: Status code returned:' + unicode(r.status_code) + ' Text result:' + unicode(r.text))
            self.system_name = r.json()["data"]["system name"]
            self.profiles_list = r.json()["data"]["profiles"]
            if self.debugextra:
                self.logger.debug(u"Connected to '%s'" % self.system_name )
            return True
        except:
            self.logger.exception(u'Exception with connectServer:')
            return False

    def myProfiles(self, filter=0, valuesDict=None, typeId="", targetId=0):
        self.logger.debug(u'myProfiles called')
        # update profile list by calling server

        if self.connectServer():
            self.sleep(0.3)
            return self.profiles_list
        else:
            return 'Error Connecting','Error Connecting'



    def runConcurrentThread(self):

        try:
            while self.pluginIsShuttingDown == False:
                self.prefsUpdated = False
                self.sleep(0.5)
                updateCams = t.time() + 60
                updateServer = t.time() +10
                while self.prefsUpdated == False:
                #self.debugLog(u" ")
                    if t.time()>updateCams:
                        # update and create current blueIris Camera List
                        self.getCameraList()     # modifed to update Cameras
                        updateCams = t.time()+300
                    self.sleep(1)
                    if t.time()>updateServer:
                        self.updateStatus()
                        updateServer = t.time()+120

        except self.StopThread:
            self.logger.info(u'Restarting/or error. Stopping  thread.')
            pass

    def shutdown(self):

        self.debugLog(u"shutdown() method called.")
        self.pluginIsShuttingDown = True
        self.prefsUpdated = True

    def startup(self):

        self.debugLog(u"Starting Plugin. startup() method called.")



    def setStatestonil(self, dev):

        self.debugLog(u'setStates to nil run')


    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """

        self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin
        devices.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshData() method called.")

        try:
            # Check to see if there have been any devices created.
            if indigo.devices.itervalues(filter="self"):
                if self.debugLevel >= 2:
                    self.debugLog(u"Updating data...")

                for dev in indigo.devices.itervalues(filter="self"):
                    self.refreshDataForDev(dev)

            else:
                indigo.server.log(u"No Client devices have been created.")

            return True

        except Exception as error:
            self.errorLog(u"Error refreshing devices. Please check settings.")
            self.errorLog(unicode(error.message))
            return False

    def refreshDataForDev(self, dev):

        if dev.configured:
            if self.debugLevel >= 2:
                self.debugLog(u"Found configured device: {0}".format(dev.name))

            if dev.enabled:
                if self.debugLevel >= 2:
                    self.debugLog(u"   {0} is enabled.".format(dev.name))
                timeDifference = int(t.time() - t.mktime(dev.lastChanged.timetuple()))

            else:
                if self.debugLevel >= 2:
                    self.debugLog(u"    Disabled: {0}".format(dev.name))


    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected device based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDevAction() method called.")

        dev = indigo.devices[valuesDict.deviceId]

        self.refreshDataForDev(dev)
        return True

    def stopSleep(self, start_sleep):
        """
        The stopSleep() method accounts for changes to the user upload interval
        preference. The plugin checks every 2 seconds to see if the sleep
        interval should be updated.
        """
        try:
            total_sleep = float(self.pluginPrefs.get('configMenuUploadInterval', 300))
        except:
            total_sleep = iTimer  # TODO: Note variable iTimer is an unresolved reference.
        if t.time() - start_sleep > total_sleep:
            return True
        return False

    def toggleDebugEnabled(self):
        """ Toggle debug on/off. """


        self.logger.debug(u"toggleDebugEnabled() method called.")

        if self.debugLevel == int(logging.INFO):
            self.debug = True
            self.debugLevel = int(logging.DEBUG)
            self.pluginPrefs['showDebugInfo'] = True
            self.pluginPrefs['showDebugLevel'] = int(logging.DEBUG)
            self.logger.info(u"Debugging on.")
            self.logger.debug(u"Debug level: {0}".format(self.debugLevel))
            self.logLevel = int(logging.DEBUG)
            self.logger.debug(u"New logLevel = " + str(self.logLevel))
            self.indigo_log_handler.setLevel(self.logLevel)

        else:
            self.debug = False
            self.debugLevel = int(logging.INFO)
            self.pluginPrefs['showDebugInfo'] = False
            self.pluginPrefs['showDebugLevel'] = int(logging.INFO)
            self.logger.info(u"Debugging off.  Debug level: {0}".format(self.debugLevel))
            self.logLevel = int(logging.INFO)
            self.logger.debug(u"New logLevel = " + str(self.logLevel))
            self.indigo_log_handler.setLevel(self.logLevel)

###### Actions

    def ptzmain(self, camera, ptzargs):

        self.logger.debug(u'Ptz Main Called')

        self.sendccommand("ptz", {"camera": str(camera),"button": int(ptzargs),"updown": 0})
        return

    def ptzAction(self, valuesDict):
        self.logger.debug(u'ptzAction Called')
        #self.logger.debug(unicode(valuesDict))

        action = valuesDict.pluginTypeId
        actionevent = -1
        device = indigo.devices[valuesDict.deviceId]
        cameraname = device.states['optionValue']
        self.logger.debug(u'Action is:'+unicode(action))
        self.logger.debug(u'Camera is:'+unicode(cameraname))

        conditions = {
            'Left':0,
            'Right':1,
            'Up':2,
            'Down':3,
            'Home':4,
            'ZoomIn':5,
            'ZoomOut':6,
            'Hz50':8,
            'Hz60':9,
            'Outdoor':10,
            'B0':11,
            'B1':12,
            'B2': 13,
            'B3': 14,
            'B4': 15,
            'B5': 16,
            'B6': 17,
            'B7': 18,
            'B8': 19,
            'B9': 20,
            'B10': 21,
            'B11': 22,
            'B12': 23,
            'B13': 24,
            'B14': 25,
            'B15': 26,
            'C0': 27,
            'C1': 28,
            'C2': 29,
            'C3': 30,
            'C4': 31,
            'C5': 32,
            'C6': 33,
            'IRon': 34,
            'IRoff': 35
        }

        if action in conditions.keys():
            actionevent = conditions[action]
            self.logger.debug(u'Action Called =' + unicode(action) + u' action event:' + unicode(actionevent))
        else:
            self.logger.error(u'No such action event found: '+unicode(action))
        self.ptzmain(cameraname, actionevent)
        return

    def ptzPreset(self, valuesDict):
        self.logger.debug(u'ptzPreset Called')
        # self.logger.debug(unicode(valuesDict))

        #self.logger.info(unicode(valuesDict))
        action = valuesDict.pluginTypeId
        actionevent = int(valuesDict.props['presetnum'])

        device = indigo.devices[valuesDict.deviceId]
        cameraname = device.states['optionValue']
        self.logger.debug(u'Action is:' + unicode(action)+u' & Camera is:' + unicode(cameraname))

        self.ptzmain(cameraname, actionevent)
        return

    def triggerCam(self, valuesDict):
        self.logger.debug(u'triggerCam Called')
        # self.logger.debug(unicode(valuesDict))

        #self.logger.info(unicode(valuesDict))
        action = valuesDict.pluginTypeId
        #actionevent = int(valuesDict.props['presetnum'])

        device = indigo.devices[valuesDict.deviceId]
        cameraname = device.states['optionValue']
        self.logger.debug(u'Action is:' + unicode(action)+u' & Camera is:' + unicode(cameraname))

        self.sendccommand("trigger", {"camera": str(cameraname)})
        return

    def changeProfile(self, valuesDict):

        self.logger.debug(unicode(valuesDict))
        profileselected = str(valuesDict.props['targetProfile'])
        try:
            profile_id = self.profiles_list.index(profileselected)
            self.logger.debug(u'Selected Profile ID Equals:'+unicode(profile_id))
        except:
            self.logger.info(u'Could not find Profile with that name')
        self.logger.info(u'Setting BlueIris active Profile to: %s  (id: %d)' % (profileselected, profile_id))
        self.sendccommand("status", {"profile": profile_id})
        return

### subscribe variable changes

    def variableUpdated(self, origVariable, newVariable):

        folderId = indigo.variables.folders['BlueIris'].id
        #self.logger.info(u'Folder Id equals:'+unicode(folderId))
        #self.logger.debug(u'Variable Updated called..')
        if len(newVariable.value) < 3: return
        if origVariable.folderId != folderId:
            return
        if newVariable.value =='False':
            # Self triggered
            #self.logger.debug(u'Variable = False. Ignore.')
            return

        #self.logger.debug(u'original :'+unicode(origVariable)+' , new :'+unicode(newVariable))
        #self.logger.debug(u'Camera Triggered:'+unicode(origVariable.name))

        for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
            if dev.states['optionValue'] == origVariable.name:

                #  Should add check for true
                # trigger trigger for this dev camera &
                #
                self.logger.debug(u'Trigger Motion for this Camera:'+unicode(origVariable.name))
                dev.updateStateOnServer('Motion', value=True)
                dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
                self.sleep(0.5)
                # Only triggered if change - so quickly change back to False
                indigo.variable.updateValue(origVariable.id, 'False')

        return


