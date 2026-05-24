![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# Release v1.3.55

**Released:** May 2026  
**Minimum Indigo:** 2025.2  
**Download:** [BlueIris.indigoPlugin](https://github.com/Ghawken/IndigoPlugin-BlueIris/releases/tag/v1.3.55)

This is a major feature release covering all changes since **v1.3.20**.  It adds License Plate Recognition triggers, a completely overhauled MP4 recorder, five new trigger types, animated WebP and HEIC actions, enhanced logging, and a full documentation wiki.

---

## ⭐ Highlights

### License Plate Recognition (ALPR)

Blue Iris 5's ALPR engine can now drive Indigo triggers directly.

- **`plateFound`** — fires on any plate detection, regardless of which plate
- **`plateMatch`** — fires when the plate matches your personal watch list (exact / starts-with / contains, case-insensitive, dash/space normalised)
- New **camera device states** updated on every detection: `lastPlate`, `lastPlateConfidence`, `lastPlateTime`
- Two delivery paths: real-time via the 7-segment OnAlert webhook (`&MEMO`/`&PLATE`), and background via BI log polling — duplicates within ~10 s are suppressed

**New webhook URL format:**
```
http://<IndigoMacIP>:4556/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH/&MEMO/&PLATE
```

The existing 5-segment URL continues to work unchanged.

📖 [License Plate / ALPR wiki page](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/License-Plate-ALPR)

---

### Improved MP4 Recording

The **Create MP4 Video** action has been significantly hardened for real-world RTSP streams:

- **BI-side scaling** — the plugin appends `&h=<height>&isolate=1` to the RTSP URL; Blue Iris scales the stream at the server so ffmpeg receives a correctly-sized feed, eliminating encode back-pressure frame-dropping on slower Macs
- **Bursty stream fix** — `-thread_queue_size 512` (vs ffmpeg's default of 8) prevents silent frame drops when BI delivers H.264 frames in large TCP bursts
- **Simplified action UI** — fps / CRF / preset / profile / level knobs removed; output size is now controlled entirely by the Width field
- **3× Python timeout** — `max(60 s, duration × 3)` prevents hangs on slow or remote cameras while still allowing a slow stream to fully deliver
- **Dynamic RTSP socket timeout** — `max(30 s, duration × 2)` so a slow-but-live stream doesn't time out between frames
- **Copy-paste debug command** — when debug logging is on, the Indigo log emits the full ffmpeg command with `-loglevel verbose` substituted in, ready to paste into a terminal
- Default clip duration changed from 5 s → **15 s**

📖 [Animated Media wiki page](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Animated-Media)

---

### Five New Trigger Types (v1.3.24)

| Trigger | Event ID | Fires when… |
|---------|----------|-------------|
| BI Log Message | `logMessageTrigger` | BI publishes a log entry matching a category / text filter |
| AI Tag | `aiTagTrigger` | BI's AI engine tags an alert (person, vehicle, animal, plate, …) |
| Camera No Signal | `cameraNoSignalTrigger` | A camera loses its video signal |
| Software Update Available | `softwareUpdateTrigger` | BI reports a new software version |
| Disk Free Below Threshold | `diskFreeBelowTrigger` | Free disk space drops below a configurable GB threshold |

📖 [Triggers Reference wiki page](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Triggers-Reference)

---

### Animated WebP — Rewritten (v1.3.30+)

- **MJPEG parser rewrite:** separate SOI/EOI scan offsets so in-progress frames are not discarded; longer read timeout; content-type checking; surface fallback reasons in the log
- **Speed:** encoder method 4; O(n) buffer scanning; `minimize_size` dropped
- **Correct playback speed in iMessage:** per-frame durations set from real elapsed capture time; uniform durations emitted for maximum player compatibility
- **Concurrent worker safety:** unique per-call tmp filenames eliminate the race between simultaneous captures

📖 [Animated Media wiki page](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Animated-Media)

---

### Animated HEIC (v1.3.36)

New **Create Animated HEIC** action (`animateHeif`) — captures a single JPEG frame and encodes it as a HEIC file via [pillow-heif](https://github.com/bigcat88/pillow_heif) for Apple-ecosystem sharing.

---

### Full Documentation Wiki

The plugin now ships with a comprehensive GitHub wiki that auto-syncs on every push:

| Page | |
|------|-|
| [Home](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki) | Overview and quick navigation |
| [Installation](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Installation) | Download, install, first-run setup |
| [Blue Iris Setup](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Blue-Iris-Setup) | Webhook URLs for BI alert settings |
| [Plugin Configuration](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Plugin-Configuration) | All plugin preference fields |
| [Device Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Device-Reference) | Every device type and its states |
| [Actions Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Actions-Reference) | Every action and its options |
| [Triggers Reference](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Triggers-Reference) | Every trigger event and configuration |
| [Animated Media](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Animated-Media) | WebP / GIF / HEIC / MP4 capture details |
| [License Plate / ALPR](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/License-Plate-ALPR) | ALPR trigger setup and troubleshooting |
| [Changelog](https://github.com/Ghawken/IndigoPlugin-BlueIris/wiki/Changelog) | Full version history |

---

## Full Change List Since v1.3.20

### v1.3.55
- MP4: append `&h=<height>&isolate=1` to RTSP URL — BI scales stream at source
- MP4: `-thread_queue_size 512` to handle bursty H.264 TCP delivery without frame drops
- MP4: simplified action UI — removed fps / CRF / preset / profile / level fields
- MP4: copy-paste ffmpeg debug command logged with `-loglevel verbose`
- MP4: default capture duration 5 s → 15 s
- Sync-wiki GitHub Actions workflow — `wiki/` auto-pushed to GitHub wiki on every master push
- README completely rewritten with banner, wiki links, and feature overview
- Bugfix: doorbell alert path parsing corrected in ALPR webhook handler

### v1.3.50
- New triggers: `plateFound` (any plate) and `plateMatch` (plate matches watch list)
- 7-segment OnAlert webhook URL supports `&MEMO` (parsed for plate text) and `&PLATE` (bare ALPR macro)
- New camera states: `lastPlate`, `lastPlateConfidence`, `lastPlateTime`
- Log-poll fallback path for ALPR detections without an associated alert
- ~10 s deduplication window suppresses duplicate hits from webhook + log poll
- ALPR matching: case-insensitive, dash/space-insensitive; exact / starts-with / contains modes; optional camera filter and minimum-confidence threshold

### v1.3.45
- Fixed `KeyError` in `updatecamConfig` for cameras missing `ptzcycle`, `motion`, or `pause` keys in the BI API response

### v1.3.40
- MP4: re-encode mode is now the **default** (stream-copy remains available via checkbox)
- MP4: low-bitrate AAC mono audio track added (24 kbps, 16 kHz) so clips play with sound in Messages and Mail
- MP4: fixed `-f mp4` flag so the `.tmp` output filename is recognised correctly
- MP4: replaced deprecated `-stimeout` with `-timeout` for RTSP (modern ffmpeg rejected the old name)
- MP4: atomic tmp-file write then `os.replace()` so a partial encode never overwrites a good file
- MP4: log line includes thread name and active thread count for each worker
- MP4: 3× Python subprocess timeout (`max(60 s, duration × 3)`)

### v1.3.37 / v1.3.36
- WebP: per-frame durations set from real elapsed capture time — playback speed in iMessage now matches the original
- WebP: uniform per-frame durations for maximum compatibility across players
- WebP: unique per-call tmp filename eliminates race condition between concurrent camera captures
- HEIC: `animateHeif` action added — captures a single JPEG and encodes as HEIC via pillow-heif

### v1.3.31
- Startup logging expanded: Indigo server info probes (web URL, reflector URL, database path, license, time zone)
- macOS version helpers and emoji in startup log

### v1.3.30
- WebP MJPEG parser rewritten: separate SOI/EOI scan offsets so in-progress frames are not discarded
- WebP: longer stream read timeout; content-type validation; fallback reason surfaced in log
- WebP: encoder method 4; O(n) buffer scanning; `minimize_size` dropped for speed
- Reverted ffmpeg fast-path for WebP (bundled ffmpeg not guaranteed to include libwebp)

### v1.3.26 – v1.3.29
- `IndigoLogHandler` added — all Python `logging` output routed to the Indigo event log
- Separate file-level and Indigo-level debug verbosity controls
- `actionChangeMacro`: hardened `substitute(validateOnly=True)` to match the real Indigo contract
- `actionChangeMacro`: fixed `TypeError` caused by comparing string `blueirisserverVersion` to int
- `actionChangeMacro`: validate Indigo substitution tokens before calling BI

### v1.3.24 — Five New Trigger Types
- `logMessageTrigger` — fires on BI log messages by category (Any, Motion, AI Alerted, Alert Canceled, Connection, Web Request, Warning, Error) with optional text filter
- `aiTagTrigger` — fires when BI's AI engine tags an alert with a keyword (person, vehicle, animal, plate, …) with optional camera filter
- `cameraNoSignalTrigger` — fires when a camera loses its video signal
- `softwareUpdateTrigger` — fires once when BI first reports an available update
- `diskFreeBelowTrigger` — fires when free disk drops below a configurable GB threshold (supports drive-label filter)
- BI log-level constants hoisted to module scope; severity mapping corrected against BI HTTP Interface Manual
- `mem` / `memfree` server states correctly mapped to BI's `memphys` / `mem` API fields

### v1.3.21
- Fixed P0/P1 bugs identified against the BI HTTP Interface manual
- Corrected `mem` (physical) vs `memfree` (free) server state mapping

---

## Upgrade Notes

- **No breaking changes** — all existing devices, triggers, and action groups are preserved on upgrade
- If you use the MP4 action: the fps / CRF / preset / profile / level fields have been removed from the action dialog; output size is now set via the Width field and applied at the BI RTSP source using `&h=`
- For ALPR triggers: update your BI webhook URL to the 7-segment form to enable real-time plate delivery; the 5-segment URL continues to work for all other triggers

---

## Screenshots

![Plugin configuration](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/PlugConfig1.png)

![Available triggers](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/BITriggers.png)

![Camera device states](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/BICameraStates.png)

![Available actions](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/ActionOptions.png)
