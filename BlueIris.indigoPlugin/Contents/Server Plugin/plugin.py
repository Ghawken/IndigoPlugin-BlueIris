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
import urllib
import os
import shutil

import subprocess
import threading

## Role together own httpserver
import string,cgi
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from urlparse import urlparse
from cgi import parse_qs

from ghpu import GitHubPluginUpdater

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
    u'updaterEmailsEnabled': False,  # Notification of plugin updates wanted.
    u'ServerTimeout': 5,
    u'ImageTimeout': 10
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.startingUp = True
        self.pathtoPlugin = os.getcwd()
        self.pathtoGifsicle = self.pathtoPlugin+'/gifsicle/1.91/bin/giflossy'
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False
        self.prefsUpdated = False
        self.system_name = ''
        self.oldlistenPort = 4556
        self.systemdata = None
        self.session =''

        self.ImageTimeout =10
        self.ServerTimeout = 5
        self.requestTimeout = self.ServerTimeout

        self.logger.info(u"")
        self.logger.info(u"{0:=^130}".format(" Initializing New Plugin Session "))
        self.logger.info(u"{0:<30} {1}".format("Plugin name:", pluginDisplayName))
        self.logger.info(u"{0:<30} {1}".format("Plugin version:", pluginVersion))
        self.logger.info(u"{0:<30} {1}".format("Plugin ID:", pluginId))
        self.logger.info(u"{0:<30} {1}".format("Indigo version:", indigo.server.version))
        self.logger.info(u"{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        self.logger.info(u"{0:<30} {1}".format("Install Path :", self.pathtoPlugin.replace('\n', '')))
        self.logger.info(u"{0:<30} {1}".format("Path to Gifsicle :", self.pathtoGifsicle.replace('\n', '')))
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

        self.pathtoPlugin = indigo.server.getInstallFolderPath()

        self.listenPort = 4556 #default
        # add callhere
        self.validatePrefsConfigUi(pluginPrefs)
        num =0
        try:
            for server in indigo.devices.itervalues('self.BlueIrisServer'):
                self.logger.debug(u'Found This Server Device:'+server.name)
                num=num+1
        except:
            self.logger.exception(u'Caught Error in Counting Server Devices...')
            pass

        if num >1:
            self.logger.error(u"{0:=^130}".format(""))
            self.logger.info(u"{0:=^130}".format(" You have more than one BlueIris Server Device.  Please Delete one and restart."))
            self.logger.error(u"{0:=^130}".format(""))

        # Choose Save Path

        MAChome = os.path.expanduser("~") + "/"
        folderLocation = MAChome + "Documents/Indigo-BlueIris/"
        self.saveDirectory = self.pluginPrefs.get('directory', '')

        self.logger.debug(u'Self.SaveDirectory equals:'+unicode(self.saveDirectory))

        if self.saveDirectory == '':
            self.saveDirectory = folderLocation
            self.logger.debug(u'Self.SaveDirectory changed:'+self.saveDirectory)
        try:
            if not os.path.exists(self.saveDirectory):
                os.makedirs(self.saveDirectory)
        except:
            self.logger.error(u'Error Accessing Save Directory.  Using Default:'+unicode(folderLocation))
            self.saveDirectory = folderLocation
            pass



        self.serverip = self.pluginPrefs.get('serverip', '')
        self.serverport = int(self.pluginPrefs.get('serverport', '80'))
        self.serverusername = self.pluginPrefs.get('serverusername', '')
        self.serverpassword = self.pluginPrefs.get('serverpassword', '')

        self.debugLevel = self.pluginPrefs.get('showDebugLevel', "20")
        self.debugextra = self.pluginPrefs.get('debugextra', False)
        self.debuggif = self.pluginPrefs.get('debuggif', False)
        self.debugserver = self.pluginPrefs.get('debugserver', False)
        self.debugimage = self.pluginPrefs.get('debugimage', False)
        self.debugtriggers = self.pluginPrefs.get('debugtriggers', False)
        self.debugother = self.pluginPrefs.get('debugother', False)


        # self.logger.info(unicode(self.pluginPrefs.get('Httpserverport','4556')))

        #self.listenPort = int(self.pluginPrefs.get('Httpserverport','4556'))
        # if self.listenPort is None:
        #     self.listenPort = 4556
        # elif self.listenPort == '':
        #     self.listenPort = 4556

        # self.listenPort = int(self.listenPort)

        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.configUpdaterInterval = self.pluginPrefs.get('configUpdaterInterval', 24)

        #self.configUpdaterForceUpdate = self.pluginPrefs.get('configUpdaterForceUpdate', False)

        self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "24")) * 60.0 * 60.0
        self.next_update_check = t.time() + 20

        if 'BlueIris' not in indigo.variables.folders:
            indigo.variables.folder.create('BlueIris')
        self.folderId = indigo.variables.folders['BlueIris'].id


        self.pluginIsInitializing = False



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

            #self.logger.error(unicode(valuesDict))

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
            self.debugserver = valuesDict.get('debugserver', False)
            self.debugimage = valuesDict.get('debugimage', False)
            self.debuggif = valuesDict.get('debuggif', False)
            self.debugtriggers = valuesDict.get('debugtriggers', False)
            self.debugother = valuesDict.get('debugother', False)
            self.openStore = valuesDict.get('openStore', False)
            self.saveDirectory = valuesDict.get('directory', '')

            # self.ImageTimeout = int(valuesDict.get('ImageTimout',5))
            # self.ServerTimeout = int(valuesDict.get('ServerTimeout'),5)

            #oldlistenport = self.listenPort

            self.listenPort = int(valuesDict.get('Httpserverport', '4556'))

            if self.listenPort != self.oldlistenPort:
                self.logger.error(u"{0:=^130}".format(""))
                self.logger.error(u'After Changing Port need to Restart Plugin.  Restarting Now.....')
                self.logger.error(u"{0:=^130}".format(""))
                self.restartPlugin()
                return False

            self.oldlistenPort = self.listenPort

            self.updateFrequency = float(valuesDict.get('updateFrequency', "24")) * 60.0 * 60.0

            # Attempt to connnect to BlueIris and get sesion
            if self.connectServer():
                self.logger.debug(u'Connection established to Blueiris Server:'+unicode(self.system_name))
            else:
                self.logger.info(u'Cannot connect to Blue Iris Server.  Check Username/Password/Server Details')
                return False
        return True

    def validateDeviceConfigUi(self, valuesDict, typeID, devId):
        self.logger.debug(u'validateDeviceConfigUi Called')
        errorDict = indigo.Dict()

        try:
            if typeID=='BlueIrisCamera':
                if valuesDict['animateGif']:
                    giftime = int(valuesDict['giftime'])
                    if giftime > int(60):
                        errorDict['giftime'] ='Probably a little long.  Try less than 60 seconds'
                        return (False, valuesDict, errorDict)
                    giflossy = int(valuesDict['gifcompression'])
                    if giflossy <=20 or giflossy >200:
                        errorDict['gifcompression']='To high or low for compression try again'
                        return (False, valuesDict, errorDict)
                if valuesDict['animateGif'] and valuesDict['saveimage']== False:
                    errorDict['animateGif']= 'Need to also enabled Save Images above for this to work'
                    return (False, valuesDict, errorDict)

            return (True, valuesDict, errorDict)

        except ValueError:
            self.logger.debug(u'Error in Validate')
            return (False, valuesDict, errorDict)
        except:
            self.logger.exception(u'Caught Error in Device Validate')
            return (False, valuesDict, errorDict)


    def validatePrefsConfigUi(self, valuesDict):
        """ docstring placeholder """
        self.logger.debug(u"------ validatePrefsConfigUi() method called.")
        errorDict = indigo.Dict()

        #self.logger.info(unicode(valuesDict))

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
        else:
            return False, valuesDict


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
        else:
            return False, valuesDict


        if 'Httpserverport' in valuesDict:
            try:
                self.oldlistenPort = self.listenPort
                #self.logger.debug(u'Old listenPort is :' + unicode(self.oldlistenPort))
                self.listenPort = int(valuesDict['Httpserverport'])
            except:
                #self.logger.exception(u'Httpserverport Error')
                self.listenPort = 4556
                self.pluginPrefs['Httpserverport'] = 4556
                errorDict['Httpserverport']='Please enter valid Port Number'
                errorDict['showAlertText']='The field is invalid as it is not an integer'
                return (False, valuesDict, errorDict)
        else:
            #self.logger.error(u'No httpServerport in valuesDict Why')
            self.listenPort = 4556
            self.pluginPrefs['Httpserverport'] = 4556

        self.logger.debug(u'Checking Timeouts...')
        if valuesDict.get('ServerTimeout',"") == "":
            valuesDict['ServerTimeout'] = 5
            self.pluginPrefs['ServerTimeout'] = 5
            self.logger.debug(u'Setting ServerTimeout to Default 5 as Blank')

        if valuesDict.get('ImageTimeout', "") == "":
            valuesDict['ImageTimeout'] = 10
            self.pluginPrefs['ImageTimeout'] = 10
            self.logger.debug(u'Setting ImageTimeout to Default 10 as blank')

        if 'ImageTimeout' in valuesDict:
            self.logger.debug(u'ImageTimeout:'+unicode(valuesDict['ImageTimeout']))
            try:
                self.ImageTimeout = int(valuesDict['ImageTimeout'])
                if self.ImageTimeout <=0:
                    self.ImageTimeout = 10
                    valuesDict[u'ImageTimeout'] = 10
                    self.pluginPrefs[u'ImageTimeout'] = 10
                self.logger.debug(u'Setting ImageTimeout to '+unicode(valuesDict['ImageTimeout']))
            except:
                self.logger.exception(u'Exception ImageTimeout')
                valuesDict[u'ImageTimeout'] = 10
                self.pluginPrefs[u'ImageTimeout'] = 10
                self.logger.debug(u'Setting to Default ImageTimout of 5 seconds')
                self.ImageTimeout = 10

        if 'ServerTimeout' in valuesDict:
            self.logger.debug(u'ServerTimeOut:'+unicode(valuesDict['ServerTimeout']))
            try:
                self.ServerTimeout = valuesDict['ServerTimeout']
                if self.ServerTimeout <=0:
                    self.ServerTimeout = 5
                    valuesDict[u'ServerTimeout'] = 5
                    self.pluginPrefs[u'ServerTimeout'] = 5
                self.logger.debug(u'Setting ServerTimeout to ' + unicode(valuesDict['ServerTimeout']))
                self.logger.debug(u'Self ServerTimeout  :'+unicode(self.ServerTimeout))
            except:
                self.logger.exception(u'Server Timeout exception:')
                valuesDict[u'ServerTimeout'] = 5
                self.pluginPrefs[u'ServerTimeout'] = 5
                self.logger.debug(u'Setting to Default ServerTimeout of 5 seconds')
                self.ServerTimeout = 5

        if valuesDict.get('directory', '') != '':
            # check read/write access to directory
            if os.access(valuesDict['directory'],os.W_OK) == False:
                errorDict['directory']='No write Access to this location.'
                errorDict['shwoAlertText']='Error.  Cannot write to this location'
                self.logger.debug(u'DiskAccessError:  Cannot Read/Write to this location')
                return (False, valuesDict, errorDict)
            else:
                self.logger.debug(u'DiskAcces:  All Good.  Can Read/Write to this location')
        if valuesDict.get('directory','') == '':
            MAChome = os.path.expanduser("~") + "/"
            folderLocation = MAChome + "Documents/Indigo-BlueIris/"
            valuesDict['directory'] = folderLocation
            self.pluginPrefs['directory'] = folderLocation



        if 'serverip' in valuesDict and 'serverport' in valuesDict and 'serverusername' in valuesDict  and 'serverpassword' in valuesDict and 'Httpserverport' in valuesDict:
            # Validate login
            return True, valuesDict
        else:
            errorDict['showAlertText']='Missing some Plugin Configuration Settings Please review'
            return (False, valuesDict, errorDict)



        return True, valuesDict

    def restartPlugin(self):
        self.logger.debug(u"Restarting the  Plugin Called.")
        plugin = indigo.server.getPlugin('com.GlennNZ.indigoplugin.BlueIris')
        if plugin.isEnabled():
            plugin.restart(waitUntilDone=False)


    # Start 'em up.
    def deviceStartComm(self, dev):

        self.logger.debug(u"deviceStartComm() method called.")
        dev.stateListOrDisplayStateIdChanged()
        if dev.deviceTypeId == 'BlueIrisCamera':
            try:
            # Update extra settings so can check elsewhere
                cameraprops = dev.pluginProps
                #self.logger.info(unicode(cameraprops))
                if 'animateGif' not in cameraprops:
                    cameraprops.update({'animateGif': False })
                if 'gifcompression' not in cameraprops:
                    cameraprops.update({'gifcompression':150})
                if 'giftime' not in cameraprops:
                    cameraprops.update({'giftime':10 })
                if 'saveimage' not in cameraprops:
                    cameraprops.update({'saveimage':False})
                if 'widthimage' not in cameraprops:
                    cameraprops.update({'widthimage':1920})
                if 'gifwidth' not in cameraprops:
                    cameraprops.update({'gifwidth':800})
                dev.replacePluginPropsOnServer(cameraprops)
            except:
                self.logger.debug(u'pluginProps exception being passed')
                pass
            dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
            dev.updateStateOnServer('Motion', value=False, uiValue='False')
            dev.updateStateOnServer('deviceIsOnline', value=True )
            #self.createupdatevariable(dev.states['optionValue'], 'False')
            stateList = [
                {'key': 'MotionDetection', 'value': None, 'uiValue': 'Unknown'},
                {'key': 'PtzCycle', 'value': None, 'uiValue': 'Unknown'},
                {'key': 'CameraPaused', 'value': 'unknown', 'uiValue': 'Unknown'},
                {'key': 'PluginTriggeringEnabled', 'value': True}
            ]
            dev.updateStatesOnServer(stateList)


    def createupdatevariable(self, variable, result):

        if self.debugextra:
            self.logger.debug(u'createupdate variable called.')

        # if 'BlueIris' not in indigo.variables.folders:
        #     indigo.variables.folder.create('BlueIris')

        if variable not in indigo.variables:
            indigo.variable.create(variable, str(result), folder='BlueIris')
            return
        else:
            indigo.variable.updateValue(str(variable), str(result))
        return

    # Shut 'em down.

    def deviceStopComm(self, dev):

        self.logger.debug(u"deviceStopComm() method called.")
        #indigo.server.log(u"Stopping device: " + dev.name)
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")

        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
        if dev.deviceTypeId == 'BlueIrisCamera':
            dev.updateStateOnServer('Motion', value=False, uiValue='Disabled')


    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    def generateCameras(self, valuesDict):
        if self.debugextra:
            self.logger.debug(u'generate Cameras called')
        # Generate Cameras - main check will not create cameras if deleted

        camlist = {}
        results = self.sendccommand('camlist')

        if results is None:
            self.logger.error(u'Cannot create Cameras.  ?Login/Server details correct')
            return

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
                             if self.debugextra:
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
                                 dev.updateStateOnServer('Motion', value=False , uiValue='False')
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
                            device.updateStateOnServer('Motion', value=False, uiValue='')
                         else:
                             device.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
                             device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                         update_time = t.strftime('%c')
                         device.updateStateOnServer('deviceLastUpdated', value=str(update_time))

                     #create motion variable in folder
                     #self.createupdatevariable(str(camlist[i][0]['optionValue']).replace(' ',''), camlist[i][0]['isTriggered'])
                x=x+1
            #now fill with data
                self.sleep(0.1)

            self.logger.info(u'generate Cameras complete.')



        except:
            self.logger.exception(u'Caught Exception in generate Cameras')


        return valuesDict



    def loginServer(self, valuesDict):
        if self.debugextra:
            self.logger.debug(u'loginServer Called.')

        #self.logger.debug(unicode(valuesDict))
        statusresults = self.sendccommand('status','')
        #result = statusresults['mem']
        #self.logger.info(unicode(statusresults))

        if statusresults is None:
            self.logger.info(u'Cannot login to BI Server.  Are details correct?')
            return

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
            self.logger.exception(u'Caught Exception creating Server Device')
            valuesDict['loginOK'] = False
            return

        if self.updateBIServerdevice(dev, statusresults):
            valuesDict['loginOK'] = True
        else:
            valuesDict['loginOK'] = False

        self.logger.info(u'Login to Server, Create BI Server Device Complete.')
        return valuesDict

    def updateStatus(self):

        try:
            if self.debugextra:
                self.logger.debug(u'Update Status called')

            statusresults = self.sendccommand('status', '')

            FoundDevice = False
            for dev in indigo.devices.itervalues('self.BlueIrisServer'):
                FoundDevice = True
                if self.debugextra:
                    self.logger.debug(u'Found Device:'+unicode(dev.name))
            if FoundDevice==False:
                self.logger.error(u'Please use Plugin Config Settings to Login/Create Main BI server Device')
                return
            if statusresults is None:
                self.logger.info(u'No result from status enquiry. If repeated please check Login Server Details in Plugin Config')
                return

            # add check for fail
            if 'result' in statusresults:
                if statusresults['result']=='fail':
                    self.logger.debug(u'Failed info from Update Status.  Ending.')
                    return

           #login self.logger.info(unicode(statusresults  ))
            if self.updateBIServerdevice(dev, statusresults):
                if self.debugextra:
                    self.logger.debug(u'Updated BI Server')
            else:
                self.logger.error(u'Failed to update BI Server Device')
        except:
            self.logger.debug(u'Exception in update Status/Update BI Server caught')
        return


    def updateBIServerdevice(self, dev, statusresults):


        try:
            if self.debugextra:
                self.logger.debug(u' updateBIServerdevice called')

            disktotal = None
            diskallocated = None
            diskname = 'Unknown'
            diskfree = None
            diskused = None

            disks = next(iter(statusresults['disks']), None)

            if disks is not None:
                if self.debugextra:
                    self.logger.debug(u'Disks:'+unicode(disks))
                if 'total' in disks:
                    disktotal =  disks['total']
                if 'allocated' in disks:
                    diskallocated = disks['allocated']
                if 'free' in disks:
                    diskfree = disks['free']
                if 'used' in disks:
                    diskused = disks['used']
                if 'disk' in disks:
                    diskname = disks['disk']
        except:
            if self.debugextra:
                self.logger.exception(u'Caught Exception in updateBIServer Device:  Disk Error')
            pass

        try:
            #dev = indigo.devices[devId]

            # add checks from memfree versus mem - which is a v4 and v5 difference
            memFree = '_';
            if 'mem' in statusresults:
                memFree = statusresults['mem']
            elif 'memfree' in statusresults:
                memFree = statusresults['memFree']

            stateList = [
                                 {'key': 'cxns', 'value': statusresults['cxns']},
                                 {'key': 'profile', 'value': statusresults['profile']},
                                 {'key': 'uptime', 'value': statusresults['uptime']},
                                 {'key': 'schedule', 'value': statusresults['schedule']},
                                 {'key': 'mem', 'value': memFree},
                                 {'key': 'lock', 'value': statusresults['lock']},
                                 {'key': 'signal', 'value': statusresults['signal']},
                                 {'key': 'alerts', 'value': statusresults['alerts']},
                                 {'key': 'tzone', 'value': statusresults['tzone']},
                                 {'key': 'clips', 'value': statusresults['clips']},
                                 {'key': 'memload', 'value': statusresults['memload']},
                                 {'key': 'memfree', 'value': statusresults['mem']},
                                 {'key': 'warnings', 'value': statusresults['warnings']},
                                 {'key': 'cpu', 'value': statusresults['cpu']},
                                 {'key': 'clipsInfo', 'value': str(statusresults['clips'])},
                                 {'key': 'disktotal', 'value': disktotal},
                                 {'key': 'diskallocated', 'value': diskallocated},
                                 {'key': 'diskname', 'value': diskname},
                                 {'key': 'diskfree', 'value': diskfree},
                                 {'key': 'diskused', 'value': diskused}
            ]
            dev.updateStatesOnServer(stateList)
            update_time = t.strftime('%c')


            deviceState = str('Cpu :')+str(statusresults['cpu'])+'% MemFree :'+str(memFree)

            dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))
            dev.updateStateOnServer('deviceTimestamp', value=str(t.time()))
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
            dev.updateStateOnServer('deviceState', value=str(deviceState))
            return True

        except:
            self.logger.exception(u'Caught Exception in updateBIServer Device')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Offline")
            return False


    def getCameraList(self):
        if self.debugextra:
            self.logger.debug(u'get CameraList called')

        try:
            camlist = {}
            results = self.sendccommand('camlist')

            if results is None:
                self.logger.debug(u'No Cameras found, or a connection issue.  Please create from within Plugin Config.')
                return

            #add check here
            if 'result' in results:
                if results['result']=='fail':
                    self.logger.debug(u'Failed to get Camera List.  No data provided by BI.')
                    return

            if len(results)<=0:
                self.logger.debug(u'No Cameras found.2.  Please create from within Plugin Config.')
                return
            x =0
            for i in range(len(results)):
                if 'ManRecLimit' in results[i]:
                    camlist[x] = []
                    camlist[x].append(results[i])
                    x=x+1
            # send camera list to check devices
            self.checkCamDevices(camlist)
        except:
            if self.debugextra:
                self.logger.exception(u'Caught Exception in getCameraList:')
                self.logger.exception(unicode(results))


    def updateSystemDevice(self):
        if self.debugextra:
            self.logger.debug(u'updateSystemDevice Called')

        try:
            if self.systemdata is not None:
                for dev in indigo.devices.itervalues('self.BlueIrisServer'):
                    if dev.enabled:
                        streamslist = '|'.join(self.systemdata['streams'])
                        stateList = [
                                {'key': 'systemName', 'value': self.systemdata['system name'] },
                                {'key': 'admin', 'value': self.systemdata['admin']},
                                {'key': 'audio', 'value': self.systemdata['audio']},
                                {'key': 'clips', 'value': self.systemdata['clips']},
                                {'key': 'user', 'value': self.systemdata['user']},
                                {'key': 'latitude', 'value': self.systemdata['latitude']},
                                {'key': 'longitude', 'value': self.systemdata['longitude']},
                                {'key': 'version', 'value': self.systemdata['version']},
                                {'key': 'streams', 'value': streamslist }
                            ]
                        dev.updateStatesOnServer(stateList)
                        if self.debugextra:
                            self.logger.debug(u'updateSystemDevice Updated/Done.')

        except:
            self.logger.exception(u'Caught Exception within UpdateSystemDevice')
        return

    def camconfigUpdateData(self, configdata, camera):
        if self.debugextra:
            self.logger.debug(u'camConfig Update Data Called.')
        try:
            if camera.enabled :
                cameraname = camera.states['optionValue']
                if self.debugother:
                    self.logger.debug(u'Attempting to Update CamConfig for Camera:' + cameraname)
                #cameraconfigdata = self.sendccommand('camconfig', {'camera': str(cameraname)})
                    self.logger.debug(u'ConfigData:'+unicode(configdata))
                # Below - command only returns data if successful if not reason etc why
                # so if a 'result' key in the data returned - it has not been successful.
                if configdata is not None and 'result' not in configdata:
                    stateList = [
                    {'key': 'MotionDetection', 'value': configdata['motion']},
                    {'key': 'PtzCycle', 'value': configdata['ptzcycle']},
                    {'key': 'CameraPaused', 'value': configdata['pause']}
                ]
                    self.logger.debug(u'Sucessfully updated Camera:'+unicode(cameraname))
                    camera.updateStatesOnServer(stateList)
                else:
                    self.logger.debug(u'CamConfig Update Data Failed. Most likely no longer admin user.')
                    return
        except:
            self.logger.exception(u'Caught Exception in Update CamConfig Update Data Exception')
            return

    def updatecamConfig(self):

        # call CamConfig for each Camera to get Motion Detection Details
        # Can't Hammer it otherwise timesout.

        if self.debugextra:
            self.logger.debug(u'updateCamConfig Called')
        try:
            if self.checkadminuser():
                for camera in indigo.devices.itervalues('self.BlueIrisCamera'):
                    if camera.enabled:
                        cameraname = camera.states['optionValue']
                        if self.debugother:
                            self.logger.debug(u'Checking CamConfig for Camera:' + cameraname)

                        cameraconfigdata = self.sendccommand('camconfig', {'camera': str(cameraname) })
                        #self.logger.info(unicode(cameraconfigdata))
                        if cameraconfigdata is not None and 'result' not in cameraconfigdata:
                        #if cameraconfigdata is not None :
                            stateList = [
                                        {'key': 'MotionDetection', 'value': cameraconfigdata['motion'] },
                                        {'key': 'PtzCycle', 'value': cameraconfigdata['ptzcycle']},
                                        {'key': 'CameraPaused', 'value': cameraconfigdata['pause']}
                                        ]
                            if self.debugother:
                                self.logger.debug(u'Updated Camera with new States:'+unicode(stateList))
                            camera.updateStatesOnServer(stateList)
                        self.sleep(1)
            else:
                if self.debugextra:
                    self.logger.debug(u'Need to be Admin BI User to access these addtional states')
                for camera in indigo.devices.itervalues('self.BlueIrisCamera'):
                    #self.logger.error(u'Camera States MD are:'+unicode(camera.states['MotionDetection']))

                    if camera.enabled and camera.states['MotionDetection'] != '':
                        cameraname = camera.states['optionValue']
                        if self.debugother:
                            self.logger.debug(u'Removing CamConfig for Camera, as Not Admin User.  Camera:' + cameraname)
                        stateList = [
                                        {'key': 'MotionDetection', 'value': None, 'uiValue':'Unknown' },
                                        {'key': 'PtzCycle', 'value':None, 'uiValue': 'Unknown'},
                                        {'key': 'CameraPaused', 'value': 'unknown', 'uiValue': 'Unknown'}
                                    ]
                        camera.updateStatesOnServer(stateList)
                return
        except:
            self.logger.debug(u'Exception within updateCamConfig:')
            if self.debugextra:
                self.logger.exception(u'Caught Exception:')
            self.logger.debug(u'Most likely to many calls to quickly.')
            return


    def checkCamDevices(self, camlist):
        if self.debugextra:
            self.logger.debug(u'checkCamDevices Called')

        try:
            if camlist is not None:
                x = 1
                for i in range(len(camlist)):
                     deviceName = 'BlueIris Camera '+str(camlist[i][0]['optionDisplay'])
                     FoundDevice = False
                     for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                         if dev.name == deviceName:
                             if self.debugextra:
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
                                 dev.updateStateOnServer('Motion', value=False, uiValue='False' )
                             else:
                                 dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
                                 dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                                 dev.updateStateOnServer('Motion', value=False, uiValue='Disabled')
                             update_time = t.strftime('%c')
                             dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))

                     if FoundDevice == False:
                         if self.debugextra:
                            self.logger.debug(u'No matching Camera Device Found - Ignoring one..')
                         #self.logger.debug(unicode(deviceName)+'  created Device')
                         #device = indigo.device.create(address=deviceName, deviceTypeId='BlueIrisCamera',name=deviceName,protocol=indigo.kProtocol.Plugin, folder='BlueIris')
                         #self.sleep(2)
                     #create motion variable in folder
                     #self.createupdatevariable(str(camlist[i][0]['optionValue']).replace(' ',''), camlist[i][0]['isTriggered'])
                x=x+1
            #now fill with data
                self.sleep(1)
        except:
            self.logger.exception(u'Caught Exception in checkcamDevices')


    def sendccommand(self, cmd, params=dict()):

        try:
            self.url = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/json'
            if self.debugextra:
                self.logger.debug(u'sendcommand called')
                self.logger.debug(u'cmd ='+unicode(cmd)+' params='+unicode(params))
            if self.connectServer():  #this commands updates session key before command called
                if self.debugextra:
                    self.logger.debug(u'Connection to Server Complete')
            else:
                self.logger.debug(u'Failed connection to server.')
                return

            if len(self.session)==0:
                self.logger.debug(u'No self.session cannot run command')
                return
            if len(self.response)<=0:
                self.logger.debug(u'No self.response cannot run command')
                return
            args = {"session": self.session, "response": self.response, "cmd": cmd}

            if cmd=='status' and 'macro' not in params:
                args = {"session": self.session, "cmd": cmd}

            args.update(params)
            if self.debugextra:
                self.logger.debug('Command to be sent:'+unicode(args))

            r = requests.post(self.url, data=json.dumps(args), timeout=self.ServerTimeout)

            if r.status_code != 200:
                self.logger.debug(u'Status code'+unicode(r.status_code) )
                self.logger.debug(u'Text :'+unicode(r.text))  #r.text
                self.logger.debug(u'Error Running command')
                return ''
            else:
                if self.debugextra:
                    self.logger.debug(u'SUCCESS Text :' + unicode(r.text))

            if self.debugextra:
                self.logger.debug(u'sendcommand r.json result:')# + unicode(r.json()  )   )

            try:
                return r.json()["data"]
            except:
                return r.json()

        except requests.exceptions.Timeout:
            self.logger.debug(u'sendCommand has timed out and cannot connect to BI Server.')
            self.sleep(5)
            pass
        except requests.exceptions.ConnectionError:
            self.logger.debug(u'sendCommand has ConnectionError and cannot connect to BI Server.')
            self.sleep(5)
            pass


        except:
            self.logger.exception(u'Caught Exception within Send Command')


    def connectServer(self):

        if self.debugextra:
            self.logger.debug(u'connect Server started')
        try:
            self.url = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/json'
            if self.debugextra:
                self.logger.debug(u'Attempting Connection to:'+unicode(self.url) )
            r = requests.post(self.url, data=json.dumps({"cmd": "login"}), timeout=self.ServerTimeout)
            if int(r.status_code) != 200:
                if self.debugextra:
                    self.logger.debug(u'!200 return:  R.status Code equals:'+ unicode(r.status_code))
                    self.logger.debug(u' and r.text:'+unicode(r.text))
                return False

            if r.json() is None:
                if self.debugextra:
                    self.logger.debug(u'Nothing returned from BI')
                    self.logger.debug(unicode(r.text))
                    self.logger.debug(u'Connected.  But nothing returned from BI')
                    return False

            if self.debugextra:
                self.logger.debug(u'Status code returned:'+unicode(r.status_code)+' Text result:'+unicode(r.text))
            if 'session' in r.json():
                self.session = r.json()["session"]
            else:
                self.logger.info(u'Connection to BI Server denied.  Reason:'+unicode(r.json()['data']['reason']))
                return False

            if self.debugextra:
                self.logger.debug(u'Session returned:'+unicode(self.session))
            self.response = hashlib.md5("%s:%s:%s" % (self.serverusername, self.session, self.serverpassword)).hexdigest()

            if self.debugextra:
                self.logger.debug( "session: %s response: %s" % (self.session, self.response))

            r = requests.post(self.url,data=json.dumps({"cmd": "login", "session": self.session, "response": self.response}), timeout=self.ServerTimeout)
            if int(r.status_code) != 200 or r.json()["result"] != "success":
                if self.debugextra:
                    self.logger.debug(u'!200 return:  R.status Code equals:' + unicode(r.status_code))
                    self.logger.debug(u' and r.text:' + unicode(r.text))
                return False

            if self.debugextra:
                self.logger.debug(u'Session: Status code returned:' + unicode(r.status_code) + ' Text result:' + unicode(r.text))
            self.systemdata = r.json()['data']
            self.system_name = r.json()["data"]["system name"]
            self.profiles_list = r.json()["data"]["profiles"]
            if self.debugextra:
                self.logger.debug(u"Connected to '%s'" % self.system_name )
            return True
        except requests.exceptions.Timeout:
            self.logger.debug(u'connectServer has timed out and cannot connect to BI Server.')
            pass

        except requests.exceptions.ConnectionError:
            self.logger.debug(u'connectServer has a Connection Error and cannot connect to BI Server.')
            self.sleep(10)
            pass

        except:
            self.logger.exception(u'Caught Exception with connectServer:')
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
                updateCams = t.time() + 5
                updateServer = t.time() +2
                while self.prefsUpdated == False:
                #self.debugLog(u" ")
                    if self.updateFrequency > 0:
                        if t.time() > self.next_update_check:
                            try:
                                self.checkForUpdates()
                                self.next_update_check = t.time() + self.updateFrequency
                            except:
                                self.logger.debug(
                                u'Error checking for update - ? No Internet connection.  Checking again in 24 hours')
                                self.next_update_check = t.time() + 86400;


                    if t.time()>updateCams:
                        # update and create current blueIris Camera List
                        self.getCameraList()     # modifed to update Cameras
                        updateCams = t.time()+300
                        self.sleep(0.2)
                        self.updatecamConfig()
                    self.sleep(1)
                    if t.time()>updateServer:
                        self.updateStatus()
                        self.sleep(0.2)
                        updateServer = t.time()+120
                        self.updateSystemDevice()

        except self.StopThread:
            self.logger.info(u'Restarting/or error. Stopping  thread.')
            pass

    def shutdown(self):

        self.logger.debug(u"shutdown() method called.")
        self.pluginIsShuttingDown = True
        self.prefsUpdated = True

    def startup(self):

        self.logger.debug(u"Starting Plugin. startup() method called.")


        # MAChome = os.path.expanduser("~") + "/"
        # folderLocation = MAChome + "Documents/Indigo-BlueIris/"
        # if not os.path.exists(folderLocation):
        #     os.makedirs(folderLocation)
        # folderLocation = self.saveDirectory

        self.updater = GitHubPluginUpdater(self)
        try:
            self.logger.debug(u'Creating Directories and deleting files..')
            for dev in indigo.devices.iter('self.BlueIrisCamera'):
                cameraname = dev.states['optionValue']
                folderLocation = self.saveDirectory + str(cameraname) + '/'

                if not os.path.exists(folderLocation):
                    os.makedirs(folderLocation)
                if os.path.exists(folderLocation+'tmp'):
                    shutil.rmtree(folderLocation+'tmp')
                    self.sleep(0.2)
                    os.makedirs(folderLocation + 'tmp')
                else:
                    os.makedirs(folderLocation + 'tmp')

        except:
            self.logger.exception(u'Caught Exception at Startup :')
            pass


