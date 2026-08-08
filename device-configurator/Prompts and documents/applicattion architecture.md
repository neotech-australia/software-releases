> this document describes data model and structure of the application

## Configuration profile
this is a data struct composed of:
- name: user-given name for each profile
- APPEUI
- APPKEY
- BAND
- MASK 
- UPLINKPERIOD
- GPSDECIMATIONFACTOR
meaning and values of these parameters are explained in `Serial Protocol.md`

user can add, edit and remove configuration profiles.
after the board is connected, user selects one of previously defined profiles and then the software configures the device with values of that profile.

profiles are saved in `profiles.json`, stored in the application data directory: next to the executable when bundled (PyInstaller), otherwise in the current working directory.

## Device parameters
when the PC sends `ATC+STARTCONFIG`, the device responds with a `KEY=VALUE` dump that includes the device read-only fields plus the same profile fields:
- DEVEUI (read only)
- APPEUI, APPKEY, BAND, MASK, UPLINKPERIOD, GPSDECIMATIONFACTOR
- HWSTATUS (read only)
these are shown in the Device frame (Configuration tab). BAND is displayed as a readable name (e.g. `EU868 - 868 MHz Europe (4)`).

## Sensor monitoring
after the board is connected, the app can run action commands (no config session required):
- `SAMPLETILT` — returns `tilt_x`, `tilt_y`; used in the Measurements tab.
- `FULLSAMPLE` — returns `tilt_x`, `tilt_y`, `compass_heading`, `temperature`, `battery_charge_percent`, `battery_voltage_v`; used to continuously poll the Measurements tab while it is open.
- `GPSFIX` — returns `latitude`, `longitude`, `altitude` (may take up to 60 seconds; progress bar in the GPS tab). May be aborted gracefully via `ABORTGPSFIX`.

sensor and GPS readings are displayed in the Device frame's Measurements and GPS tabs (the 3D board-orientation viewer consumes the live tilt readings).