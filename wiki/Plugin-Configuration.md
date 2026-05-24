![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# Plugin Configuration

Open **Plugins ▸ BlueIris ▸ Configure…** to access plugin preferences.

![Plugin configuration screen](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/PlugConfig1.png)

---

## Connection Settings

| Field | Default | Description |
|-------|---------|-------------|
| **BI Server IP** | — | LAN IP address of your Blue Iris Windows machine (e.g. `192.168.1.100`) |
| **BI Web Port** | `81` | The port Blue Iris's built-in web server listens on |
| **Username** | — | A BI user account.  Use an **admin** account for PTZ, config, macro-change, and profile-change actions |
| **Password** | — | Password for the BI user account |

---

## Plugin HTTP Listener

| Field | Default | Description |
|-------|---------|-------------|
| **Plugin HTTP Port** | `4556` | The port the plugin's built-in HTTP server listens on.  This is the port you use in the BI webhook URL (see [Blue Iris Setup](Blue-Iris-Setup.md)).  Change it if 4556 is in use. |

![Plugin HTTP port setting](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/PlugConfigPort.png)

The listener accepts BI's webhook path segments and routes them to motion triggers, plate triggers, log triggers, etc.  No `subscribeToVariables` is required.

---

## RTSP Settings

| Field | Default | Description |
|-------|---------|-------------|
| **RTSP Port** | `554` | Port Blue Iris uses for RTSP streams.  Used by the **Create MP4 Video** action (`animateMp4`) to build `rtsp://…:<rtspport>/<cam>&stream=2` URLs. |

If BI is configured to use a non-standard RTSP port (e.g. `8554` for NAT traversal) update this field.

---

## File Settings

| Field | Default | Description |
|-------|---------|-------------|
| **Save Directory** | — | Absolute path to the folder where the plugin writes downloaded images, animated WebP/GIF/HEIF/MP4 files, and clip-list HTML.  Must exist before saving.  Example: `/Users/yourname/Documents/Indigo-BlueIris/` |

Each camera gets a sub-folder named after its BI short name, e.g.:
```
/Users/yourname/Documents/Indigo-BlueIris/FrontDoor/Animated.mp4
/Users/yourname/Documents/Indigo-BlueIris/FrontDoor/Animated.webp
```

---

## Advanced Options

The plugin exposes additional camera and motion settings under the Advanced Options panel:

![Advanced options panel](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/AdvancedOptions.png)

---

## Debug Logging

| Field | Default | Description |
|-------|---------|-------------|
| **Debug Level** | Info | Sets the verbosity of the Indigo log.  `Debug` shows ffmpeg command lines, frame counts, thread names, etc. |

---

## Server Actions in Plugin Config

| Button | What It Does |
|--------|-------------|
| **Login / Generate Server Device** | Authenticates with BI and creates the BlueIris Server device in Indigo |
| **Generate Cameras** | Queries BI's camera list and creates/updates one device per camera |
| **Refresh All Devices** | Pulls the latest state for all cameras without recreating devices |