## Start Http Server at Startup
        self.myThread = threading.Thread(target=self.listenHTTP, args=())
        self.myThread.daemon = True
        self.myThread.start()


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


    def checkadminuser(self):
        if self.debugextra:
            self.logger.debug(u'check Admin User called')
        try:
            admin = False
            for dev in indigo.devices.itervalues('self.BlueIrisServer'):
                if dev.enabled:
                    if bool(dev.states['admin']):
                        if self.debugextra:
                            self.logger.debug(u'Check Admin User: Admin User Found.')
                        return True
            if admin == False:
                self.logger.debug(u'BlueIris Server User is not Admin.')
                return False
        except:
            self.logger.exception(u'Caught Exception in Checkadmin User')
            return False
###### Actions

    def camconfig(self,valuesDict):

        try:
            self.logger.debug(u'CamConfig Called: args'+unicode(valuesDict))

            if self.checkadminuser() == False:
                self.logger.info(u'BlueIris Server User is not admin these commands will not work.')
                return

            device = indigo.devices[valuesDict.deviceId]
            cameraname = device.states['optionValue']
            #self.logger.info(unicode(valuesDict))
            action = str(valuesDict.props['Configargs'])
            #split to get two arguments to send
            conditions = action.split(':')

            if conditions[1]=='False':
                argtouse = False
            elif conditions[1] =='True':
                argtouse =True
            else:
                argtouse = conditions[1]

            self.logger.debug(u'Action ArgtoUse:'+unicode(argtouse))
            self.logger.debug(u'Action Called =' + unicode(action) + u' action event:' + unicode(conditions))

            configdata = self.sendccommand('camconfig', {'camera': str(cameraname), conditions[0]:argtouse })
            # if command set update camera now with data received
            self.camconfigUpdateData(configdata, device)
            #self.sendccommand('camconfig', {'camera': str(cameraname), 'motion': False})
        except:
            self.logger.exception(u'Caught Exception within Cam Config')
        return

    def actionEnableAnim(self, valuesDict):
        self.logger.debug(u'action Enable Anim called')
        try:

            action = valuesDict.pluginTypeId
            actionevent = valuesDict.props['setting']
            cameras = valuesDict.props['deviceCamera']
            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if str(dev.id) in cameras:
                    #self.logger.debug(u'Action is:' + unicode(action) + u' & Camera is:' + unicode(dev.name)+u' and action:'+unicode(actionevent))
                    cameraprops = dev.pluginProps
                    #self.logger.debug(u'Before:'+unicode(cameraprops))
                    if actionevent == 'False':
                        cameraprops.update({'animateGif': False })
                        dev.replacePluginPropsOnServer(cameraprops)
                    if actionevent == 'True':
                        cameraprops.update({'animateGif': True})
                        dev.replacePluginPropsOnServer(cameraprops)
                    #self.logger.debug(unicode(u'After:')+unicode(cameraprops))
            return
        except:
            self.logger.exception(u'Caught Exception in Enable Anim Gifs')
            return

    def actionCreateAnimGif(self, valuesDict):
        self.logger.debug(u'action Create Gif for Cameras/s ')
        try:
            action = valuesDict.pluginTypeId
            if self.debuggif:
                self.logger.debug(unicode(valuesDict))
            cameras = valuesDict.props.get('deviceCamera',[])
            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if str(dev.id) in cameras and dev.enabled:
                        cameraname = dev.states['optionValue']
                        gifwidth = int(valuesDict.props.get('gifwidth', 800))
                        giftime = int(valuesDict.props.get('giftime', 10))
                        gifcompression = int(valuesDict.props.get('gifcompression', '50'))
                        #width = int(gifwidth)
                        #time = int(giftime)
                        #gifcompression = int(gifcompression)
                        if self.debuggif:
                            self.logger.debug(u'Action AnimGif: Cameraname:'+unicode(cameraname)+u' gifwidth:'+unicode(gifwidth)+u' giftime:'+unicode(giftime)+u' gifcompression:'+unicode(gifcompression))
                        AnothermyThread = threading.Thread(target=self.animateGif,args=[cameraname, gifwidth, giftime, gifcompression])
                        AnothermyThread.start()
                        self.logger.debug(
                            u'AnimGif: Action New Thread For Camera:' + unicode(cameraname) + u' & Number of Active Threads:' + unicode(
                                threading.activeCount()))
                        self.sleep(0.1)
            return
        except:
            self.logger.exception(u'Caught Exception in Create Anim Gifs')
            return

    def actionDownloadImage(self, valuesDict):
        self.logger.debug(u'action Download Image  for Cameras/s ')
        try:
            action = valuesDict.pluginTypeId
            if self.debugimage:
                self.logger.debug(unicode(valuesDict))
            cameras = valuesDict.props.get('deviceCamera',[])

            # MAChome = os.path.expanduser("~") + "/"
            # folderLocation = MAChome + "Documents/Indigo-BlueIris/"

            folderLocation = self.saveDirectory

            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if str(dev.id) in cameras and dev.enabled:
                        cameraname = dev.states['optionValue']
                        width = int(valuesDict.props.get('imagewidth', 800))
                        path = folderLocation + str(cameraname) + '.jpg'
                        if width <= 0:
                            yetanotherUrl = "http://" + str(self.serverip) + ':' + str(
                                self.serverport) + '/image/' + cameraname
                        else:
                            yetanotherUrl = "http://" + str(self.serverip) + ':' + str(
                                self.serverport) + '/image/' + cameraname + '?w=' + str(width)
                        ImageThread = threading.Thread(target=self.threadDownloadImage,
                                                           args=[cameraname, path, yetanotherUrl])
                        ImageThread.start()
            return
        except:
            self.logger.exception(u'Caught Exception in action Download Image')
            return

    def actiongetclipList(self, valuesDict):
 ## test html link
 ## https://www.w3schools.com/code/tryit.asp?filename=FOSD5YV6MT58
        try:
            self.logger.debug(u'action get Clip List Image for Cameras/s Called: Starting Thread.')
            clipThread = threading.Thread(target=self.actiongetclipListThread,  args=[valuesDict])
            clipThread.start()
        except:
            self.logger.exception(u'Caught Exception in actiongetclipList')
            return


    def actiongetclipListThread(self, valuesDict):
        try:
            self.logger.debug(u'thread actiongetclipList called  & Total # of Active Threads:' + unicode(
                threading.activeCount()))


            folderpath = indigo.server.getInstallFolderPath() + '/IndigoWebServer/static/'
            if not os.path.exists(folderpath):
                os.makedirs(folderpath)

            action = valuesDict.pluginTypeId
            if self.debugimage:
                self.logger.debug(unicode(valuesDict))
            cameras = valuesDict.props.get('deviceCamera',[])
            duration = valuesDict.props.get('duration', 1)
            folderLocation = self.saveDirectory

            nowtime = t.time()
            four_hours_ago = float(nowtime - (int(duration)*60*60))

            for server in indigo.devices.itervalues('self.BlueIrisServer'):
                #diskpath = server.states['diskname']
                clipaccess = server.states['clips']


            if clipaccess == 'false':
                self.logger.error(u'BlueIris Server user does not have clip access.  Cannot access.')
                return

            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if str(dev.id) in cameras and dev.enabled:
                        cameraname = dev.states['optionValue']
                        path = folderLocation + str(cameraname) + '.jpg'
                        clips = self.sendccommand('cliplist', {'camera':str(cameraname),'startdate':int(four_hours_ago), 'enddate':int(nowtime), 'tiles':False })
                        #self.logger.info(unicode(clips))

                        htmlheader = """<?php header(Access-Control-Allow-Origin: "h"""+ str('ttp://')+str(self.serverip)+ ':'+ str(self.serverport) + """"); ?>
                        <html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
                        
                        <title>Blue Iris</title>
                        <style>
.container {
     position: relative;
     display:table;
     width:100%;
   }
   
    .container img {background:#e1e1e1; padding 0px; border 1px; margin 2px; width:100%; min-height:200px} 
    
   .align {
     vertical-align: top;
     display: table-cell;
     position: relative;
   }

    .align img {background:#e1e1e1; padding 0px; border 1px; margin 2px; min-height:200px; min-width:200px}

.bottom-left {
    position: absolute;
    bottom: 8px;
    left: 16px;
    font-size:16pt;
}

.top-left {
    position: absolute;
    top: 8px;
    left: 16px;
    font-size: 16pt;
    font-size: 2vw;
}

.top-right {
    position: absolute;
    top: 8px;
    right: 16px;
    font-size: 16pt;
    font-size: 2vw;
}

.bottom-right {
    position: absolute;
    bottom: 8px;
    right: 16px;
    font-size: 16pt;
}

.centered {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
 } 
a:link {
color: #ffffff;
}
a:visited {
color: #999999;
}
a:hover {
color: #ff3300;
}
 
 </style>
                        
                        </head><body>
                        <h1>Blue Iris Clips</h1><p>
                        <h1>Camera: """ +str(cameraname) + """</h1><p></p>
                        """
                        page = ''
                        x=1
                        for clip in clips:

                            if 'path' in clip:
                                #wrongpath = clip['path'][1:]  ## path is completely wrong ???
                                #endpath = str(wrongpath[-4:])
                                #newpath = datetime.datetime.fromtimestamp( float(clip['date'])).strftime('%Y%m%d_%H%M%S')
                                #newpath = cameraname+'.'+newpath
                                diskpath = "http://" +str(self.serverusername)+':'+str(self.serverpassword) +'@' + str(self.serverip) + ':' + str(self.serverport)
                                #self.logger.debug(u'ClipPath:'+clip['path'])
                                clippath =  str(diskpath) + '/clips/' +  str(clip['path'])
                                thumbpath = str(diskpath) + '/thumbs/' + str(clip['path'])


                                imgsrc = """<img src=""" +'"' + str(thumbpath) + '" alt="No Image available ?CORS error/Try Safari" >\n'
                                divbottomleft =  '<div class="top-left">' +str(clip['camera'])+' '+str(clip['filesize'])+'</div>\n'
                                href = '<a href="' + str(clippath)+'"/a>\n'
                                #self.logger.info(unicode(clippath))
                                container = """<div class="container">\n"""
                                timeofclip =  datetime.datetime.fromtimestamp( clip['date'])
                                DateTaken = timeofclip.strftime('%c')
                                divbottomright = '<div class="top-right">' + str(DateTaken) +'</div>\n'

                                if x != 0:
                                    container = container+'\n<div class="image align">\n'
                                    end = ''
                                    x= 0
                                else:
                                    container = '</div><div class="image align">\n'
                                    x = 1
                                    end ='</div>\n</div>\n'

                                page = page + container +href  + imgsrc + divbottomright + divbottomleft +end




                        self.logger.debug(u'Saving Html ClipLists to :'+unicode(folderpath)+str(cameraname)+u"-cliplist.html")
                        html = htmlheader + page + '</body></html>'
                        # Write to HTML to file.html
                        with open(folderpath+'/'+str(cameraname)+"-cliplist.html", "w") as file:
                            file.write(html)
            return
        except:
            self.logger.exception(u'Caught Exception in action clipList Image')
            return


    def threadDownloadImage(self, cameraname, path, url):
        if self.debugimage:
            self.logger.debug(u'threadDownloadImages called.  Action New Thread For Camera:' + unicode(
                    cameraname) + u' & Number of Active Threads:' + unicode(
                    threading.activeCount()))
        try:
             # add timer and move to chunk download...
             start = t.time()

             r = requests.get(url, auth=(str(self.serverusername), str(self.serverpassword)),
                              stream=True, timeout=self.ServerTimeout)
             if r.status_code == 200:
                 # self.logger.debug(u'Yah Code 200....')
                 with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                        if t.time()>(start +self.ImageTimeout):
                            self.logger.error(u'Download Image Taking too long.  Aborted.  ?Network issue')
                            break

                 # with open(path, 'wb') as f:
                 #     r.raw.decode_content = True
                 #     shutil.copyfileobj(r.raw, f)
                    if self.debugimage:
                        self.logger.debug(u'Saved Image attempt for:'+unicode(path)+' for Camera:'+unicode(cameraname)+' in [seconds]:'+unicode(t.time()-start))
             else:
                 self.logger.debug(u'Issue Downloading Image. Failed.')

        except requests.exceptions.Timeout:
            self.logger.debug(u'threadDownloadImage has timed out and cannot connect to BI Server.')
            pass

        except requests.exceptions.ConnectionError:
            self.logger.debug(u'connectServer has a Connection Error and cannot connect to BI Server.')
            self.sleep(5)
            pass

        except:
            self.logger.exception(u'Caught Exception in threadDownloadImage')




    def pluginTriggering(self, valuesDict):
        self.logger.debug(u'pluginTriggering called')
        try:
            #self.logger.info(unicode(valuesDict))
            action = valuesDict.pluginTypeId
            actionevent = valuesDict.props['plugintriggersetting']
            cameras = valuesDict.props['deviceCamera']
            #self.logger.info(unicode(cameras))

            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if str(dev.id) in cameras:
                    self.logger.debug(u'Action is:' + unicode(action) + u' & Camera is:' + unicode(dev.name)+u' and action:'+unicode(actionevent))
                    if actionevent == 'False':
                        dev.updateStateOnServer('PluginTriggeringEnabled', value=False)
                        dev.updateStateOnServer('Motion', value=False ,uiValue='False')
                    if actionevent == 'True':
                        dev.updateStateOnServer('PluginTriggeringEnabled', value=True)
                        dev.updateStateOnServer('Motion', value=False, uiValue='False')
            return
        except:
            self.logger.exception(u'Caught Exception within pluginTriggerin')



    def ptzmain(self, camera, ptzargs):

        self.logger.debug(u'Ptz Main Called')

        self.sendccommand("ptz", {"camera": str(camera),"button": int(ptzargs),"updown": 0})
        return

    def ptzAction(self, valuesDict):

        try:
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
                self.ptzmain(cameraname, actionevent)
            else:
                self.logger.error(u'No such action event found: '+unicode(action))
        except:
            self.logger.exception(u'Caught Exception within Ptz Main')
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

    def actionChangeMacro(self, valuesDict):

        try:
            self.logger.debug(unicode(valuesDict))
            macronumber = str(valuesDict.props['macroNumber'])
            macrotext = str(valuesDict.props['macroText'])

            data = {
                "macro": {

                        "number": int(macronumber),
                        "value": str(macrotext)

            }}
        except:
        self.logger.error(u'Error within Change Macro - check details entered...')


        self.sendccommand("status", data )

        return


    ### Download Image

    def downloadImage(self, dev):
        if self.debugimage:
            self.logger.debug(u'downloadImage Called')
        try:
            cameraname = dev.states['optionValue']
            widthimage = dev.pluginProps.get('widthimage',0)
            folderLocation = self.saveDirectory

            path = folderLocation + str(cameraname) + '.jpg'
            if widthimage <=0:
                yetanotherUrl = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/image/' +cameraname
            else:
                yetanotherUrl = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/image/' + cameraname +'?w='+str(widthimage)
            if self.debugimage:
                self.logger.debug(u'Image:  Getting url:'+unicode(yetanotherUrl)+' with path:'+unicode(path))
            #thread this out - called a lot and could slow down
            ImageThread = threading.Thread(target=self.threadDownloadImage,
                                           args=[cameraname, path, yetanotherUrl])
            ImageThread.start()

            animateGif=dev.pluginProps.get('animateGif',False)
            try:
                if animateGif:
                    gifwidth = dev.pluginProps.get('gifwidth',0)
                    giftime = dev.pluginProps.get('giftime',10)
                    gifcompression = dev.pluginProps.get('gifcompression',50)
                    width = int(gifwidth)
                    time = int(giftime)
                    gifcompression = int(gifcompression)
                    myThread = threading.Thread(target=self.animateGif, args=[cameraname, width, time, gifcompression])
                    myThread.start()
                    self.logger.debug(u'New Thread Camera:'+unicode(cameraname)+u' & Number of Active Threads:'+unicode(threading.activeCount()))
                    return
            except:
                self.logger.exception(u'Caught Exception in Animated Gif Threads')

            return
        except:
            self.logger.exception(u'Caught Exception in download Camera Image')
            return


