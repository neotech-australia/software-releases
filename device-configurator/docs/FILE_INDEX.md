# File Index

This document lists every source file in the codebase, its role, and how it relates to the rest of the application. See `ARCHITECTURE.md` for a narrative overview and `DIAGRAMS.md` for visual diagrams.

---

## Root Files

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, and entry points (`config-tool-gui`, `config-tool-cli`). |
| `config-tool.spec` | PyInstaller spec for packaging the GUI as a standalone executable. |
| `build.bat` | Windows build script driving PyInstaller. |
| `README.md` | User-facing readme. |

---

## Configuration Package (`src/config_tool/`)

### Entry Points

| File | Purpose |
|------|---------|
| `config_tool/gui/app.py` | GUI entry point (`main()`). Defines `ConfigToolApp` — the main window that owns the controller, profile service, and all frames. |
| `config_tool/cli/main.py` | CLI entry point (`main()`). Argparse subcommands: `profiles`, `ports`, `connect`. |

### Package Root

| File | Purpose |
|------|---------|
| `config_tool/__init__.py` | Package init; exports `__version__`. |
| `config_tool/logging_config.py` | Centralized logging: RotatingFileHandler + StreamHandler + MemoryLogHandler (in-memory deque shown in the GUI log window). |
| `config_tool/paths.py` | Resolves the application data directory (next to frozen executable when bundled, else CWD) and `get_assets_dir()` for UI assets. |

---

## GUI Layer (`config_tool/gui/`)

| File | Purpose |
|------|---------|
| `app.py` | `ConfigToolApp` main window. Owns `DeviceController` + `ProfileService`. Async I/O, loading overlay with cancel, info column, 3D viewer launch, GPS polling. |
| `theme.py` | Shared Neotech branding: deep-navy palette, `apply_global_theme()`, `primary_button()` / `secondary_button()` / `danger_button()` kwarg helpers. |
| `info_panel.py` | Right-hand fixed-width company/device info column (logo, device photo, product name, version, status). Depends only on `theme`, `paths`, `__version__`, PIL. |
| `profile_list.py` | Scrollable list of profile cards + floating Add (FAB) button. Each card: active checkbox, name/APPEUI, gear edit button. |
| `profile_editor.py` | Modal popup for creating/editing profiles. Fields for all 7 profile attributes; Save/Cancel/Import/Export/Delete buttons. |
| `com_selector.py` | COM port dropdown + Refresh + Connect buttons. |
| `device_frame.py` | Connected-device view with 4 tabs: Configuration (params + copy), Measurements (sensors + 3D View), GPS (fix + Poll GPS Fix), Battery (charge + ✎, estimated lifetime, voltage, capacity + ✎). |
| `battery_editor.py` | Modal popup (`BatteryEditorWindow`) to read/change `BATTERYCHARGE` / `BATTERYCAPACITY` on the device. Shows when-to-edit instructions; brief version shown as tooltip. |
| `board_3d_viewer.py` | Standalone VPython 3D board orientation viewer. `AngleSource` thread-safe angle container; runs in a daemon thread. No app imports. |
| `status_bar.py` | Bottom status message + Logs button. |
| `log_window.py` | Toplevel window rendering the in-memory log buffer. |
| `tooltip.py` | Hover tooltip utility for widgets. |

---

## Controller Layer (`config_tool/controller/`)

| File | Purpose |
|------|---------|
| `device_controller.py` | `DeviceController` — transport lifecycle, `read_device()`, `apply_profile()`, `abort()`, `abort_gps_fix()`, `sample_tilt()`, `gps_fix()`, `full_sample()`, `read_battery_value()`, `write_battery_value()`, `disconnect()`. Exposes `at_client`, `device_state`, `is_connected`, `connected_port`. |
| `profile_service.py` | `ProfileService` — thin wrapper over `ProfileStore` (CRUD, active profile, import/export). |

---

## Models (`config_tool/models/`)

