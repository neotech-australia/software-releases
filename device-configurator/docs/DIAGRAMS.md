# Architecture Diagrams

Visual diagrams for the current architecture. For narrative descriptions, see `ARCHITECTURE.md`; for a per-file reference, see `FILE_INDEX.md`.

---

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                                  │
│                                                                      │
│   config-tool-gui          config-tool-cli                           │
│   (pyproject.toml:         (pyproject.toml:                          │
│    config_tool.gui.app:main)  config_tool.cli.main:main)             │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      GUI LAYER (customtkinter)                        │
│                                                                      │
│  ┌────────────┬───────────┬──────────┬───────────┬──────────────┐   │
│  │ app.py     │ profile_  │ profile_ │ com_      │ device_      │   │
│  │ (main      │ list.py   │ editor   │ selector  │ frame.py     │   │
│  │  window)   │ (cards)   │ .py      │ .py       │ (4 tabs)     │   │
│  └─────┬──────┴─────┬─────┴────┬────┴─────┬─────┴──────┬───────┘   │
│        │            │          │          │            │           │
│  ┌─────┴────────────┴──────────┴──────────┴────────────┴───────┐   │
│  │ log_window.py │ status_bar.py │ tooltip.py │ theme.py        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  │ info_panel.py (right column)   board_3d_viewer.py (daemon)      │  │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │  calls controller methods
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    CONTROLLER LAYER                                   │
│                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐     │
│  │ DeviceController          │  │ ProfileService               │     │
│  │  • connect/disconnect     │  │  • list/add/update/delete    │     │
│  │  • read_device            │  │  • set_active/get_active     │     │
│  │  • apply_profile          │  │  • import/export             │     │
│  │  • abort/abort_gps_fix    │  │                              │     │
│  │  • sample_tilt/gps_fix/   │  │                              │     │
│  │    full_sample            │  │                              │     │
│  └───────────┬───────────────┘  └──────────────┬───────────────┘     │
│              │                                 │                     │
└──────────────┼─────────────────────────────────┼─────────────────────┘
               │                                 │
               ▼                                 ▼
┌────────────────────────────────┐  ┌─────────────────────────────────┐
│      PROTOCOL LAYER             │  │   PROFILE / STORE LAYER         │
│                                 │  │                                 │
│  ┌──────────────────────────┐  │  │  ┌───────────────────────────┐  │
│  │ Transport (ABC)           │  │  │  │ ProfileStore              │  │
│  │  ├─ SerialTransport       │  │  │  │  • JSON persistence       │  │
│  │  └─ MockTransport         │  │  │  │  • profiles.json          │  │
│  ├──────────────────────────┤  │  │  └──────────┬────────────────┘  │
│  │ AtClient                  │  │  │             │                   │
│  │  • start_config           │  │  │  ┌──────────▼────────────────┐  │
│  │  • write_parameter        │  │  │  │ Validation                 │  │
│  │  • read_parameter         │  │  │  │  • appeui, appkey, band   │  │
│  │  • config_done            │  │  │  │  • mask, uplink, gps      │  │
│  │  • run_action / drain     │  │  │  └────────────────────────────┘  │
│  │  • sample_tilt / gps_fix /│  │  └─────────────────────────────────┘
│  │    abort_gps_fix /        │  │
│  │    full_sample            │  │
│  ├──────────────────────────┤  │
│  │ Parser / Commands /       │  │
│  │ Constants / Errors        │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       MODELS LAYER                                    │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │ ConfigurationProfile         │  │ DeviceParameters              │  │
│  │  • name, APPEUI, APPKEY,     │  │  • device fields + sensor +   │  │
│  │    BAND, MASK, UPLINKPERIOD, │  │    GPS fields                 │  │
│  │    GPSDECIMATIONFACTOR       │  │  • from_key_value_lines()     │  │
│  │  • validate(), to_dict()     │  │  • diff_writable()            │  │
│  └──────────────────────────────┘  └──────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Communication Flow: Connecting and Reading Device