##################  Triggers

    def triggerStartProcessing(self, trigger):
        self.logger.debug("Adding Trigger %s (%d) - %s" % (trigger.name, trigger.id, trigger.pluginTypeId))
        assert trigger.id not in self.triggers
        self.triggers[trigger.id] = trigger

    def triggerStopProcessing(self, trigger):
        self.logger.debug("Removing Trigger %s (%d)" % (trigger.name, trigger.id))
        assert trigger.id in self.triggers
        del self.triggers[trigger.id]

    def triggerCheck(self, device, camera, event):

        if self.debugtriggers:
            self.logger.debug('triggerCheck run.  device.id:'+unicode(device.id)+' Camera:'+unicode(camera)+' Event:'+unicode(event))
        try:
            if self.pluginIsInitializing:
                self.logger.info(u'Trigger: Ignore as BlueIris Plugin Just started.')
                return

            if device.states['deviceIsOnline'] == False:
                if self.debugtriggers:
                    self.logger.debug(u'Trigger Cancelled as Device is Not Online')
                return

            if device.states['PluginTriggeringEnabled'] ==False:
                if self.debugtriggers:
                    self.logger.debug(u'Plugin Triggering is Disable for this Camera')
                return


            for triggerId, trigger in sorted(self.triggers.iteritems()):

                if self.debugtriggers:
                    self.logger.debug("Checking Trigger %s (%s), Type: %s, Camera: %s" % (trigger.name, trigger.id, trigger.pluginTypeId, camera))
                    #self.logger.debug(unicode(trigger))
                #self.logger.error(unicode(trigger))
                # Change to List for all Cameras

                if str(device.id) not in trigger.pluginProps['deviceCamera']:
                    if self.debugtriggers:
                        self.logger.debug("\t\tSkipping Trigger %s (%s), wrong Camera: %s" % (trigger.name, trigger.id, device.id))
                elif trigger.pluginTypeId == "motionTriggerOn" and event =='motiontrue':
                    if self.debugtriggers:
                        self.logger.debug("===== Executing motionTriggerOn/motiontrue Trigger %s (%d)" % (trigger.name, trigger.id))
                    indigo.trigger.execute(trigger)
                elif trigger.pluginTypeId == "motionTriggerOff" and event =='motionfalse':
                    if self.debugtriggers:
                        self.logger.debug("===== Executing motionTriggerOff/motionfalse Trigger %s (%d)" % (trigger.name, trigger.id))
                    indigo.trigger.execute(trigger)
                else:
                    if self.debugtriggers:
                        self.logger.debug("Not Run Trigger Type %s (%d), %s" % (trigger.name, trigger.id, trigger.pluginTypeId))

        except:
            self.logger.exception(u'Caught Exception within Trigger Check')
            return
