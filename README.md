## BlueIris Indigo Plugin
![http://blueirissoftware.com/media/Download_03.png](http://blueirissoftware.com/media/Download_03.png)

Have put together the Indigo Plugin for BlueIris windows based Cam Server Software. http://blueirissoftware.com/

https://github.com/Ghawken/IndigoPlugin-BlueIris
&
http://forums.indigodomo.com/viewtopic.php?f=222&t=20174&p=154546#p154546


# ** Indigo 7 Only**



Install

Go to Plugin Config

Enter:
BlueIris Server: IP address
Port Used for Webserver:
BlueIris Username
BlueIris Password

Click Login/Generate Server Device
(This will generate a main BI server device in either BlueIris directory or main)
if all goes well -- Generate Cameras button should appear

Click this - to generate all your camera devices...

Select Debugging options

Click Save.

## **Update 0.3.0:**

See github main link for download

Add Main BI Server Device.  This is generated in PluginConfig Page with the Login button

![http://i66.tinypic.com/1qh4yf.png](http://i66.tinypic.com/1qh4yf.png)

Generates this device with status options

![http://i64.tinypic.com/fongab.png](http://i64.tinypic.com/fongab.png)

Allows CPU,Mem Monitoring etc and triggering if CPU gets out of hand


Change to generate Cameras - generate them in PluginConfig.  If deleted won't be recreated unless this button is pressed again.
(if pressed again won't remove current devices)

Generate Cameras button appears if login successful.

Create Variables in BlueIris/Variable folder enabled BI to tell plugin what is happening

Fix: Remove device from Profile selection

**To trigger plugin - add**
indigousername:indigopassword@indigoip:8176/variables/&CAM?_method=put&value=True
to each camera in BlueIris;  Camera: Alerts, request from web service:  When triggered.


**BI ScreenShots:**

![http://i68.tinypic.com/egwprd.png](http://i68.tinypic.com/egwprd.png)
&
![http://i63.tinypic.com/6i8rkm.png](http://i63.tinypic.com/6i8rkm.png)



--------------------------------------------------------------------------------------------------------------------
For Triggering within Indigo need to do one of the following for each Camera
--------------------------------------------------------------------------------------------------------------------
## **For Indigo with Basic Authenication:**

Remembering to put this in all alert boxes for every BI Camera:


    indigousername:indigopassword@indigoIP:8176/variables/&CAM?_method=put&value=True

DOES NOT Need to be changed - same lines with correct username/password/IP/Port for every camera - just copy and paste - took me 60 seconds for 15 cameras.
--------------------------------------------------------------------------------------------------------------------
OR
--------------------------------------------------------------------------------------------------------------------
## **For Indigo with  Digest Authenication  (Default):**

1. Download and install curl for Windows [[url]https://curl.haxx.se/download.html[/url]].  Put the files in c:\curl or somewhere you can find them.
2. In BI, instead of using a web service on the alert action, choose "Run a program or execute a script"
3. In the File, navigate to the appropriate place and select your curl.exe file, e.g.  **c:\curl\curl.exe**
4. In Parameters, put this:
`-u username:password --digest http://192.168.x.x:8176/variables/&CAM?_method=put&value=True`
[Remember that CAM gets replaced by the BI short name, which is the variable created by the plugin]
5.  Do this for every Camera within BlueIris

-------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------------

This will trigger and update camera in Indigo everytime triggered or motion sensor changes - this happens immediately.

Can use Indigo Events/Triggers to trigger action on Motion

There Multiple Action Groups created which can be selected for each camera, from Ptz controls, contrast, select preset, IR on off etc., select Profiles.
These can all be triggered from within Indigo as you required.




To come:
- generate animated gif to send via imsg or other
- add static URLs for Image/Videos to Camera devices for Control Page usage
+ any suggestions!



Glenn
