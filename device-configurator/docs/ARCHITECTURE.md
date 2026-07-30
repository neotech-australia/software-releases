# LoRaWAN Configuration Tool — Architecture Overview

## Purpose

Desktop utility for provisioning LoRaWAN IoT sensor devices over a COM port. The application reads device parameters and writes configuration profiles via an AT/ATC serial command protocol. It supports both a graphical interface (CustomTkinter) and a CLI interface, sharing a common controller layer.

In addition to provisioning, the tool supports **real-time sensor monitoring**: continuous tilt/acceleration polling with a **3D board orientation viewer** (VPython), GPS fix acquisition, and reading of environmental sensor data (temperature, compass heading, battery status).

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Entry Points                          │
│              config-tool-gui  │  config-tool-cli               │
└──────────────────────────────┘───────────────────────────────┘
              ▲                            │
              │                            │
──────────────┴────────────────────────────┴─────────────────────
                     Controller Layer
              ┌──────────────────────┐
              │   DeviceController    │
              │   ProfileService      │
              └──────┬─────────┬──────┘
                     │         │
              ┌──────┘         └──────┐
              ▼                       ▼
┌─────────────────────┐   ┌──────────────────────┐
│    Protocol Layer    │   │   Profile & Models    │
│  AtClient, Transport │   │  ProfileStore, Models │
│  Parser, Commands    │   │  Validation           │
└─────────────────────┘   └──────────────────────┘
```

The application has **four layers** and **two cross-cutting modules**:

| Layer / Module           | Responsibility                                                                 |
|--------------------------|--------------------------------------------------------------------------------|
| **GUI**                  | CustomTkinter windows, frames, user interaction, async UI updates, 3D viewer   |
| **CLI**                  | argparse-based command-line interface                                          |
| **Controller**           | Orchestrates device connection, profile application; contains business logic   |
| **Protocol**             | Raw serial communication, AT/ATC command building, response parsing            |
| **Models**               | Data classes for device state and profiles                                     |
| **Profiles (Store)**     | JSON persistence and validation of configuration profiles                      |

---

## Layer Responsibilities

### GUI (`config_tool/gui/`)

- **`app.py`** — Main application window (`ConfigToolApp`). Owns the `DeviceController` and `ProfileService`. Manages lifecycle: profile selection, connect/disconnect, configure, tilt polling, GPS polling. Runs blocking I/O in background threads, updates UI via `after()` callbacks. Includes a **loading overlay** with progress bar and cancel button during the connect phase.
- **`profile_list.py`** — Scrollable list of profile cards with a floating action button. Each card has a checkbox (active selection), name/APPEUI display, and a gear button (edit).
- **`profile_editor.py`** — Modal popup for creating/editing profiles. Fields for all 7 profile attributes. Buttons: Save, Cancel, Import, Export, Delete.
- **`com_selector.py`** — COM port dropdown with Refresh and Connect buttons.
- **`device_frame.py`** — Displays device parameters in a **tabbed interface** with three tabs:
  - **Configuration** — Standard device parameters (DevEUI, AppEUI, AppKey, Band, Mask, Uplink Period, GPS Decimation, HW Status). Copy buttons for EUI/Key fields. Configure and Disconnect buttons.
  - **Measurements** — Real-time sensor readings: Tilt X, Tilt Y, Temperature, Compass Heading. Includes a **"3D" button** to launch the 3D board orientation viewer.
  - **GPS** — GPS fix data: Longitude, Latitude, Altitude, EHPE, Satellite Count. Includes a **"Poll GPS Fix"** button with a determinate progress bar (up to 60 seconds) and Cancel button.
- **`board_3d_viewer.py`** — 3D board orientation viewer using **VPython**. Displays a cuboid representing the embedded board, rotated according to tilt_x (roll) and tilt_y (pitch) angles. Runs in a background daemon thread. Uses a thread-safe `AngleSource` object to receive live sensor data. Falls back to a gentle automated sweep when real data is stale (>2 seconds). Fully isolated from the rest of the application.
- **`status_bar.py`** — Bottom status message with a Logs button.
- **`log_window.py`** — Toplevel window showing in-memory log buffer.
- **`tooltip.py`** — Hover tooltip utility for widgets.

### CLI (`config_tool/cli/`)

- **`main.py`** — Single entry point with subcommands: `profiles` (list, add, edit, delete, set-active, import, export), `ports` (list COM ports), `connect` (read, apply, disconnect). Uses the same `DeviceController` and `ProfileService` as the GUI. Supports `--mock` flag for offline testing.

### Controller (`config_tool/controller/`)

- **`device_controller.py`** — `DeviceController` class. Manages transport lifecycle. `connect()` creates either `SerialTransport` or `MockTransport`. `read_device()` starts a config session and returns device parameters. `apply_profile()` diffs current device state against a profile, writes changed parameters, then ends the config session. Returns `ApplyResult`. New features:
  - `abort()` — Forcefully closes the transport without sending CONFIGDONE (used for cancel operations).
  - `sample_tilt()` — Delegates to `AtClient.sample_tilt()`.
  - `gps_fix()` — Delegates to `AtClient.gps_fix()` (may block up to 60 seconds).
  - `full_sample()` — Delegates to `AtClient.full_sample()`.
  - `at_client` property — Exposes the underlying `AtClient` instance.
- **`profile_service.py`** — `ProfileService` class. Thin wrapper around `ProfileStore` providing CRUD operations, active-profile management, import/export.

### Models (`config_tool/models/`)

- **`profile.py`** — `ConfigurationProfile` dataclass with fields: name, APPEUI, APPKEY, BAND, MASK, UPLINKPERIOD, GPSDECIMATIONFACTOR, id (UUID). Has `validate()` (calls validation functions), `to_dict()`, `from_dict()`, `writable_values()`.
- **`device_state.py`** — `DeviceParameters` dataclass with all device fields including DEVEUI, HWSTATUS, **and new sensor fields**: `tilt_x`, `tilt_y`, `compass_heading`, `temperature`, `battery_charge_percent`, `battery_voltage_v`, `latitude`, `longitude`, `altitude`, `ehpe`, `satellite_count`. Includes `from_key_value_lines()` (parses device dump), `diff_writable()` (compares against profile values), `get()`/`set()` methods.

### Protocol (`config_tool/protocol/`)

- **`serial_transport.py`** — Abstract `Transport` base class and `SerialTransport` implementation using `pyserial`. Config: 115200 baud, 8N1. `read_line()` handles timeouts by raising `TimeoutError`. `list_serial_ports()` utility.
- **`mock_transport.py`** — `MockTransport` implementation for offline testing. Scriptable: responds to ATC+STARTCONFIG with a parameter dump, processes write commands by updating internal state, emulates AT error responses. **Extended** to handle `ATC+SAMPLETILT`, `ATC+GPSFIX`, and `ATC+FULLSAMPLE` action commands with canned responses.
- **`at_client.py`** — `AtClient` class. High-level protocol client. `start_config()` sends ATC+STARTCONFIG, collects device dump lines until timeout or OK. `write_parameter()` writes a single parameter. `read_parameter()` reads a single parameter. `config_done()` sends ATC+CONFIGDONE. Ignores device debug log lines. New features:
  - `run_action(key)` — Generic action command execution: sends an action-only command (e.g., SAMPLETILT), collects KEY=VALUE result lines, returns a `DeviceParameters` object.
  - `sample_tilt()` — Sends ATC+SAMPLETILT, returns tilt readings.
  - `gps_fix()` — Sends ATC+GPSFIX with extended timeout (65s), returns GPS fix data.
  - `full_sample()` — Sends ATC+FULLSAMPLE, returns all sensor readings.
  - `ensure_config_done()` — Gracefully ends a config session if one is active, catching errors.
- **`commands.py`** — String builders: `build_write_command`, `build_read_command`, `build_start_config`, `build_config_done`, `build_action_command`. Determines `AT` vs `ATC` prefix per key.
- **`parser.py`** — Response parsing: `parse_dump_lines`, `parse_echo_value`, `is_ok_line`, `is_error_line`, `is_device_log_line`, `is_ignorable_line`, `prefix_for_key`. Defines `AtResponseError`, `TimeoutError`, `ProtocolError`. Includes `ACTION_ERROR_LINES` — special error result strings from action commands (INCLINATION_SENSOR_ERROR, NO_GPS_FIX, NO_DATA_FROM_GPS_MODULE).
- **`constants.py`** — All protocol constants: LINE_ENDING, BAUD_RATE, key sets (BUILTIN_KEYS, CUSTOM_KEYS includes SAMPLETILT/GPSFIX/FULLSAMPLE, WRITABLE_KEYS, PROFILE_KEYS, DEVICE_DUMP_KEYS), MASK_APPLICABLE_BANDS, AT_OK, AT_ERRORS, timeouts.
- **`errors.py`** — Human-readable error message map for AT error codes.

### Profiles / Store (`config_tool/profiles/`)

- **`store.py`** — `ProfileStore` class. Loads/saves `profiles.json` (JSON with `active_profile_id` and `profiles` array). CRUD operations with uniqueness checks. `import_profile()` and `export_profile()` for JSON file transfer.
- **`validation.py`** — Individual field validators: `validate_appeui` (16 hex), `validate_appkey` (32 hex), `validate_band` (0-12), `validate_mask` (4 hex, conditionally required per band), `validate_uplink_period`, `validate_gps_decimation_factor`, `validate_profile_name`. Raises `ValidationError`.

### Cross-Cutting

- **`logging_config.py`** — Centralized logging setup using RotatingFileHandler, StreamHandler, and a MemoryLogHandler (in-memory deque for GUI log window).
- **`paths.py`** — Resolves application data directory: next to frozen executable when bundled, else current working directory.

---

## Application Startup Flow

### GUI

```
pyproject.toml entry point → config_tool.gui.app:main
  └─ ctk.set_appearance_mode / set_default_color_theme
  └─ ConfigToolApp()
       ├─ ProfileService() → ProfileStore() → load profiles.json
       ├─ DeviceController(use_mock)
       ├─ ProfileListFrame()        [upper frame]
       ├─ ComSelectorFrame()        [bottom frame, initially visible]
       ├─ DeviceFrame()             [bottom frame, hidden initially]
       │    ├─ Tab "Configuration"  [device params + copy buttons]
       │    ├─ Tab "Measurements"   [sensor readings + 3D button]
       │    └─ Tab "GPS"            [GPS fields + Poll GPS Fix button]
       └─ StatusBar()              [bottom of bottom frame]
  └─ app.mainloop()
