# UI layout and structure

main application window is composed of two frame(one in upper half of window and the other bottom half). the main window is portrate rectangle. 

## upper frame :
list of configuration profiles in a scrollable frame with a `add` floating action button to add new profile.
- each profile is shown as a card (landscape rectangle with rounded corners)

### profile cards:
 shows  profile's `name` in bold at top, bellow that is `APPEUI`.at left side of the card there is a check box, checking that, choses the profile as active, only one profile can be active at time. at right there is a gear icon. pressing that open `profile editor window` as a pop up window.

### profile editor window:
smaller pop up window where profile field can be modified. 
bellow the window there are: save, cancel, import, export and delete bottoms.
selecting the `add` floating action button also opens a `profile editor window`

## bottom frame:
used to connect/disconnect to device, see current values and parameter and also load selected profile config to the device.
this frame itselfe is two frame stacked on top:
- the initial one is used to select COM port and connect. lets call this `COM selector frame`
- then the other frame shows up that is used to config device, incpect parameters and disconnect. lets call this `device frame` 
### COM selector frame 
- shows list of avaiable COM ports in a drop down menu
- has a `connect` button at right. 
### device frame
- have a `disconnect` and `configure` buttons at bottom.
- device parameters including: (DEVEUI, APPEUI, APPKEY, BAND, MASk, UPLINKPERIOD, GPSDECIMATIONFACTOR, HWSTATUS) are displayed, in front of first three parameter are a copy icon, pressing that copies correspoding parameter value to clipboard.

## A few other notes
- error and result messages (connection failed, configed succeffuly etc) are display in a `statue bar section` at bottom of the bottom frame. 
- there is a small `logs` bottom in right side of `statue bar section`. pressing that opens a log window that that show application logs
- closing application windows, sends a `CONFIGDONE` to device.
- error messages shows a modal window with ok button 