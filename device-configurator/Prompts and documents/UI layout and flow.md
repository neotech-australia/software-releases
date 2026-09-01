# UI layout and structure

main application window is a wide rectangle composed of two columns: a main left column and a fixed-width info panel on the right. the main column is itself composed of two frames stacked vertically (upper half and bottom half).

## info panel (right column)

a fixed-width company/device column that shows the app logo, a device photo, the product name, the app version, and the connection status. it is populated with live device details after connecting.

## upper frame (left column):
list of configuration profiles in a scrollable frame with a `add` floating action button to add new profile.
- each profile is shown as a card (landscape rectangle with rounded corners)

### profile cards:
 shows profile's `name` in bold at top, bellow that is `APPEUI`. at left side of the card there is a check box, checking that, choses the profile as active, only one profile can be active at time. at right there is a gear icon. pressing that open `profile editor window` as a pop up window.

### profile editor window:
smaller pop up window where profile field can be modified.
bellow the window there are: save, cancel, import, export and delete bottoms.
selecting the `add` floating action button also opens a `profile editor window`

## bottom frame (left column):
used to connect/disconnect to device, see current values and parameters and also load selected profile config to the device.
this frame itself is two frames stacked on top plus a status bar:
- the initial one is used to select COM port and connect. lets call this `COM selector frame`
- then the other frame shows up that is used to config device, inspect parameters and disconnect. lets call this `device frame`
### COM selector frame
- shows list of available COM ports in a drop down menu
- has a refresh button to rescan ports and a `connect` button at right.

### device frame
- have a `disconnect` and `configure` buttons at bottom.
- device parameters are displayed in a tabbed interface with three tabs:

**Configuration tab** — device parameters including (DEVEUI, APPEUI, APPKEY, BAND, MASK, UPLINKPERIOD, GPSDECIMATIONFACTOR, HWSTATUS) are displayed. BAND and MASK share a row, UPLINKPERIOD and GPSDECIMATIONFACTOR share a row. BAND is shown as a readable name (e.g. `EU868 - 868 MHz Europe (4)`). in front of DEVEUI, APPEUI and APPKEY is a copy icon, pressing that copies the corresponding parameter value to clipboard.

**Measurements tab** — real-time sensor readings: Tilt X, Tilt Y, Temperature, Compass Heading. includes a `3D View` button that opens the 3D board-orientation viewer, which rotates a board model according to the live tilt readings.

**GPS tab** — GPS fix data: Longitude, Latitude, Altitude, plus EHPE and Satellite Count. includes a `Poll GPS Fix` button. after clicking, a determinate progress bar is shown under the fields (with a `Cancel` button) that animates over up to 30 seconds while the fix is acquired. when the fix completes, the fields are updated; if it fails, an error message is shown.

## status bar section
- error and result messages (connection failed, configured successfully etc) are displayed in a `status bar section` at bottom of the bottom frame.
- there is a small `logs` button on the right side of the `status bar section`. pressing that opens a log window that shows application logs.

## A few other notes
- during the connect phase, a loading overlay with a progress bar and a `Cancel` button is displayed; pressing cancel force-closes the transport and returns to the COM selector.
- closing application window sends a `CONFIGDONE` to device if a configuration session is active, and also cancels any in-progress GPS poll (sending `ABORTGPSFIX`).
- while a GPS poll is running, any conflicting action (disconnect, configure, close) first gracefully aborts the GPS fix via `ATC+ABORTGPSFIX`, falling back to a hard close if needed.
- error messages show a modal window with an ok button.