```

### CLI

```
pyproject.toml entry point → config_tool.cli.main:main
  └─ argparse parses subcommand
  └─ ProfileService() + DeviceController(use_mock)
  └─ Dispatch to _handle_profiles() or _handle_connect()
```

---

## Data Flow

### Reading Device Parameters

```
User clicks Connect
  → ComSelectorFrame._on_connect(port)
    → ConfigToolApp._on_connect(port) → _run_async(_connect_worker)
      → DeviceController.connect(port)
          → SerialTransport(port).open()
          → AtClient(transport)
      → DeviceController.read_device()
          → AtClient.start_config()
              → Transport.write_line("ATC+STARTCONFIG\r\n")
              → Transport.read_line() × N (collect key=value dump lines)
              → Parser: parse_dump_lines(lines) → DeviceParameters
          → returns DeviceParameters
      → ConfigToolApp._show_device_frame(params, port)
          → DeviceFrame.set_parameters(params)
          → switch ComSelectorFrame → DeviceFrame
```

### Applying Profile to Device

```
User clicks Configure
  → DeviceFrame._on_configure()
    → ConfigToolApp._on_configure()
      → get ProfileService.get_active()
      → _run_async(_configure_worker, profile)
        → DeviceController.apply_profile(profile)
            → profile.validate()
            → if not in session: AtClient.start_config()
            → DeviceParameters.diff_writable(profile.writable_values())
            → for each changed key:
                AtClient.write_parameter(key, value)
                  → Transport.write_line("AT+KEY=VALUE\r\n")
                  → read until "OK" or error
            → AtClient.config_done()
              → Transport.write_line("ATC+CONFIGDONE\r\n")
              → read until "OK"
            → returns ApplyResult
        → ConfigToolApp._configure_done(message, params, success)
