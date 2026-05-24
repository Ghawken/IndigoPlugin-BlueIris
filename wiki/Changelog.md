![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# Changelog

Major changes by version.  Full commit history is on [GitHub](https://github.com/Ghawken/IndigoPlugin-BlueIris).

---

## v1.3.55 — MP4 RTSP Scaling & Wiki  *(current)*

- **animateMp4 — BI-side RTSP scaling:** plugin now appends `&h=<height>&isolate=1` to the RTSP URL so Blue Iris scales the video stream at the server before it reaches ffmpeg — eliminates encode back-pressure frame dropping on slower Macs
- **animateMp4 — simplified action UI:** removed fps / CRF / preset / profile / level knobs; output size is controlled entirely via the Width field (height derived assuming 16:9 aspect ratio)
- **animateMp4 — bursty stream handling:** `-thread_queue_size 512` prevents silent frame drops when BI delivers H.264 frames in large TCP bursts
- **animateMp4 — copy-paste debug command:** Indigo log now emits the full ffmpeg command with `-loglevel verbose` substituted in, ready to paste into a terminal
- **Wiki:** comprehensive GitHub wiki added covering all features; GitHub Actions workflow syncs `wiki/` on every push to master
- **Bugfix:** ALPR doorbell alert path parsing corrected (backport from v1.3.50)

---

## v1.3.50 — License Plate / ALPR Triggers

- **New triggers:** `plateFound` (any plate) and `plateMatch` (plate matches a user-supplied list)
- **New webhook segment:** optional 7th URL segment `&PLATE` carries BI's dedicated ALPR macro directly; optional 6th segment `&MEMO` is parsed for `plate:ABC123 95%` / `Plate: ABC123 [95%]` patterns
- **New camera device states:** `lastPlate`, `lastPlateConfidence`, `lastPlateTime`
- ALPR plate matching is case- and dash/space-insensitive; supports `exact`, `starts-with`, and `contains` modes with optional camera filtering and minimum-confidence threshold
- Duplicate detections arriving via both webhook and log-poll paths within ~10 s fire only once
- The existing 5-segment OnAlert URL continues to work unchanged

---

## v1.3.45

- Fixes to PTZ cycle / motion / pause key handling in `updatecamConfig` (KeyError for missing keys)

---

## v1.3.40

- **animateMp4 improvements:**
  - Re-encode is now the **default** (was stream-copy)
  - Added low-bitrate AAC mono audio track (24 kbps, 16 kHz) to MP4 output so clips play with sound in Messages/Mail
  - Fixed `-f mp4` flag to correctly handle the `.tmp` output filename
  - Replaced deprecated `-stimeout` with `-timeout` for RTSP (modern ffmpeg rejected old name)
  - Added stream-copy checkbox (OFF by default) for users who want fast remux-only mode
  - Log now includes thread name and active thread count for each MP4 worker

---

## v1.3.37 / v1.3.36

- **animateWebp:** corrected per-frame duration encoding so animated WebP plays at the correct speed in iMessage (was playing too fast)
- **animateWebp:** emit uniform per-frame durations for better compatibility
- **animateWebp:** fix tmp-file race between concurrent workers (per-call unique tmp filename)
- **animateHeif:** emits a single still HEIC frame; UI label updated to match

---

## v1.3.31

- Init logging expanded: Indigo server info probes (web URL, reflector, DB, license, time zone)
- macOS version helpers and emoji in startup log

---

## v1.3.30

- **animateWebp MJPEG parser rewrite:** separate SOI/EOI scan offsets so in-progress frames are not discarded; longer read timeout; content-type check; fallback reason surfacing
- **animateWebp speed:** encoder method=4, dropped `minimize_size`, O(n) MJPEG buffer scanning
- Reverted ffmpeg fast-path for WebP (libwebp not always available in bundled ffmpeg)

---

## v1.3.29 / v1.3.28 / v1.3.27 / v1.3.26

- `actionChangeMacro`: simplified `substitute(validateOnly=True)` validation to match the real Indigo contract
- Hardened `substitute()` unpack so it doesn't raise TypeError on edge-case return values
- Fixed `TypeError` in `actionChangeMacro` by coercing `blueirisserverVersion` to `int` before comparison

---

## v1.3.26

- Added `IndigoLogHandler` so all Python `logging` output is routed to the Indigo event log
- Separate file-level and Indigo-level debug verbosity controls

---

## v1.3.24 (approx — Create MP4 Video initial release)

- **New action:** `animateMp4` — standalone ffmpeg-based MP4 encoder
- Pulls H.264 from BI's RTSP endpoint (`rtsp://…/<cam>&stream=2`) for stream-copy remux into MP4
- Bundled `homekitlink_ffmpeg` binary; no runtime encoder probing required
- Atomic tmp-file rename so a partial write never overwrites a good file
- `lastmp4` Indigo variable updated on success
- Per-camera background worker threads; concurrent camera captures are supported

---

## v1.3.0 — Animated WebP & HEIF

- Added `animateWebp` action — captures MJPEG stream frames and encodes an animated WebP via Pillow
- Added `animateHeif` action — captures a single JPEG and encodes as HEIC via pillow-heif
- HTTP listener replaces variable-subscription approach — no more `subscribeToVariables` dependency

---

## v0.6.0 — Built-in HTTP Server

- Plugin now runs its own HTTP server (default port `4556`) to receive BI webhooks
- Port is configurable in Plugin Config
- All cameras use the same URL format; no per-camera variable setup required
- Added `lastMotionTriggerType` camera state: `MOTION`, `AUDIO`, `EXTERNAL`, `WATCHDOG`, `TEST`
- Added `timelastMotion` state

---

## Earlier versions

- Initial release: BlueIris Server and Camera devices, motion triggers, PTZ actions, profile/macro change actions, animated GIF capture via `sips` + bundled `gifsicle`