| File | Purpose |
|------|---------|
| `profile.py` | `ConfigurationProfile` dataclass (name, APPEUI, APPKEY, BAND, MASK, UPLINKPERIOD, GPSDECIMATIONFACTOR, id). `validate()`, `to_dict()`, `from_dict()`, `writable_values()`, `create_profile()`. |
| `device_state.py` | `DeviceParameters` dataclass with all device + sensor + GPS fields plus `BATTERYCHARGE` / `BATTERYCAPACITY` persistence fields and `battery_lifetime_days` (derived). `from_key_value_lines()`, `diff_writable()`, `as_dict()`, `get()`/`set()`. |
| `battery.py` | Battery lifetime estimator. `estimate_battery_lifetime_days(charge_pct, capacity_mah, uplink_period, gps_decimation)` — charge-based drain model (GPS acquisition + sensor sampling per uplink). |

---

## Profiles / Store (`config_tool/profiles/`)

| File | Purpose |
|------|---------|
| `store.py` | `ProfileStore` — loads/saves `profiles.json` (`active_profile_id` + `profiles`). CRUD with uniqueness checks, import/export. Raises `ProfileNotFoundError`. |
| `validation.py` | Field validators: `validate_appeui`, `validate_appkey`, `validate_band`, `validate_mask`, `validate_uplink_period`, `validate_gps_decimation_factor`, `validate_profile_name`. Raises `ValidationError`. |

---

## Protocol Layer (`config_tool/protocol/`)

| File | Purpose |
|------|---------|
| `serial_transport.py` | `Transport` ABC + `SerialTransport` (pyserial, 115200 8N1). `read_line()` raises `TimeoutError`. `list_serial_ports()`. |
| `mock_transport.py` | `MockTransport` for offline testing — scriptable responses to config dump (incl. BATTERYCHARGE/BATTERYCAPACITY), writes, action commands (SAMPLETILT, GPSFIX, FULLSAMPLE, ABORTGPSFIX). |
| `at_client.py` | `AtClient` — high-level protocol client: `start_config()`, `write_parameter()`, `read_parameter()`, `config_done()`, `run_action()`, `drain()`, `sample_tilt()`, `gps_fix()`, `abort_gps_fix()`, `full_sample()`, `read_battery_charge()`/`write_battery_charge()`, `read_battery_capacity()`/`write_battery_capacity()`, `ensure_config_done()`. |
| `commands.py` | String builders: `build_write_command`, `build_read_command`, `build_start_config`, `build_config_done`, `build_action_command`. Prefix resolution (`AT` vs `ATC`). |
| `parser.py` | Response parsing: `parse_dump_lines`, `parse_echo_value`, `is_ok_line`, `is_error_line`, `is_device_log_line`, `is_ignorable_line`, `prefix_for_key`. Exceptions: `AtResponseError`, `TimeoutError`, `ProtocolError`. `ACTION_ERROR_LINES`. |
| `constants.py` | Protocol constants: `LINE_ENDING`, `BAUD_RATE`, key sets (BUILTIN_KEYS, CUSTOM_KEYS incl. SAMPLETILT/GPSFIX/FULLSAMPLE/ABORTGPSFIX/BATTERYCHARGE/BATTERYCAPACITY, WRITABLE_KEYS incl. BATTERYCHARGE/BATTERYCAPACITY, PROFILE_KEYS, DEVICE_DUMP_KEYS incl. BATTERYCHARGE/BATTERYCAPACITY), `MASK_APPLICABLE_BANDS`, `AT_OK`, `AT_ERRORS`, timeouts. Also `BAND_OPTIONS`/`BAND_BY_ID` + `format_band_option()`/`format_band_value()`. |
| `errors.py` | Human-readable message map for AT error codes. |

---

## Tests (`tests/`)

Flat unit-test files at the top level of `tests/`:

| File | Covers |
|------|--------|
| `test_parser.py` | Protocol response parsing. |
| `test_at_client_mock.py` | `AtClient` driven over the mock transport. |
| `test_profile_store.py` | `ProfileStore` CRUD + import/export. |
| `test_validation.py` | Profile field validators. |
| `test_battery.py` | Battery lifetime estimator + device-state BATTERYCHARGE/BATTERYCAPACITY parsing. |