```

### Polling Tilt / Sensor Data

```
DeviceFrame switches to "Measurements" tab
  → ConfigToolApp._on_tab_change("Measurements")
    → _start_tilt_polling()
      → daemon thread: _tilt_poll_worker()
        → every 100ms: DeviceController.sample_tilt()
          → AtClient.sample_tilt()
            → run_action("SAMPLETILT")
              → Transport.write_line("ATC+SAMPLETILT\r\n")
              → read tilt_x=tilt_y=... lines
          → returns DeviceParameters with tilt_x, tilt_y
        → after(0): DeviceFrame.set_parameters(params)
          → updates labels + pushes angles to AngleSource for 3D viewer

User switches away from "Measurements" tab
  → _stop_tilt_polling()
  → thread exits at next loop iteration
```

### GPS Fix Acquisition

```
User clicks "Poll GPS Fix" on GPS tab
  → DeviceFrame._on_gps_poll_click()
    → shows determinate progress bar (animates to fill over 60s)
    → ConfigToolApp._on_gps_poll()
      → _run_async(_gps_poll_worker)
        → DeviceController.gps_fix()
          → AtClient.gps_fix()
            → run_action("GPSFIX")  [timeout extended to 65s]
              → Transport.write_line("ATC+GPSFIX\r\n")
              → read latitude=longitude=... lines
          → returns DeviceParameters with GPS data
        → after(0): _gps_poll_done(params)
          → DeviceFrame.on_gps_poll_done() [hides progress bar]
          → DeviceFrame.set_parameters(params)