```
┌──────────┐    ┌──────────────┐    ┌──────────────────┐    ┌─────────────┐    ┌──────────┐
│   User   │    │ ConfigToolApp│    │ DeviceController │    │   AtClient   │    │ Serial   │
│          │    │  (GUI/CLI)   │    │                  │    │              │    │ Transport│
└────┬─────┘    └──────┬───────┘    └────────┬─────────┘    └──────┬──────┘    └─────┬────┘
     │                 │                      │                    │                  │
     │ Click Connect   │                      │                    │                  │
     │────────────────►│                      │                    │                  │
     │                 │ connect(port)        │                    │                  │
     │                 │─────────────────────►│                    │                  │
     │                 │                      │ open()             │                  │
     │                 │                      │───────────────────────────────────────►│
     │                 │                      │                    │                  │
     │                 │ read_device()        │                    │                  │
     │                 │─────────────────────►│                    │                  │
     │                 │                      │ start_config()     │                  │
     │                 │                      │───────────────────►│                  │
     │                 │                      │                    │ write_line(      │
     │                 │                      │                    │  ATC+STARTCONFIG) │
     │                 │                      │                    │─────────────────►│
     │                 │                      │                    │                  │
     │                 │                      │                    │ read_line() × N  │
     │                 │                      │                    │◄─────────────────│
     │                 │                      │                    │  (dump lines)     │
     │                 │                      │                    │                  │
     │                 │                      │                    │ parse →          │
     │                 │                      │                    │ DeviceParameters │
     │                 │                      │◄───────────────────│                  │
     │                 │                      │                    │                  │
     │                 │◄─────────────────────│                    │                  │
     │                 │                      │                    │                  │
     │  Show params +  │                      │                    │                  │
     │  info panel     │                      │                    │                  │
     │◄────────────────│                      │                    │                  │
```

Cancel during connect:

```
User clicks Cancel (loading overlay)
  → ConfigToolApp._request_cancel()
    → DeviceController.abort()  [force-close transport]
    → blocking read_line() raises RuntimeError → caught by worker
    → worker sees cancel → disconnect() → _after_connect_cancelled()
```

---

## Communication Flow: Applying Profile

```
┌──────────┐    ┌──────────────┐    ┌──────────────────┐    ┌─────────────┐    ┌──────────┐
│   User   │    │ ConfigToolApp│    │ DeviceController │    │   AtClient   │    │ Serial   │
└────┬─────┘    └──────┬───────┘    └────────┬─────────┘    └──────┬──────┘    └─────┬────┘
     │                 │                      │                    │                  │
     │ Click Configure │                      │                    │                  │
     │────────────────►│                      │                    │                  │
     │                 │ apply_profile        │                    │                  │
     │                 │─────────────────────►│                    │                  │
     │                 │                      │ profile.validate() │                  │
     │                 │                      │                    │                  │
     │                 │                      │ start_config()     │                  │
     │                 │                      │ (if not in session)│                  │
     │                 │                      │───────────────────►│                  │
     │                 │                      │                    │  → → → dump      │
     │                 │                      │◄───────────────────│                  │
     │                 │                      │                    │                  │
     │                 │                      │ diff_writable()    │                  │
     │                 │                      │ if no changes →    │                  │
     │                 │                      │   config_done,     │                  │
     │                 │                      │   "already matches"│                  │
     │                 │                      │ for each change:   │                  │
     │                 │                      │ write_parameter(   │                  │
     │                 │                      │   key, value)      │                  │
     │                 │                      │───────────────────►│─────────────────►│
     │                 │                      │                    │ write_line()     │
     │                 │                      │                    │ (AT+KEY=VALUE)   │
     │                 │                      │                    │                  │
     │                 │                      │                    │← "OK" ──────────│
     │                 │                      │                    │                  │
     │                 │                      │ config_done()      │                  │
     │                 │                      │───────────────────►│─────────────────►│
     │                 │                      │                    │ ATC+CONFIGDONE   │
     │                 │                      │                    │                  │
     │                 │                      │                    │← "OK" ──────────│
     │                 │                      │◄───────────────────│                  │
     │                 │◄─────────────────────│                    │                  │
     │                 │                      │  ApplyResult       │                  │
     │  Show result    │                      │                    │                  │
     │◄────────────────│                      │                    │                  │
```

