![BlueIris Plugin](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/banner.png)

# License Plate Recognition (ALPR)

Blue Iris 5 includes an ALPR (Automatic License Plate Recognition) engine that can read plate text from camera footage.  Version 1.3.50 of the plugin adds full support for turning those detections into Indigo triggers.

---

## How Plate Data Reaches Indigo

Plate detections arrive via two independent paths — the plugin deduplicates hits that come from both sources within ~10 seconds.

### Path 1 — OnAlert Webhook (real-time)

When BI fires an alert with ALPR data, it calls the plugin's HTTP listener.  You must include the `&MEMO` and/or `&PLATE` segments in the alert URL:

```
http://<IndigoIP>:<port>/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH/&MEMO/&PLATE
```

- **`&PLATE`** — BI's dedicated ALPR macro; expands to the bare detected plate (e.g. `ABC123`).  This is the cleanest source.
- **`&MEMO`** — the full alert memo; the plugin scans it for `plate:ABC123 95%` or `Plate: ABC123 [95%]` patterns and extracts text + confidence.

If `&PLATE` delivers a bare plate text, that takes precedence over memo parsing.

### Path 2 — BI Server Log Poll (background)

The plugin polls BI's log endpoint periodically.  Log entries containing `plate:` or `Plate:` text are parsed and dispatched as plate-detected events.  This path catches detections that don't have an alert associated with them, but has a latency of one poll interval (typically ~30 seconds).

---

## Setting Up Webhooks

In each camera's BI alert settings, use the 7-segment URL:

```
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH/&MEMO/&PLATE
```

![BI v5 On Alert URL setup](https://raw.githubusercontent.com/Ghawken/IndigoPlugin-BlueIris/master/Images/BIOnAlert.png)

The 5-segment URL continues to work unchanged if you don't need ALPR:

```
http://192.168.1.6:4556/&CAM/&TYPE/&PROFILE/True/&ALERT_PATH
```

See [Blue Iris Setup](Blue-Iris-Setup.md) for full screenshots and instructions.

---

## Indigo Triggers

### plateFound — any plate detected

Fires on every plate detection, regardless of which plate it is.

```
Trigger type: Trigger when License Plate Detected (any plate)
```

**Useful for:** Logging all plates that pass by, recording a clip whenever any plate is seen.

**Configuration:**

| Field | Description |
|-------|-------------|
| Camera(s) | Limit to specific cameras (none = any) |
| Minimum confidence % | Only fire if ALPR confidence ≥ this value |

---

### plateMatch — specific plate(s) detected

Fires only when the detected plate matches one of your listed plates.

```
Trigger type: Trigger when License Plate Matches
```

**Useful for:** Recognising family cars, flagging known vehicles, opening a gate.

**Configuration:**

| Field | Description |
|-------|-------------|
| Plates | Comma/space-separated list: `ABC123, XYZ789` |
| Match mode | `exact` / `starts with` / `contains` |
| Camera(s) | Limit to specific cameras |
| Minimum confidence % | Confidence threshold |

**Matching rules:**
- Case-insensitive (`abc123 == ABC123`)
- Dashes and spaces ignored (`ABC-123 == ABC 123 == ABC123`)
- `exact` — full plate must match one entry
- `starts with` — plate begins with the entry
- `contains` — plate contains the entry anywhere

---

## Camera Device States

After any plate detection, these states are updated on the matching camera device:

| State | Type | Description |
|-------|------|-------------|
| `lastPlate` | string | Detected plate text (uppercase, normalised) |
| `lastPlateConfidence` | integer | Confidence percentage (0–100) |
| `lastPlateTime` | string | Timestamp of detection |

These states persist across triggers so you can always read the most recent plate for each camera.

---

## Example Action Group — Log Plate and Capture MP4

```
Trigger: plateFound (any camera, min confidence 60%)
Actions:
  1. Log "Plate detected: %%d:CAM_DEVICE_ID:lastPlate%% (%%d:CAM_DEVICE_ID:lastPlateConfidence%%%%)"
  2. Create MP4 Video (5s, front-door camera)
  3. Delay 20s
  4. Send iMessage with /path/to/Animated.mp4
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `plateFound` never fires | Webhook URL missing `&MEMO`/`&PLATE` segment | Update BI alert URL to 7-segment form |
| `plateMatch` fires for wrong plates | Dashes/spaces in your plate list | The plugin normalises both sides — `AB-CD 12` matches `ABCD12` |
| Low-confidence plates fire | `minConfidence` set to 0 | Set minimum confidence to 60–80% |
| Duplicate triggers | Both webhook and log poll deliver the same plate | Normal — deduplicated within ~10s window |
| `lastPlate` state blank | ALPR not configured in BI | Enable BI's AI / ALPR feature in camera settings |