User clicks "Cancel" during GPS poll
  → DeviceFrame._cancel_gps_poll()
    → sets _gps_cancel_requested = True
    → ConfigToolApp._on_gps_cancel()
      → DeviceController.abort() [force-close transport]
```

### Profile CRUD Flow

```
GUI editor → ProfileEditorWindow._save()
  → ConfigToolApp._save_profile(profile)
    → ProfileService.update(profile) or store.add(profile)
      → ProfileStore.update() / add()
          → profile.validate()  [ValidationError if invalid]
          → save to profiles.json
    → refresh profile list
    → update status bar
```

---

## Event Flow (GUI)

| User Action                 | Source Widget          | Controller Callback          | Async Thread | UI Update Callback             |
|-----------------------------|------------------------|------------------------------|--------------|--------------------------------|
| Select profile              | ProfileCard checkbox   | `_on_profile_select`         | No           | `_refresh_profiles`, status    |
| Click Add (+) FAB           | ProfileListFrame FAB   | `_open_new_editor`           | No           | Open `ProfileEditorWindow`     |
| Click gear icon             | ProfileCard gear_btn   | `_open_editor`               | No           | Open `ProfileEditorWindow`     |
| Click Connect               | ComSelectorFrame       | `_on_connect`                | Yes (loading overlay with cancel) | `_show_device_frame` / error   |
| Click Configure             | DeviceFrame            | `_on_configure`              | Yes          | `_configure_done` / error      |
| Click Disconnect            | DeviceFrame            | `_on_disconnect`             | Yes          | `_show_com_selector`           |
| Switch to Measurements tab  | DeviceFrame TabView    | `_on_tab_change`             | No           | Start/stop tilt polling        |
| (Tilt poll loop)            | (background thread)    | `sample_tilt()`              | Yes (100ms)  | `set_parameters()`             |
| Click "3D" button           | DeviceFrame            | `_open_3d_viewer`            | Yes (daemon) | Launch VPython viewer thread   |
| Click "Poll GPS Fix"        | DeviceFrame GPS tab    | `_on_gps_poll`               | Yes          | Show progress bar, then results|
| Click Cancel (GPS)          | DeviceFrame GPS tab    | `_on_gps_cancel`             | Yes (abort)  | Hide progress bar              |
| Click Logs                  | StatusBar              | `_show_logs`                 | No           | Open/raise `LogWindow`         |
| Close main window           | ConfigToolApp          | `_on_close`                  | No           | Stop tilt polling, `disconnect()`, `destroy()` |

All I/O operations (connect, read, write, disconnect, GPS fix) run in daemon threads via `_run_async()`. UI is updated from those threads via `self.after(0, callback)`. The `_busy` flag prevents concurrent operations.

---

## 3D Board Orientation Viewer

Located in `config_tool/gui/board_3d_viewer.py`. Fully isolated module using VPython.

- **AngleSource** — Thread-safe container for tilt angles. `push()` called from the tilt polling thread, `pull()` called from the VPython thread each frame (30 fps).
- **_BoardViewer** — Owns the VPyton canvas, cuboid, and animation loop. Runs in a daemon thread. When real sensor data is stale (>2 seconds), falls back to a gentle sine-wave sweep.
- **launch()** — Public API: spawns the viewer in a daemon thread.
- **Signal monkey-patch** — VPython calls `signal.signal()` at import time, which crashes in non-main threads. The viewer patches `signal.signal` to a no-op before first import, safe for PyInstaller.

```
DeviceFrame (Measurements tab)
  → "3D" button → launch(angle_source)
    → daemon thread:
        → monkey-patch signal.signal
        → import vpython
        → build scene (canvas, cuboid, axes, ground ring, face dots)
        → loop at 30 fps:
            → AngleSource.pull() → tilt_x, tilt_y, age
            → if age < 2s: use real angles; else: fake sweep
            → apply pitch (Y) then roll (X) rotation to board
            → update scene title with current angles