---

## Communication Flow: Sensor Polling (Measurements tab)

```
┌──────────┐   ┌──────────────┐   ┌──────────────────┐   ┌─────────────┐   ┌──────────┐
│  User     │   │ ConfigToolApp│   │ DeviceController │   │   AtClient   │   │ Serial   │
└────┬─────┘   └──────┬───────┘   └────────┬─────────┘   └──────┬──────┘   └─────┬────┘
     │                │                     │                   │                 │
     │ Switch to      │                     │                   │                 │
     │ Measurements   │                     │                   │                 │
     │ tab            │                     │                   │                 │
     │───────────────►│                     │                   │                 │
     │                │ start polling       │                   │                 │
     │                │ (daemon, every 100ms)│                  │                 │
     │                │ full_sample()       │                   │                 │
     │                │────────────────────►│                   │                 │
     │                │                     │ full_sample()     │                 │
     │                │                     │──────────────────►│                 │
     │                │                     │                   │ ATC+FULLSAMPLE   │
     │                │                     │                   │────────────────►│
     │                │                     │                   │                 │
     │                │                     │                   │← tilt_x, ...  ──│
     │                │                     │◄──────────────────│  battery_voltage_v│
     │                │◄────────────────────│                   │                 │
     │  update labels │                     │                   │                 │
     │  + push angles │                     │                   │                 │
     │◄───────────────│  to AngleSource     │                   │                 │
     │                │  for 3D viewer      │                   │                 │
     │                │                     │                   │                 │
     │ Switch away    │                     │                   │                 │
     │───────────────►│  stop polling       │                   │                 │
```

---

## Communication Flow: GPS Fix with Graceful Abort

```
┌──────────┐   ┌──────────────┐   ┌──────────────────┐   ┌─────────────┐   ┌──────────┐
│  User     │   │ ConfigToolApp│   │ DeviceController │   │   AtClient   │   │ Serial   │
└────┬─────┘   └──────┬───────┘   └────────┬─────────┘   └──────┬──────┘   └─────┬────┘
     │                │                     │                   │                 │
     │ Click Poll GPS │                     │                   │                 │
     │─► progress bar │                     │                   │                 │
     │                │ gps_fix()           │                   │                 │
     │                │────────────────────►│                   │                 │
     │                │                     │ gps_fix()         │                 │
     │                │                     │ (65s timeout)     │                 │
     │                │                     │──────────────────►│                 │
     │                │                     │                   │ ATC+GPSFIX       │
     │                │                     │                   │────────────────►│
     │                │                     │                   │                 │
     │                │                     │                   │← latitude, ... ─│
     │                │                     │◄──────────────────│                 │
     │                │                     │ drain() [clear    │                 │
     │                │                     │ leftover lines]   │                 │
     │                │◄────────────────────│                   │                 │
     │  show fix      │                     │                   │                 │
     │◄───────────────│  (or NO_GPS_FIX /   │                   │                 │
     │                │   NO_DATA error)    │                   │                 │
```

Cancellation path (graceful):

```
User clicks Cancel (or any conflicting action)
  → ConfigToolApp._cancel_gps_if_active()
    → DeviceController.abort_gps_fix()
      → AtClient.abort_gps_fix() → ATC+ABORTGPSFIX
      → pending gps_fix() reader completes with NO_GPS_FIX
    → AtClient.drain() busies the buffer
  → if abort_gps_fix() itself fails → DeviceController.abort() (force-close fallback)
```

---

## Dependency Graph (Module to Module)

