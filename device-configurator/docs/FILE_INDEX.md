# Architecture Diagrams

## Layer Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS                                  │
│                                                              │
│   config-tool-gui          config-tool-cli                    │
│   (pyproject.toml:         (pyproject.toml:                   │
│    config_tool.gui.app:main)  config_tool.cli.main:main)     │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      GUI LAYER (customtkinter)                        │
│                                                                      │
│  ┌────────────┬───────────┬──────────┬───────────┬──────────────┐   │
│  │ app.py     │ profile_  │ profile_ │ com_      │ device_      │   │
│  │ (main      │ list.py   │ editor   │ selector  │ frame.py     │   │
│  │  window)   │ (cards)   │ .py      │ .py       │ (parameters) │   │
│  │            │           │ (modal)  │ (conn.)   │              │   │
│  └─────┬──────┴─────┬─────┴────┬────┴─────┬─────┴──────┬───────┘   │
│        │            │          │          │            │           │
│  ┌─────┴────────────┴──────────┴──────────┴────────────┴───────┐   │
│  │ log_window.py │ status_bar.py │ tooltip.py                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
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
│  │  • list_ports             │  │                              │     │
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
│  ├──────────────────────────┤  │  │  └────────────────────────────┘  │
│  │ Parser / Commands / Const │  │  └─────────────────────────────────┘
│  └──────────────────────────┘  │
└────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       MODELS LAYER                                    │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │ ConfigurationProfile         │  │ DeviceParameters              │  │
│  │  • name, APPEUI, APPKEY      │  │  • Same fields + DEVEUI,      │  │
│  │  • BAND, MASK, UPLINKPERIOD, │  │    HWSTATUS                   │  │
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
     │  Show params    │                      │                    │                  │
     │◄────────────────│                      │                    │                  │
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

## Dependency Graph (Module to Module)

```
                        ┌──────────────┐
                        │  cli/main.py │
                        └──┬───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
      ┌───────────────┐       ┌─────────────────┐
      │ controller/    │       │ controller/      │
      │ device_        │       │ profile_service  │
      │ controller    │       └───────┬─────────┘
      └───────┬───────┘               │
              │                       │
     ┌────────┼────────┐              │
     │        │        │              │
     ▼        ▼        │              ▼
┌────────┐ ┌─────────┐ │    ┌──────────────────┐
│ models │ │ protocol│ │    │ profiles/store.py │
│ /device│ │ /at_    │ │    └────────┬─────────┘
│ _state │ │ client  │ │             │
└────────┘ └──┬──────┘ │             │
              │        │             │
              ▼        │             ▼
       ┌────────────┐  │  ┌──────────────────────┐
       │ protocol/  │  │  │ models/profile.py     │
       │ parser,    │  │  └──────────┬───────────┘
       │ commands,  │  │             │
       │ constants, │  │             ▼
       │ transport  │  │  ┌──────────────────────┐
       └────────────┘  │  │ profiles/validation   │
                        │  └──────────────────────┘
                        │
                        └── (imports protocol constants)
```

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
│ + MASK: str      (4 hex, US915/AU915/CN470)         │
│ + UPLINKPERIOD: int  (seconds, default 1800)        │
│ + GPSDECIMATIONFACTOR: int (0=disabled, default 8)  │
├────────────────────────────────────────────────────┤
│ + validate() → calls per-field validators           │
│ + to_dict() → dict for JSON serialization           │
│ + from_dict(data) → class method for deserialization│
│ + writable_values() → dict of fields sent to device │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│                 DeviceParameters                    │
├────────────────────────────────────────────────────┤
│ + DEVEUI: str     (read from device)                │
│ + APPEUI: str     (read from device)                │
│ + APPKEY: str     (read from device)                │
│ + BAND: str       (read from device)                │
│ + MASK: str       (read from device)                │
│ + UPLINKPERIOD: str   (read from device)            │
│ + GPSDECIMATIONFACTOR: str (read from device)       │
│ + HWSTATUS: str   (read from device)                │
├────────────────────────────────────────────────────┤
│ + from_key_value_lines(lines) → parse device dump   │
│ + diff_writable(profile_values) → find changes      │
│ + get(key) / set(key, value)                        │
└────────────────────────────────────────────────────┘
```

---

## Key vs Prefix Mapping

```
┌──────────────┬─────────┬────────────┬────────────────────┐
│ Key          │ Prefix  │ Writable   │ In Profile         │
├──────────────┼─────────┼────────────┼────────────────────┤
│ DEVEUI       │ AT      │ No (R/O)   │ No                 │
│ APPEUI       │ AT      │ Yes        │ Yes                │
│ APPKEY       │ AT      │ Yes        │ Yes                │
│ BAND         │ AT      │ Yes        │ Yes                │
│ MASK         │ AT      │ Yes        │ Yes                │
│ UPLINKPERIOD │ ATC     │ Yes        │ Yes                │
│ GPSDECIMATION│ ATC     │ Yes        │ Yes                │
│ HWSTATUS     │ ATC     │ No (R/O)   │ No                 │
└──────────────┴─────────┴────────────┴────────────────────┘
```

---

## GUI Layout (Simplified)

```
┌─────────────────────────────────┐
│  ConfigToolApp (420×720)        │
│  ┌───────────────────────────┐  │
│  │   ProfileListFrame        │  │  ← upper half
│  │   ┌─ ProfileCard ──────┐  │  │
│  │   │ ☑ Profile Name   ⚙ │  │  │
│  │   │   APPEUI=...       │  │  │
│  │   └────────────────────┘  │  │
│  │   ┌─ ProfileCard ──────┐  │  │
│  │   │ ☐ Profile Name   ⚙ │  │  │
│  │   │   APPEUI=...       │  │  │
│  │   └────────────────────┘  │  │
│  │           [+ FAB]         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │   bottom_frame            │  │  ← lower half
│  │                           │  │
│  │   ┌── ComSelectorFrame ─┐ │  │  ← visible when disconnected
│  │   │  Port: [▼ COM3] [↻] │ │  │
│  │   │          [Connect]   │ │  │
│  │   └─────────────────────┘ │  │
│  │   ┌── DeviceFrame ──────┐ │  │  ← visible when connected
│  │   │  DevEUI: ...  [📋]  │ │  │
│  │   │  AppEUI: ...  [📋]  │ │  │
│  │   │  AppKey: ...  [📋]  │ │  │
│  │   │  Band: 4            │ │  │
│  │   │  Mask: 0000         │ │  │
│  │   │  Uplink: 1800       │ │  │
│  │   │  GPS Dec: 8         │ │  │
│  │   │  HW Status: 0       │ │  │
│  │   │  [Configure] [Disc] │ │  │
│  │   └─────────────────────┘ │  │
│  │  ┌── StatusBar ─────────┐ │  │
│  │  │  Ready        [Logs] │ │  │
│  │  └──────────────────────┘ │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
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