![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# BlueIris Indigo Plugin

An [Indigo](https://www.indigodomo.com/) plugin that gives full two-way control and automation of [Blue Iris](https://blueirissoftware.com/) — the Windows IP-camera server — from your Mac home automation hub.

**[📖 Full documentation in the Wiki](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki)**

---

## Overview

The plugin creates Indigo devices for your BI server and every camera, then fires Indigo triggers the instant Blue Iris detects motion, a license plate, an AI tag, a geofence event, or a log condition.  You can also drive Blue Iris from Indigo — PTZ moves, profile switches, macro changes, image downloads, and animated clip creation.

### What it creates

| Object | Description |
|--------|-------------|
| **BlueIris Server device** | CPU, memory, disk, profile, schedule, connection count |
| **BlueIris Camera device** | Motion state, recording, PTZ, plate data, 30+ live states |
| **BlueIris Device** | Geofence / mobile device inside/outside state |
| **BlueIris User** | Login events per BI user account |

### Triggers

| Trigger | Fires when… |
|---------|-------------|
| Camera Motion On / Off | BI sends a motion start or reset webhook |
| AI Tag | BI's AI engine tags an alert (`person`, `vehicle`, `animal`, …) |
| License Plate Found | ALPR detects any plate |
| License Plate Match | Detected plate matches your watch list |
| User Login | A named BI user logs in |
| Geofence Inside / Outside | Mobile device enters or leaves BI's geofence |
| BI Log Message | Log entry matches a category / text filter |
| No Signal | Camera loses video |
| Disk Space Low | Free disk drops below a threshold |
| Software Update Available | BI reports a new version |

### Actions

| Category | Actions |
|----------|---------|
| **Camera control** | Trigger motion, enable/disable motion detection, pause, manual record |
| **PTZ** | Pan, tilt, zoom, home, preset, IR on/off, brightness, Hz |
| **Server** | Change active profile (0–7), change macro contents |
| **Media** | Download JPEG snapshot, create animated WebP, GIF, HEIC, or MP4 clip |
| **Plugin** | Enable/disable plugin triggering per camera, enable/disable auto-GIF |

---

## Screenshots

![Plugin configuration](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/PlugConfig1.png)

![Camera device states](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/BICameraStates.png)

![Available actions](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/ActionOptions.png)

![Available triggers](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/BITriggers.png)

---

## Quick Start

1. **Install** — download from the [Indigo Plugin Store](http://www.indigodomo.com/pluginstore/149/) or from [GitHub Releases](https://github.com/Ghawken/IndigoPlugin-BlueIris/releases) and double-click the `.indigoPlugin` bundle
2. **Configure** — open **Plugins ▸ BlueIris ▸ Configure…**, enter your BI server IP, port, username and password
3. **Login** — click **Login / Generate Server Device** to create the server device
4. **Cameras** — click **Generate Cameras** to create one Indigo device per camera
5. **Webhooks** — in Blue Iris, add the plugin's URL to each camera's alert settings:

```
http://<IndigoMacIP>:4556/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH
```

For full setup instructions including ALPR, see the **[Wiki](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki)**.

---

## Animated Media

The plugin can capture live footage and save it as an animated file ready to send via iMessage, email, or push notification.

| Format | Engine | Best For |
|--------|--------|----------|
| **Animated WebP** | Pillow / MJPEG | iMessage, web pages |
| **Animated GIF** | gifsicle (bundled) | Email, broad compatibility |
| **HEIC still** | pillow-heif | Apple ecosystem |
| **MP4 video** | ffmpeg (bundled) | Highest quality, iMessage video |

MP4 recording pulls from Blue Iris's RTSP H.264 substream with BI-side scaling (`&h=` parameter) so the stream arrives at the correct resolution without taxing the Mac's encoder.

See **[Animated Media](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Animated-Media)** in the wiki for full details.

---

## License Plate Recognition (ALPR)

Blue Iris 5's built-in ALPR engine can read plate text from camera footage.  The plugin turns those detections into Indigo triggers with a 7-segment webhook URL:

```
http://<IndigoMacIP>:4556/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH/&MEMO/&PLATE
```

- `plateFound` trigger — fires on any detected plate
- `plateMatch` trigger — fires when the plate matches your watch list (exact / starts-with / contains, case-insensitive)
- Camera states `lastPlate`, `lastPlateConfidence`, `lastPlateTime` updated on every detection

See **[License Plate / ALPR](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/License-Plate-ALPR)** in the wiki.

---

## Requirements

| Item | Version |
|------|---------|
| Indigo | 2025.2 (macOS) |
| Blue Iris | 4 or 5 (Windows, on your LAN) |
| Network | Indigo Mac must reach BI's web server and RTSP ports |

---

## Documentation

All documentation is in the **[GitHub Wiki](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki)**:

| Page | Topic |
|------|-------|
| [Installation](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Installation) | Download, install, first-run setup |
| [Blue Iris Setup](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Blue-Iris-Setup) | Webhook URLs for BI alert settings |
| [Plugin Configuration](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Plugin-Configuration) | All plugin preference fields |
| [Device Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Device-Reference) | Every device type and its states |
| [Actions Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Actions-Reference) | Every action and its options |
| [Triggers Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Triggers-Reference) | Every trigger event and its config |
| [Animated Media](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Animated-Media) | WebP / GIF / HEIC / MP4 capture |
| [License Plate / ALPR](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/License-Plate-ALPR) | ALPR trigger setup and troubleshooting |
| [Changelog](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Changelog) | Version history |

---

## Current Release

**v1.3.55** — MP4 RTSP scaling, simplified action UI, bursty-stream fix, full wiki

See the [Changelog](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Changelog) for full version history.