```
                         ┌──────────────┐
                         │  cli/main.py │
                         └──┬───────────┘
       ┌────────────────────┴────────────────────┐
       │                                          │
       ▼                                          ▼
┌───────────────┐                       ┌─────────────────┐
│ controller/    │                       │ controller/      │
│ device_        │                       │ profile_service  │
│ controller    │                       └───────┬─────────┘
└───────┬───────┘                               │
        │                                       │
       ┌┼────────────────────────┐              │
       ││                        │              │
       ▼▼                        ▼              ▼
┌──────────┐   ┌──────────┐   ┌────────────┐  ┌──────────────────┐
│ models / │   │ protocol │   │ protocol / │  │ profiles/store.py │
│ device_  │   │ at_client│   │ transport, │  └────────┬─────────┘
│ state    │   └────┬─────┘   │ parser,    │           │
└──────────┘        │          │ commands,  │           ▼
                    │          │ constants  │  ┌──────────────────┐
                    │          └────────────┘  │ models/profile.py │
                    │                          └────────┬─────────┘
                    │                                   │
                    │                                   ▼
                    │                   ┌──────────────────────────┐
                    └──────────────────►│ profiles/validation.py   │
                                        │ (imports protocol const) │
                                        └──────────────────────────┘
```

GUI note: `config_tool/gui/app.py` reaches into `controller/device_controller.py` and `controller/profile_service.py` only. `info_panel.py` stands apart (imports only `theme`, `paths`, `__version__`, PIL). `board_3d_viewer.py` has no application imports. `battery_editor.py` is owned by `device_frame.py` and calls controller battery methods through the app.

---

## Profile Data Model

```
┌────────────────────────────────────────────────────┐
│                ConfigurationProfile                 │
├────────────────────────────────────────────────────┤
│ + id: str (UUID)                                    │
│ + name: str                                         │
│ + APPEUI: str    (16 hex chars)                     │
│ + APPKEY: str    (32 hex chars)                     │
│ + BAND: int      (0-12, EU868=4)                    │
│ + MASK: str      (4 hex, US915/AU915/LA915/CN470)   │
│ + UPLINKPERIOD: int  (seconds, default 1800)        │
│ + GPSDECIMATIONFACTOR: int (0=disabled, default 8)  │
├────────────────────────────────────────────────────┤
│ + validate() → calls per-field validators           │
│ + to_dict() → dict for JSON serialization           │
│ + from_dict(data) → class method for deserialization│
│ + writable_values() → dict of fields sent to device │
│ + create_profile() → factory helper                 │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│                 DeviceParameters                    │
├────────────────────────────────────────────────────┤
│ Device fields:                                      │
│ + DEVEUI: str     (read only)                       │
│ + APPEUI / APPKEY / BAND / MASK / UPLINKPERIOD      │
│ + GPSDECIMATIONFACTOR / HWSTATUS (read only)        │
│ Sensor fields (from FULLSAMPLE / SAMPLETILT):       │
│ + tilt_x / tilt_y: float                            │
│ + compass_heading: float                            │
│ + temperature: float                                │
│ + battery_charge_percent: int                       │
│ + battery_voltage_v: float                          │
│ Battery persistence fields (writable, from dump):   │
│ + BATTERYCHARGE: str   (percent, 0–100, writable)   │
│ + BATTERYCAPACITY: str (mAh, >0, writable)          │
│ Lifetime (derived, not stored on device):           │
│ + battery_lifetime_days: Optional[int]              │
│   (models/battery.py formula: charge-based drain)   │
│ GPS fields (from GPSFIX):                           │
│ + latitude / longitude: float                       │
│ + altitude: float                                   │
│ + ehpe: float / satellite_count: int                │
├────────────────────────────────────────────────────┤
│ + from_key_value_lines(lines) → parse device dump   │
│ + diff_writable(profile_values) → find changes      │
│ + as_dict() / get(key) / set(key, value)            │
└────────────────────────────────────────────────────┘
```

---

## Key vs Prefix Mapping

