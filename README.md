# BlueIris Indigo Plugin

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/icon.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/icon.png)


Have put together the Indigo Plugin for BlueIris windows based Cam Server Software.

This plugin creates BlueIris Server Device and BlueIris Cameras within Indigo.  With these devices you can monitor the current condition of Server (CPU/Mem etc) and also trigger Cameras to record.  There are multiple actions that Indigo can perform on each or multiple cameras - IR on/IR off, Ptz cycle on, enable/disable camera/motion etc.

From within BI we also setup communication back to Indigo - this enables immediate indigo awareness of any camera based motion events.  So Indigo based events can be triggered on one or multiple cameras - eg. motion turn lights on etc.  There is a small amount of setup required within BI for each Camera to enable this.

Here:
http://www.indigodomo.com/pluginstore/149/

## Indigo 7 Only

Installation
Download, Enable.

For Neatness I suggest creating a BlueIris Directory - which the plugin will use.
![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/CreateDirectory.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/CreateDirectory.png)


Go to Plugin Config

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/PlugConfig1.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/PlugConfig1.png)


Enter:
BlueIris Server: IP address
Port Used for Webserver:
Username
Password

(for some actions your BI account needs to be admin enabled)

## 0.6.0 Change

Changes to Plugin managing it's own Http Server:

Need to put port number of server in PluginConfig:

Default port 4556

Can be changed to any allowed port if needed.


Click Login/Generate Server Device, here:
![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/PlugConfigLoginbutton.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/PlugConfigLoginbutton.png)


(This will generate a main BI server device in either BlueIris directory or main)
![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/MainDeviceCreated.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/MainDeviceCreated.png)

if all goes well -- Generate Cameras button should appear
![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/GenerateCameraButton.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/GenerateCameraButton.png)

Click this - to generate all your camera devices...

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/ListCameraDevices.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/ListCameraDevices.png)




## Main BI Server Device


![http://i66.tinypic.com/1qh4yf.png](http://i66.tinypic.com/1qh4yf.png)

Generates this device with status options

![http://i64.tinypic.com/fongab.png](http://i64.tinypic.com/fongab.png)

Allows CPU,Mem Monitoring etc and triggering if CPU gets out of hand



-----------------------------------------------------------------------------------

# BlueIris Server Camera End Setup

To enable triggers from with the plugin - add
```
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/True/&ALERT
```
or
```
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/False/&ALERT
```


eg. IndigoIP = 192.168.1.6,  Port selected in PluginConfig: 4556

```
When Triggered
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/True/&ALERT
POST text: Indigo

Request again when trigger is reset
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/False/&ALERT
POST text: Indigo
```


to each camera in BlueIris;  Camera: Alerts, request from web service:  When triggered.
&


**BI ScreenShots:**

eg. Version 4

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v4CameraAlertSetup.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v4CameraAlertSetup.png)


eg. Version 5

Trigger On:

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v5CameraAlertON.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v5CameraAlertON.png)


Trigger Ended:
![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v5CameraAlertOFF.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/v5CameraAlertOFF.png)

 
-----------------------------------------------------------------------------------------------------------------------------
This has changed from new version 0.6.0
Same for everyone - no longer different for Basic/Digest Authenication

Allows:Motion On& Off, and adds

Add new Camera Device States:
lastMotionTriggerType  possible results
- TEST [from the Test button]
- MOTION
- AUDIO
- EXTERNAL
- WATCHDOG


timelastMotion = time of last Motion Detection
-----------------------------------------------------------------------------------------------------------------------------

This will trigger and update camera in Indigo everytime triggered or motion sensor changes - this happens immediately.

-----------------------------------------------------------------------------------------------------------------------------

## **Actions:**

There are multiple support actions that can be performed on each/some/or the Server

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/ActionOptions.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/ActionOptions.png)

![https://camo.githubusercontent.com/6da5f1a4ee61eefae425c1064cfc4ff058fdc757/687474703a2f2f6936332e74696e797069632e636f6d2f33327a693235642e706e67](https://camo.githubusercontent.com/6da5f1a4ee61eefae425c1064cfc4ff058fdc757/687474703a2f2f6936332e74696e797069632e636f6d2f33327a693235642e706e67)

## Recent Actions Added

Add Enable/Disable Generate Animated Gifs as Action Group per Camera/s
[this enables you to change the camera settings with an action as required - e.g arrived home; stop making them]

Add Status PluginTriggeringEnabled to each Camera.
[this enabled you as an action to disable any Plugin Based triggering [this doesn't affect BI Server]
eg. arrived home - Disable this setting and no Plugin Triggers for this camera will occur]

PluginTriggeringEnabled for all Cameras reset at Plugin startup to Enabled.




## Triggers

The Plugin also creates a Trigger which is run when the selected Camera(s) detects motion.

You can select multiple cameras:

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/SelectTriggerCameras.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/SelectTriggerCameras.png)

The triggering of these alerts is dependant in the settings that are created within BlueIris as above - including the retrigger timeout - will not retrigger until this time has passed.


## Camera Device Options

The Camera Devices have a few user configurable options:

- Save Image if Camera Triggered
- Width in Pixels of image (up to maximum of the camera)  Proportions are left unchanged

![https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/CameraOptions.png](https://github.com/Ghawken/IndigoPlugin-BlueIris/blob/cliplist/Images/CameraOptions.png)

If this option is select the plugin will download an image from this camera locally everytime it is triggered.
It is stored in path
`/User/Documents/Indigo-BlueIris/`

This image can be used in Control Pages (showing last triggering) or used to send via iMsg/PushOver etc with these plugins.

## Animated GIFs Created


The Plugin can also generate an Animated Gif for each Camera.  This can be done automatically if triggered from within the Camera Device settings, or it can be performed as an Action on selected Cameras

The animated Gif once triggered is then generated - eg. if length is 10 seconds 15 images/10 seconds are taken, and then packaged and sent, so if being used in a action group will need to add appropriate delay
for it all to be created.

The way I have done this is to use two external calls - one to build-in Sips app to convert jpg to Gif. The next is to package gifiscle within the plugin and this is called to create the Anims. Separate threads are created so there is no main-thread time impact for this.
There are no additional libraries required (I hope....)

***Options***

These can then be sent via imsg very easily with the following Applescript action group.


```
delay 5
tell application "Messages"
   set myid to get id of first service
   set theBuddy to buddy "toemailaddress" of service "E:fromemailaddress note the E:"
   send POSIX file "/Users/Username/Documents/Indigo-BlueIris/CameraNameShort/Animated.gif" to theBuddy
end tell
```


Would suggest this is best in a external script given the time to run aspects. Delay above depends on how long images are captured for.









Glenn








