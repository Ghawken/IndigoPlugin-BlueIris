![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# Animated Media

The plugin can capture live camera footage and save it as animated image or video files.

![Animated GIF example frames](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/AnimatedGifImages.png)

| Format | Action | Engine | Best For |
|--------|--------|--------|----------|
| **Animated WebP** | Create Animated WebP Image | pillow / MJPEG stream | iMessage, web pages |
| **Animated GIF** | Create Animated Gif | gifsicle (bundled) | Email, broad compatibility |
| **HEIC / HEIF still** | Create Animated HEIC | pillow-heif | Apple ecosystem (single frame) |
| **MP4 video** | Create MP4 Video | ffmpeg (bundled) | Video, iMessage, highest quality |

All outputs are written to `<saveDir>/<cameraShortName>/Animated.<ext>` by default (MP4 also supports a custom output path).

---

## Animated WebP

**Action:** `makewebP`

Captures frames from the camera's MJPEG HTTP stream, then encodes them into an animated WebP file using [Pillow](https://pillow.readthedocs.io/).  Frames are captured at approximately the camera's native rate; the WebP duration metadata is set from the real elapsed time so playback speed matches the original.

**Options:**

| Field | Default | Description |
|-------|---------|-------------|
| Camera(s) | — | One or more BlueIris Camera devices |
| Duration | `5` | How many seconds to capture (1–60) |
| Width (px) | `720` | Output width; height is auto-scaled |
| Quality | `80` | WebP encoder quality (1–100; 80 is a good balance) |
| Use Stream | on | Pull frames from the MJPEG stream; if off, falls back to repeated JPEG snapshots |

**Sending via iMessage (AppleScript):**
```applescript
delay 6  -- wait for the ~5s capture + encode
tell application "Messages"
    set myid to get id of first service
    set theBuddy to buddy "recipient@example.com" of service "E:sender@example.com"
    send POSIX file "/Users/yourname/Documents/Indigo-BlueIris/FrontDoor/Animated.webp" to theBuddy
end tell
```

---

## Animated GIF

**Action:** `makeAnim`

Captures JPEG snapshots at regular intervals, converts them to GIF frames using macOS `sips`, then packages them with the bundled [gifsicle](https://www.lcdf.org/gifsicle/) binary.

![Create animated GIF action UI](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/Action-CreateAnimGif.png)

**Options:**

| Field | Default | Description |
|-------|---------|-------------|
| Camera(s) | — | One or more BlueIris Camera devices |
| Duration | `5` | Capture duration in seconds |
| Width (px) | `720` | Output width |
| Compression | `10` | gifsicle optimisation level (1–10) |
| Frame count | `15` | Number of frames to capture |

**Sending via iMessage (AppleScript):**
```applescript
delay 6
tell application "Messages"
    set myid to get id of first service
    set theBuddy to buddy "recipient@example.com" of service "E:sender@example.com"
    send POSIX file "/Users/yourname/Documents/Indigo-BlueIris/FrontDoor/Animated.gif" to theBuddy
end tell
```

---

## HEIC / HEIF Still

**Action:** `animateHeif` (UI label: "Create Animated HEIC")

Captures a single JPEG frame and encodes it as a HEIC file using [pillow-heif](https://github.com/bigcat88/pillow_heif).  Produces a **single still frame** in Apple's HEIC format.

Requires `pillow-heif` to be installed in the plugin's Packages folder.

---

## MP4 Video

**Action:** `animateMp4`

Records a clip directly from Blue Iris's RTSP H.264 substream (preferred) or MJPEG HTTP stream (fallback) using the bundled [ffmpeg](https://ffmpeg.org/) binary (from the `homekitlink_ffmpeg` package).

### Source Types

| Source | Stream URL | Notes |
|--------|-----------|-------|
| h264 | `rtsp://…/<cam>&stream=2&h=<height>&isolate=1` | Preferred — BI scales at source, `&isolate=1` dedicates a BI playback object |
| mjpeg | `http://<bi-ip>:<port>/mjpg/<cam>/video.mjpg` | Fallback for cameras without a clean H.264 substream |

### BI RTSP Scaling (`&h=`)

When using the h264 source and re-encode mode, the plugin appends `&h=<height>` to the BI RTSP URL, where height is calculated from the **Output Width** setting assuming a 16:9 aspect ratio:

```
width=720  →  h=405  →  rtsp://…/<cam>&stream=2&h=405&isolate=1
width=1280 →  h=720  →  rtsp://…/<cam>&stream=2&h=720&isolate=1
```

Blue Iris scales the video at the server before it reaches the network, so ffmpeg receives a correctly-sized stream and doesn't need to scale it.  This dramatically reduces encode load and eliminates back-pressure frame-dropping on slower Macs.

`&w=` is not supported by BI's RTSP server — always use `&h=`.

`&isolate=1` dedicates a BI playback object to this connection, preventing it from sharing state with other RTSP clients.

### Encoding Modes

**Stream Copy** (ON): ffmpeg remuxes the incoming H.264 NAL units directly into an MP4 container without re-encoding.  Fastest option; resolution is whatever BI's default substream delivers (`&h=` is not applied in stream-copy mode).

**Re-encode** (OFF, default): ffmpeg transcodes with libx264 using fixed-quality defaults: `veryfast` preset, CRF 23, `main` profile, level 3.1.  Output size is controlled entirely by the **Output Width** field via `&h=` on the RTSP URL.

### Output File

Leave blank to use the default path:
```
<saveDir>/<cameraShortName>/Animated.mp4
```

Or provide a full path with optional Indigo substitutions:
```
/var/media/%%v:12345%%_camera.mp4
```

The file is written atomically — ffmpeg writes to a `.tmp` file first, then atomically renames to the final path on success.

### Timeout Behaviour (slow streams)

ffmpeg records for exactly `duration` seconds of **stream time**.  On slow WiFi or remote cameras the stream may deliver frames slower than real-time, meaning ffmpeg needs more wall-clock time to collect all the data.

The plugin uses a **3× timeout** — if `duration=15`, the plugin allows up to 45 seconds (minimum 60 s) of wall-clock time before killing ffmpeg.  The RTSP socket read timeout is set to `max(30 s, 2× duration)` so a slow stream that still delivers frames doesn't time out between individual frames.

The input packet queue is set to 512 slots (`-thread_queue_size 512`) to handle bursty TCP delivery from BI without silently dropping frames.

### Diagnosing RTSP Stream Problems

When debug logging is enabled, the plugin logs the full ffmpeg command in a copy-paste-ready form with `-loglevel verbose` already substituted in.  Copy the command from the Indigo log and paste it directly into a terminal to see full ffmpeg output:

```
MP4: copy-paste command:
/path/to/ffmpeg -hide_banner -loglevel verbose -nostdin -rtsp_transport tcp \
  -probesize 500000 -analyzeduration 5000000 -timeout 30000000 \
  -thread_queue_size 512 \
  -i rtsp://user:***@192.168.1.100:554/FrontDoor&stream=2&h=405&isolate=1 -t 15 ...
```

This is especially useful for diagnosing interrupted or dropped RTSP streams.

### Indigo Variable

On success the plugin sets (or creates) an Indigo variable named **`lastmp4`** with the full path to the saved file.

### Sending via iMessage (AppleScript)

```applescript
-- Wait for capture + encode.  For a 15s clip allow ~60s.
delay 20
tell application "Messages"
    set myid to get id of first service
    set theBuddy to buddy "recipient@example.com" of service "E:sender@example.com"
    send POSIX file "/Users/yourname/Documents/Indigo-BlueIris/FrontDoor/Animated.mp4" to theBuddy
end tell
```

---

## Automatic GIF on Motion

The **Enable Anim Gifs Enable/Disable** action (`CaptureAnim`) toggles whether the plugin automatically creates an animated GIF every time a camera is triggered.

![Enable animated GIF action](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/Action-EnableAnimGif.png)

This is separate from the manual `makeAnim` action above.