```
┌──────────────────┬─────────┬────────────┬────────────────────┐
│ Key              │ Prefix  │ Writable   │ In Profile         │
├──────────────────┼─────────┼────────────┼────────────────────┤
│ DEVEUI           │ AT      │ No (R/O)   │ No                 │
│ APPEUI           │ AT      │ Yes        │ Yes                │
│ APPKEY           │ AT      │ Yes        │ Yes                │
│ BAND             │ AT      │ Yes        │ Yes                │
│ MASK             │ AT      │ Yes        │ Yes                │
│ UPLINKPERIOD     │ ATC     │ Yes        │ Yes                │
│ GPSDECIMATIONFACTOR│ ATC    │ Yes        │ Yes                │
│ BATTERYCHARGE    │ ATC     │ Yes        │ No (battery tab)   │
│ BATTERYCAPACITY  │ ATC     │ Yes        │ No (battery tab)   │
│ HWSTATUS         │ ATC     │ No (R/O)   │ No                 │
├──────────────────┼─────────┼────────────┼────────────────────┤
│ Action keys (ATC, not writable, not in profile):            │
│ SAMPLETILT       │ ATC     │ No (action)│ No                 │
│ GPSFIX           │ ATC     │ No (action)│ No                 │
│ ABORTGPSFIX      │ ATC     │ No (action)│ No                 │
│ FULLSAMPLE       │ ATC     │ No (action)│ No                 │
└──────────────────┴─────────┴────────────┴────────────────────┘
```

BAND is displayed as a readable name using the `BAND_OPTIONS` / `BAND_BY_ID` tables in `constants.py` (`format_band_value()`), e.g. `EU868 - 868 MHz Europe (4)`. `BATTERYCHARGE` / `BATTERYCAPACITY` are writable ATC keys exposed on the **Battery** tab (not part of a configuration profile).

---

## GUI Layout (Simplified)

```
┌──────────────────────────────────────────────┐
│  ConfigToolApp (main window)                 │
│  ┌──────────────────────────┬─────────────┐  │
│  │  ProfileListFrame        │ InfoPanel   │  │  ← fixed-right column
│  │  ┌─ ProfileCard ──────┐  │  logo       │  │    (logo, device photo,
│  │  │ ☑ Profile Name   ⚙ │  │  photo      │  │     product, version,
│  │  │   APPEUI=...       │  │  status     │  │     status)
│  │  └────────────────────┘  │             │  │
│  │  ┌─ ProfileCard ──────┐  │             │  │
│  │  │ ☐ Profile Name   ⚙ │  │             │  │
│  │  │   APPEUI=...       │  │             │  │
│  │  └────────────────────┘  │             │  │
│  │          [+ FAB]         │             │  │
│  └──────────────────────────┴─────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  bottom_frame                          │  │  ← lower half
│  │                                        │  │
│  │  ┌── ComSelectorFrame ──────────────┐  │  │  ← when disconnected
│  │  │  Port: [▼ COM3] [↻]    [Connect] │  │  │
│  │  └──────────────────────────────────┘  │  │
│  │  ┌── DeviceFrame (tabs) ────────────┐  │  │  ← when connected
│  │  │ Configuration │ Measurements│GPS │  │  │
│  │  │      │ Battery                    │  │  │
│  │  │  ┌──────────────────────────────┐ │  │  │
│  │  │  │ DevEUI: ...  [📋]            │ │  │  │
│  │  │  │ AppEUI: ...  [📋]            │ │  │  │
│  │  │  │ AppKey: ...  [📋]            │ │  │  │
│  │  │  │ Band: EU868 (4)              │ │  │  │  ← readable band
│  │  │  │ Mask: 0000                   │ │  │  │
│  │  │  │ Uplink: 1800                 │ │  │  │
│  │  │  │ GPS Dec: 8                   │ │  │  │
│  │  │  │ HW Status: 0                 │ │  │  │
│  │  │  └──────────────────────────────┘ │  │  │
│  │  │  [Configure] [Disconnect]         │  │  │
│  │  └──────────────────────────────────┘  │  │
│  │  ┌── StatusBar ─────────────────────┐  │  │
│  │  │  Ready                    [Logs] │  │  │
│  │  └──────────────────────────────────┘  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘

Measurements tab:  Tilt X, Tilt Y, Temperature, Compass Heading + [3D View]
GPS tab:           Latitude, Longitude, Altitude + [Poll GPS Fix] (progress bar)
Battery tab:       Remaining Charge (%) + ✎ | Estimated Lifetime (days)
                   Battery Voltage (V) | Battery Capacity (mAh) + ✎
                   (✎ = opens BatteryEditorWindow to read/change value)
```