```

---

## Async Pattern: Loading Overlay with Cancel

During the connect phase, a loading overlay with an indeterminate progress bar and Cancel button is displayed:

```
_on_connect(port)
  → _show_loading("Connecting to {port}…")
  → _run_async(_connect_worker)

User clicks "Cancel"
  → _request_cancel()
    → _cancel_requested = True
    → controller.abort()  [force-close serial port]
    → blocking read_line() raises RuntimeError → caught by _connect_worker
    → _connect_worker checks _cancel_requested → disconnect + _after_connect_cancelled
```

The abort mechanism is also used for GPS poll cancellation.

---

## Dependency Direction

```
GUI ──────► Controller ──────► Protocol
              │                    │
              │                    ├── serial_transport (pyserial)
              │                    ├── mock_transport
              │                    ├── at_client
              │                    ├── parser
              │                    ├── commands
              │                    └── constants
              │
              └─────► Models ◄───── Protocol
                         │
              ┌───────────┘
              ▼
    Profiles (Store & Validation)
              │
              └─────► Models (ConfigurationProfile)
                     Protocol (constants for MASK_APPLICABLE_BANDS)
```

**Rules:**
- **GUI → Controller → Models, Protocol:** GUI never accesses models or protocol directly. It calls controller methods and receives results.
- **Controller → Models + Protocol + Profiles:** Controller imports models for return types, protocol for transport/AtClient, profiles for ProfileStore.
- **Protocol → Models:** Parser imports `DeviceParameters`. AtClient imports `DeviceParameters`.
- **Profiles → Models + Protocol:** Store imports `ConfigurationProfile`. Validation imports protocol constants (`MASK_APPLICABLE_BANDS`).
- **Models → Profiles:** `ConfigurationProfile` imports validation functions.
- **No circular dependencies.** Models never import controllers or GUI. Protocol never imports controllers or GUI. CLI and GUI never import each other.
- **board_3d_viewer.py** has **no imports from the rest of the application** (only standard library + vpython). It communicates via the thread-safe `AngleSource` object.