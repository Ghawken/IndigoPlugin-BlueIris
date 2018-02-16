**## BlueIris Indigo Plugin**
![https://s17.postimg.org/mv5typblr/icon.png](https://s17.postimg.org/mv5typblr/icon.png)


Have put together the Indigo Plugin for BlueIris windows based Cam Server Software.

This plugin creates BlueIris Server Device and BlueIris Cameras within Indigo.  With these devices you can monitor the current condition of Server (CPU/Mem etc) and also trigger Cameras to record.  There are multiple actions that Indigo can perform on each or multiple cameras - IR on/IR off, Ptz cycle on, enable/disable camera/motion etc.

From within BI we also setup communication back to Indigo - this enables immediate indigo awareness of any camera based motion events.  So Indigo based events can be triggered on one or multiple cameras - eg. motion turn lights on etc.  There is a small amount of setup required within BI for each Camera to enable this.

Here:
http://www.indigodomo.com/pluginstore/149/

**Indigo 7 Only**

Installation
Download, Enable.

For Neatness I suggest creating a BlueIris Directory - which the plugin will use.
![https://s17.postimg.org/41k11akz3/Create_Directory.png](https://s17.postimg.org/41k11akz3/Create_Directory.png)


Go to Plugin Config

![https://s17.postimg.org/7l5yr4xzj/Plug_Config1.png](https://s17.postimg.org/7l5yr4xzj/Plug_Config1.png)


Enter:
BlueIris Server: IP address
Port Used for Webserver:
Username
Password

(for some actions your BI account needs to be admin enabled)


Click Login/Generate Server Device, here:
![https://s17.postimg.org/9pqbs74r3/Plug_Config_Loginbutton.png](https://s17.postimg.org/9pqbs74r3/Plug_Config_Loginbutton.png)


(This will generate a main BI server device in either BlueIris directory or main)
![https://s17.postimg.org/jzsqrg2cf/Main_Device_Created.png](https://s17.postimg.org/jzsqrg2cf/Main_Device_Created.png)

if all goes well -- Generate Cameras button should appear
![https://s17.postimg.org/qdhtuorsv/Generate_Camera_Button.png](https://s17.postimg.org/qdhtuorsv/Generate_Camera_Button.png)

Click this - to generate all your camera devices...

![https://s17.postimg.org/9cyxm19mn/List_Camera_Devices.png](https://s17.postimg.org/9cyxm19mn/List_Camera_Devices.png)



Main BI Server Device:

![http://i66.tinypic.com/1qh4yf.png](http://i66.tinypic.com/1qh4yf.png)

Generates this device with status options

![http://i64.tinypic.com/fongab.png](http://i64.tinypic.com/fongab.png)

Allows CPU,Mem Monitoring etc and triggering if CPU gets out of hand



**## BlueIris Server Camera End Setup**

**To trigger plugin - add**
indigousername:indigopassword@indigoip:8176/variables/&CAM?_method=put&value=True
to each camera in BlueIris;  Camera: Alerts, request from web service:  When triggered.

**BI ScreenShots:**

![http://i68.tinypic.com/egwprd.png](http://i68.tinypic.com/egwprd.png)
&
![http://i63.tinypic.com/6i8rkm.png](http://i63.tinypic.com/6i8rkm.png)

-----------------------------------------------------------------------------------------------------------------------------
**For Indigo with Basic Authenication (not Indigo's default):**

Remembering to put this in all alert boxes for every BI Camera:

    indigousername:indigopassword@indigoIP:8176/variables/&CAM?_method=put&value=True

**DOES NOT **Need to be changed - same lines with correct username/password/IP/Port for every camera - just copy and paste - took me 60 seconds for 15 cameras.

**OR**

**For Indigo with  Digest Authenication  (Default for Indigo):**

1. Download and install curl for Windows [[url]https://curl.haxx.se/download.html[/url]].  Put the files in c:\curl or somewhere you can find them.
2. In BI, instead of using a web service on the alert action, choose "Run a program or execute a script"
3. In the File, navigate to the appropriate place and select your curl.exe file, e.g.  **c:\curl\curl.exe**
4. In Parameters, put this:
`-u username:password --digest http://192.168.x.x:8176/variables/&CAM?_method=put&value=True`
Remember that CAM gets replaced by the BI short name, which is the variable created by the plugin
-----------------------------------------------------------------------------------------------------------------------------

This will trigger and update camera in Indigo everytime triggered or motion sensor changes - this happens immediately.


## **Actions:**

There are multiple support actions that can be performed on each/some/or the Server

![https://s17.postimg.org/vowqfdqq7/Action_Options.pnghttps://s17.postimg.org/vowqfdqq7/Action_Options.png](https://s17.postimg.org/vowqfdqq7/Action_Options.pnghttps://s17.postimg.org/vowqfdqq7/Action_Options.png)

![https://camo.githubusercontent.com/6da5f1a4ee61eefae425c1064cfc4ff058fdc757/687474703a2f2f6936332e74696e797069632e636f6d2f33327a693235642e706e67](https://camo.githubusercontent.com/6da5f1a4ee61eefae425c1064cfc4ff058fdc757/687474703a2f2f6936332e74696e797069632e636f6d2f33327a693235642e706e67)


**Triggers**

The Plugin also creates a Trigger which is run when the selected Camera(s) detects motion.

You can select multiple cameras:

![https://s17.postimg.org/si26vsgkv/Select_Trigger_Cameras.png](https://s17.postimg.org/si26vsgkv/Select_Trigger_Cameras.png)


The triggering of these alerts is dependant in the settings that are created within BlueIris as above - including the retrigger timeout - will not retrigger until this time has passed.


**Camera Device Options**

The Camera Devices have a few user configurable options:

- Save Image if Camera Triggered
- Width in Pixels of image (up to maximum of the camera)  Proportions are left unchanged

![https://s17.postimg.org/4scr7c2un/Camera_Options.png](https://s17.postimg.org/4scr7c2un/Camera_Options.png)

If this option is select the plugin will download an image from this camera locally everytime it is triggered.
It is stored in path
`/User/Documents/Indigo-BlueIris/`

This image can be used in Control Pages (showing last triggering) or used to send via iMsg/PushOver etc with these plugins.




Glenn