---

## Async Execution Pattern

```
┌──────────┐        ┌─────────────┐        ┌─────────────┐
│   Main   │        │  Background  │        │   Device    │
│  Thread  │        │   Thread     │        │             │
│ (UI)     │        │ (daemon)     │        │ (COM port)  │
└────┬─────┘        └──────┬───────┘        └──────┬──────┘
     │                     │                        │
     │ _run_async(func)    │                        │
     │ set_busy(True)      │                        │
     │────────────────────►│                        │
     │                     │ func(*args)            │
     │                     │───────────────────────►│
     │                     │                        │
     │                     │◄───────────────────────│
     │                     │                        │
     │ after(0,            │                        │
     │   _clear_busy)      │                        │
     │◄────────────────────│                        │
     │                     │                        │
     │ after(0,            │                        │
     │   UI_update)        │                        │
     │ (from worker)       │                        │
```

The `_run_async()` method spawns a daemon thread. Blocking serial I/O runs in the thread. UI updates are scheduled on the main thread via `self.after(0, callback)`. The `_busy` flag prevents concurrent operations, and `set_busy(True)` disables all interactive widgets during I/O.

**Action guarding:** operations that would conflict with an in-progress GPS poll first call `_cancel_gps_if_active()` (graceful `ABORTGPSFIX`, falling back to `abort()`), then proceed. Battery edits from the Battery tab follow the same `_run_async` pattern (a daemon thread calls `read_battery_value` / `write_battery_value`, then updates the UI via `after(0, ...)`).

---

## AT Command Protocol Sequence

```
PC                                        Device
│                                           │
│  ATC+STARTCONFIG\r\n                      │
│ ───────────────────────────────────────►  │
│                                           │
│  DEVEUI=AC1F09FFFE12AB34                  │
│  APPEUI=0000000000000001                  │
│  APPKEY=2B7E151628AED2A6ABF7158809CF4F3C  │
│  BAND=4                                   │
│  MASK=0000                                │
│  UPLINKPERIOD=1800                        │
│  GPSDECIMATIONFACTOR=8                    │
│  BATTERYCHARGE=85                         │
│  BATTERYCAPACITY=1900                     │
│  HWSTATUS=0                               │
│  OK                                       │
│ ◄───────────────────────────────────────  │
│                                           │
│  AT+APPEUI=0000000000000002\r\n           │  (write changed params)
│ ───────────────────────────────────────►  │
│  OK                                       │
│ ◄───────────────────────────────────────  │
│                                           │
│  ATC+CONFIGDONE\r\n                       │
│ ───────────────────────────────────────►  │
│  OK                                       │
│ ◄───────────────────────────────────────  │

Action commands (no config session required):

  ATC+SAMPLETILT\r\n
    → tilt_x=... / tilt_y=...  or  INCLINATION_SENSOR_ERROR

  ATC+FULLSAMPLE\r\n
    → tilt_x, tilt_y, compass_heading, temperature,
      battery_charge_percent, battery_voltage_v  (any may be INVALID)

  ATC+GPSFIX\r\n   (up to 60s)
    → latitude / longitude / altitude
      or NO_GPS_FIX / NO_DATA_FROM_GPS_MODULE

  ATC+ABORTGPSFIX\r\n
    → OK  (cancels pending GPSFIX)

Battery parameters (reported in dump; read/write outside config session):

  ATC+BATTERYCHARGE=?\r\n
    → ATC+BATTERYCHARGE=<percent> + OK     (read remaining charge %)
  ATC+BATTERYCHARGE=<percent>\r\n           (e.g. 100 after a fresh battery)
    → OK

  ATC+BATTERYCAPACITY=?\r\n
    → ATC+BATTERYCAPACITY=<mAh> + OK       (read total capacity)
  ATC+BATTERYCAPACITY=<mAh>\r\n             (e.g. 1900 after a battery swap)
    → OK