## Update routines

    def checkForUpdates(self):

        updateavailable = self.updater.getLatestVersion()
        if updateavailable and self.openStore:
            self.logger.info(u'BlueIris Plugin: Update Checking.  Update is Available.  Taking you to plugin Store. ')
            self.sleep(2)
            self.pluginstoreUpdate()
        elif updateavailable and not self.openStore:
            self.errorLog(u'BlueIris Plugin: Update Checking.  Update is Available.  Please check Store for details/download.')

    def updatePlugin(self):
        self.updater.update()

    def pluginstoreUpdate(self):
        iurl = 'http://www.indigodomo.com/pluginstore/149/'
        self.browserOpen(iurl)
################## Animated Gifs

################## Run the create gifs in a seperate thread as will take a few seconds we can't afford

    def animateGif(self, cameraname, width, time, gifcompression):
        # file_names = sorted((fn for fn in os.listdir(folderLocation) ))
        try:
            if self.debuggif:
                self.logger.debug(u'AnimateGif Called: In a New thread:')
                self.logger.debug(u'animateGif: camera:'+unicode(cameraname)+u' width:'+unicode(width)+u' time:'+unicode(time)+u' gifcompression:'+unicode(gifcompression))
            # MAChome = os.path.expanduser("~") + "/"
            # folderLocation = MAChome + "Documents/Indigo-BlueIris/"+str(cameraname)+'/'

            folderLocation = self.saveDirectory+str(cameraname)+'/'

            # if not os.path.exists(folderLocation):
            #     os.makedirs(folderLocation)
            # # Download a few seconds of images at width specified above.
            # if not os.path.exists(folderLocation+'tmp'):
            #     os.makedirs(folderLocation+'tmp')

            if width <= 0:
                theUrl = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/image/' + cameraname
            else:
                theUrl = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/image/' + cameraname + '?w=' + str(width)

            x=100
            while x <115:
            #for x in range(100,115):
                start = t.time()
                path = folderLocation + 'tmp/' + str(x)+'.jpg'
                r = requests.get(theUrl, auth=(str(self.serverusername), str(self.serverpassword)), stream=True, timeout=self.ServerTimeout)

                if self.debuggif:
                    self.logger.debug(u'URL Called:'+unicode(theUrl))
                    self.logger.debug(u'Time '+unicode(t.time())+u' Path/Name in Order:'+unicode(path))
                if r.status_code == 200:
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                            if t.time() > (start + self.ImageTimeout):
                                self.logger.error(u'AnimGif - Download Image Taking to long.  Aborted.')
                                break
                    if self.debuggif:
                        self.logger.debug(u'Animgif: Image Download Attempt for: ' + unicode(path) + u' in [seconds]:' + unicode(t.time() - start))
                    #
                    # with open(path, 'wb') as f:
                    #     r.raw.decode_content = True
                    #     shutil.copyfileobj(r.raw, f)
                else:
                    self.logger.debug(u'Issue with BI connection. No image downloaded. Status code:'+unicode(r.status_code)+' Error:'+unicode(r.text))
                    #not sure about below - might hang forever and lead to multiple threads versus missing image..
                    #removing
                    #x=x-1
                    t.sleep(2)


                Interval = float( float(time) / 15)
                #change above
                if self.debuggif:
                    self.logger.debug(u'Wait Interval: '+unicode(Interval))
                x=x+1
                t.sleep(Interval)
            #
            #self.newThreadDownload( folderLocation, cameraname, width, time)
            file_names = os.listdir(folderLocation+'tmp/')
            x = 0
            for filename in file_names:
                if '.jpg' in filename:

                    filename = folderLocation + 'tmp/'+ filename
                    # oops - isn't sorted....
                    # avoid sort just rename,remove last 4 and add gif
                    newfilename = filename[:-4]+'.gif'
                    #newfilename = folderLocation + 'tmp/' + str(x) + '.gif'
                    # if self.debuggif:
                    #     self.logger.debug(u'newfilename:'+unicode(newfilename)+' :::::: old filename:'+unicode(filename))
                    #self.logger.info(unicode(filename))
                    p = subprocess.Popen(['/usr/bin/sips', '-s', 'format', 'gif', filename, '--out', newfilename],
                                         stdout=subprocess.PIPE).communicate()[0]
                    # self.logger.info(unicode(p))
                    x = x + 1
            t.sleep(0.10)

            newfilename = folderLocation + 'Animated.gif'
            file_names = os.listdir(folderLocation + 'tmp/')
            listfilenames = ''

            for filename in sorted(file_names):
                if '.gif' in filename:
                    listfilenames = listfilenames + ' ' + folderLocation + 'tmp/' + filename

            pathtouse = os.path.normpath(self.pathtoGifsicle)
            #self.logger.info(unicode(self.pathtoGifsicle))
            #self.logger.info(unicode(pathtouse))
            if self.debuggif:
                self.logger.debug(u'listfilenames (and order) to make into anim:'+unicode(listfilenames))
                self.logger.debug(u'new save filename'+unicode(newfilename))
            try:
                argstopass = '"' + pathtouse + '"' +' --delay 50 --colors 256 --loopcount --lossy='+str(gifcompression)+' ' + str(
                    listfilenames) + ' > ' + str(newfilename)
                p1 = subprocess.Popen([argstopass], shell=True)

                if self.debuggif:
                    output, err = p1.communicate()
                    self.logger.debug(unicode(argstopass))
                    self.logger.debug('giflossy/sicle return code:'+ unicode(p1.returncode)+' output:'+ unicode(output)+' error:'+unicode(err))
                self.createupdatevariable('lastAnimGif',str(newfilename))

            except Exception as e:
                self.logger.exception(u'Caught Exception within animGIF gifsicle - newThread')

        except requests.exceptions.Timeout:
            self.logger.debug(u'animGif requests has timed out and cannot connect to BI Server.')
            pass

        except requests.exceptions.ConnectionError:
            self.logger.debug(u'animGif requests has timed out/Connection Error and cannot connect to BI Server.')
            pass


        except self.StopThread:
            self.logger.info(u'Restarting/or error. Stopping thread.')
            pass

        except:
            self.logger.exception(u'Caught Error in Anim Gif Thread')


    # def newThreadDownload(self, folderLocation, cameraname, widthimage, time):
    #
    #     if self.debuggif:
    #         self.logger.debug(u'newThreadDownload Some Images Called')
    #         #self.logger.info(u'newThreadDownload:')
    #     try:
    #         if not os.path.exists(folderLocation+'tmp'):
    #             os.makedirs(folderLocation+'tmp')
    #
    #         x = 0
    #         if widthimage <= 0:
    #             AnotherUrl = "http://" + str(self.serverip) + ':' + str(self.serverport) + '/image/' + cameraname
    #         else:
    #             AnotherUrl = "http://" + str(self.serverip) + ':' + str(
    #                 self.serverport) + '/image/' + cameraname + '?w=' + str(widthimage)
    #
    #         for x in range(0,15):
    #             path = folderLocation + 'tmp/' + str(x)+'.jpg'
    #
    #             if self.debuggif:
    #                 self.logger.debug(u'newThreadDownload:  Getting url:' + unicode(AnotherUrl) + ' with path:' + unicode(path))
    #
    #             r = requests.get(AnotherUrl, auth=(str(self.serverusername), str(self.serverpassword)), stream=True)
    #             if r.status_code == 200:
    #                 with open(path, 'wb') as f:
    #                     r.raw.decode_content = True
    #                     shutil.copyfileobj(r.raw, f)
    #             else:
    #                 self.logger.debug(u'Issue with BI connection. No image downloaded. Status code:'+unicode(r.status_code)+' Error:'+unicode(r.text))
    #
    #             Interval = time/15
    #             #change above
    #             time.sleep(Interval)
    #         return
    #
    #     except self.StopThread:
    #         self.logger.info(u'Restarting/or error. Stopping thread.')
    #         pass
    #
    #     except:
    #         self.logger.exception(u'Exception in new Thread Download Camera Images')
    #         return

###########  Add own Http Server, avoid dependency on subscribeVariable.  Remove Variables
#
    def listenHTTP(self):
        try:
            self.debugLog(u"Starting HTTP listener thread")
            indigo.server.log(u"Http Server Listening on TCP port " + str(self.listenPort))
            self.server = ThreadedHTTPServer(('', self.listenPort), lambda *args: httpHandler(self, *args))
            self.server.serve_forever()

        except self.StopThread:
            self.logger.debug(u'Self.Stop Thread called')
            pass
        except:
            self.logger.exception(u'Caught Exception in ListenHttp')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class httpHandler(BaseHTTPRequestHandler):
    def __init__(self,plugin, *args):
        self.plugin=plugin
        #self.logger = logger
        if self.plugin.debugserver:
            self.plugin.logger.debug(u'New Http Handler thread:'+threading.currentThread().getName()+", total threads: "+str(threading.activeCount()))
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        global rootnode
        if self.plugin.debugserver:
            self.plugin.logger.debug(u'Received Http POST')
            self.plugin.logger.debug(u'Sending HTTP 200 Response')

        try:

            content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
            post_data = self.rfile.read(content_length)  # <--- Gets the data itself
              # <-- Print post data
            if self.plugin.debugserver:
                self.plugin.logger.debug(unicode(self.path))
                #self.plugin.logger.debug(unicode(post_data))

            #self._set_headers()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # if self.plugin.debugserver:
            #     self.plugin.logger.debug(unicode('After End_Headers'))


            if 'indigo' not in str(post_data).lower():
                if self.plugin.debugserver:
                    self.plugin.logger.info(unicode('Received a reply with no Indigo in POST text.  Ignoring. '))
                    self.plugin.logger.info(unicode('Have you put Indigo in the POST box?  Or is there something else sending to this port? '))
                return

            # if self.plugin.debugserver:
            #     self.plugin.logger.debug(unicode('After Indigo Post Check'))

            listresults = str(self.path).split('/')

            if self.plugin.debugserver:
                self.plugin.logger.debug(u'List of Results Equals:'+unicode(listresults) +u'  and length of listresults:'+unicode(len(listresults)))

            if len(listresults)<=4:
                if self.plugin.debugserver:
                    self.plugin.logger.info(u'To few information received from BlueIris.  Have you used the correct format?' )
                    self.plugin.logger.info(u'Should be: http://  IndigoIP:SelectedPort/&CAM/&TYPE/&PROFILE/True')
                    self.plugin.logger.info(u'POST text:  Indigo')
                    self.plugin.logger.info(u'& in reset when trigger is reset:')
                    self.plugin.logger.info(u'Should be: http://  IndigoIP:SelectedPort/&CAM/&TYPE/&PROFILE/False')
                    self.plugin.logger.info(u'POST text:  Indigo')
                    return
            cameraname = str(listresults[1])
            typetrigger= listresults[2]
            activeprofile = listresults[3]
            motion = str(listresults[4]).lower()
            ## Check and Update Device as BIServer info received

            for dev in indigo.devices.itervalues('self.BlueIrisCamera'):
                if dev.enabled:
                    if dev.states['optionValue'] == cameraname:

                        if self.plugin.debugserver:
                            self.plugin.logger.debug(u'Trigger Motion for this Camera:'+unicode(cameraname))
                        if motion == 'true':
                            dev.updateStateOnServer('Motion', value=True, uiValue='True')
                            dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensorTripped)
                            update_time = t.strftime('%c')
                            dev.updateStateOnServer('timeLastMotion', value=str(update_time))
                            dev.updateStateOnServer('lastMotionTriggerType', value=str(typetrigger))
                            self.plugin.triggerCheck(dev, cameraname, 'motiontrue')

                            if dev.pluginProps.get('saveimage', False):
                                self.plugin.downloadImage(dev)
                        elif motion =='false':
                            dev.updateStateOnServer('Motion', value=False, uiValue='False')
                            dev.updateStateImageOnServer(indigo.kStateImageSel.MotionSensor)
                            dev.updateStateOnServer('lastMotionTriggerType', value=str(typetrigger))
                            self.plugin.triggerCheck(dev, cameraname, 'motionfalse')
            return
        except:
            self.plugin.logger.exception(u'Exception in do_POST single thread.')
            return

#todo
#add Motion Ended Trigger
#Consider trigger animgif finished...