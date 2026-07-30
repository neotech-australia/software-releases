> this document describes Serial protocol that is used for devices-PC communication. this communication is used to configure a device with companion PC software, and also read its parameters. 

# AT command structure

all data transaction are performed via AT commands. some AT commands are built in to device SDK and some of them are custom. 

built-in AT commands start with `AT` and custom AT commands start with `ATC`
AT command are used to:

- read a value
- write a value
- performing an action

here is generic structure of any AT command: 

```
AT+XXX? provides a short description of the given command, for example, AT+DEVEUI?.
AT+XXX is used to run a command, such as AT+JOIN.
AT+XXX=? is used to get the value of a given command, for example, AT+CFS=?.
AT+XXX=<value> is used to provide a value to a command, for example, AT+CFM=1.
```

note: custom AT command have exact same structure with only difference being that they start with `ATC` instead of `AT`

note: device sends `OK` after each successful AT command transaction. here is complete guide about return AT return codes:

```
OK: command runs correctly without error.
AT_ERROR: generic error.
AT_PARAM_ERROR: a parameter of the command is wrong.
AT_BUSY_ERROR: the LoRa network is busy, so the command has not been completed.
AT_TEST_PARAM_OVERFLOW: the parameter is too long.
AT_NO_CLASSB_ENABLE: End-node has not yet switched in Class B.
AT_NO_NETWORK_JOINED: the LoRa network has not been joined yet.
AT_RX_ERROR: error detection during the reception of the command.
```

note: UART settings for this communication is: 

- baudrate = 115200
- Data bits = 8
- Parity = none
- stop bit = 1

# Communication flow

PC sends `ATC+STARTCONFIG` to start configuration process. after this, device sends all its parameters with this format:

```
<KEY_1>=<VALUE_1>
<KEY_2>=<VALUE_2>
...
<KEY_N>=<VALUE_N>
```

then PC modifies parameters like this:

```
AT+<KEY>=<VALUE> //for built-in AT commands
ATC+<KEY>=<VALUE> //for custom AT commands
```

 when PC is done, it sends `ATC+CONFIGDONE` to end configuration process. 

# List of Keys used in AT commands

Built-in commands are provided by the RAK RUI3 SDK on the LoRa module. They use the `AT+` prefix. EUIs and keys are **MSB first**. Hex values use characters `0-9`, `a-f`, or `A-F` only.

Reference: [RUI3 AT Command Manual](https://docs.rakwireless.com/product-categories/software-apis-and-libraries/rui3/at-command-manual/#content) (LoRaWAN Activation & Regional Commands).

**PC app notes**

- Terminate every command with `<CR><LF>` (`\r\n`, bytes `0x0D 0x0A`).
- Wait for the full response (value line if any, then `OK` or an error) before sending the next command.
- During configuration (see [Communication flow](#communication-flow)), use `AT+<KEY>=<VALUE>` to write and `AT+<KEY>=?` to read a single parameter.
- On read (`AT+<KEY>=?`), the device echoes `AT+<KEY>=<value>` then `OK`.

---

## Built-in AT commands

### DEVEUI


| Item            | Detail                                                  |
| --------------- | ------------------------------------------------------- |
| **Description** | Unique device EUI (DevEUI). Required for **OTAA** join. |
| **Write**       | `AT+DEVEUI=<8 bytes hex>` — 16 hex digits (8 bytes).    |
| **Read**        | `AT+DEVEUI=?` → `AT+DEVEUI=<16 hex digits>` then `OK`.  |
| **Help**        | `AT+DEVEUI?` → short description, then `OK`.            |
| **Errors**      | `AT_PARAM_ERROR` if length or characters are invalid.   |


**PC example (set DevEUI during configuration)**

```
AT+DEVEUI=AC1F09FFFE12AB34\r\n
```

Expected response:

```
OK
```

---

### APPEUI


| Item            | Detail                                                           |
| --------------- | ---------------------------------------------------------------- |
| **Description** | Application EUI (Join EUI / AppEUI). Required for **OTAA** join. |
| **Write**       | `AT+APPEUI=<8 bytes hex>` — 16 hex digits (8 bytes).             |
| **Read**        | `AT+APPEUI=?` → `AT+APPEUI=<16 hex digits>` then `OK`.           |
| **Help**        | `AT+APPEUI?` → short description, then `OK`.                     |
| **Errors**      | `AT_PARAM_ERROR` if length or characters are invalid.            |


**PC example (set AppEUI during configuration)**

```
AT+APPEUI=0000000000000001\r\n
```

Expected response:

```
OK
```

---

### APPKEY


| Item            | Detail                                                     |
| --------------- | ---------------------------------------------------------- |
| **Description** | Application root key (AppKey). Required for **OTAA** join. |
| **Write**       | `AT+APPKEY=<16 bytes hex>` — 32 hex digits (16 bytes).     |
| **Read**        | `AT+APPKEY=?` → `AT+APPKEY=<32 hex digits>` then `OK`.     |
| **Help**        | `AT+APPKEY?` → short description, then `OK`.               |
| **Errors**      | `AT_PARAM_ERROR` if length or characters are invalid.      |


**PC example (set AppKey during configuration)**

```
AT+APPKEY=2B7E151628AED2A6ABF7158809CF4F3C\r\n
```

Expected response:

```
OK
```

---

### BAND


| Item            | Detail                                         |
| --------------- | ---------------------------------------------- |
| **Description** | Active LoRaWAN regional band (frequency plan). |
| **Write**       | `AT+BAND=<0–12>` — one decimal integer.        |
| **Read**        | `AT+BAND=?` → `AT+BAND=<n>` then `OK`.         |
| **Help**        | `AT+BAND?` → short description, then `OK`.     |
| **Errors**      | `AT_PARAM_ERROR`, `AT_BUSY_ERROR`              |



| Value | Region  |
| ----- | ------- |
| 0     | EU433   |
| 1     | CN470   |
| 2     | RU864   |
| 3     | IN865   |
| 4     | EU868   |
| 5     | US915   |
| 6     | AU915   |
| 7     | KR920   |
| 8     | AS923-1 |
| 9     | AS923-2 |
| 10    | AS923-3 |
| 11    | AS923-4 |
| 12    | LA915   |


Default band depends on module SKU (often `4` = EU868). Hardware variant limits which values are valid (low-frequency modules: 0–1; high-frequency: 2–12).

**PC example (set region to EU868)**

```
AT+BAND=4\r\n
```

Expected response:

```
OK
```

---

### MASK


| Item            | Detail                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------- |
| **Description** | Channel mask — enables or disables channel groups.                                                      |
| **Applies to**  | **US915**, **AU915**, **LA915**, **CN470** only. Ignored or not applicable on other bands (e.g. EU868). |
| **Write**       | `AT+MASK=<mask>` — 4 hex digits (16-bit mask).                                                          |
| **Read**        | `AT+MASK=?` → `AT+MASK=<mask>` then `OK`.                                                               |
| **Help**        | `AT+MASK?` → short description, then `OK`.                                                              |
| **Errors**      | `AT_PARAM_ERROR`, `AT_BUSY_ERROR`                                                                       |


**Defaults:** US915 / AU915 / LA915 → `01FF`; CN470 → `0FFF`.

Common US915 / AU915 / LA915 sub-band values:


| Mask   | Sub-band | Channels (typical) |
| ------ | -------- | ------------------ |
| `0001` | 1        | 0–7 (+ 64)         |
| `0002` | 2        | 8–15 (+ 65)        |
| `0004` | 3        | 16–23 (+ 66)       |
| …      | …        | …                  |
| `0080` | 8        | 56–63 (+ 71)       |


For an 8-channel gateway on US915 using channels 8–15, use mask `0002` (see RAK manual).

**PC example (US915: enable sub-band 2, channels 8–15)**

```
AT+MASK=0002\r\n
```

Expected response:

```
OK
```

---

## Custom AT commands

Custom commands are implemented in device firmware. They use the `ATC+` prefix and follow the same read/write/help syntax as built-in commands (see [AT command structure](#at-command-structure)).

During configuration, the device may also report these keys in the initial dump as `KEY=VALUE` lines (no `ATC+` prefix on those lines). To change a value from the PC app, send `ATC+<KEY>=<VALUE>`.

**PC app notes**

- Terminate every command with `<CR><LF>` (`\r\n`).
- Writable parameters are **unsigned decimal integers** (`0`–`9` only). Non-numeric input returns `AT_PARAM_ERROR`.
- On read (`ATC+<KEY>=?`), the device echoes `ATC+<KEY>=<value>` then `OK`.

---

### UPLINKPERIOD


| Item            | Detail                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------- |
| **Description** | Uplink period in seconds. On each uplink routine, sensor data is sampled and sent to the gateway. |
| **Write**       | `ATC+UPLINKPERIOD=<seconds>` — unsigned decimal integer.                                          |
| **Read**        | `ATC+UPLINKPERIOD=?` → `ATC+UPLINKPERIOD=<seconds>` then `OK`.                                    |
| **Help**        | `ATC+UPLINKPERIOD?` → short description, then `OK`.                                               |
| **Errors**      | `AT_PARAM_ERROR` if the value is missing or not a decimal integer.                                |
| **Default**     | `1800` (30 minutes) when no stored configuration exists.                                          |


**PC example (set uplink period to 600 seconds)**

```
ATC+UPLINKPERIOD=600\r\n
```

Expected response:

```
OK
```

---

### GPSDECIMATIONFACTOR


| Item            | Detail                                                                                                                           |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Decimation factor for GPS sampling. `n` means GPS location is acquired once every `n` uplink routines. Setting `0` disables GPS. |
| **Write**       | `ATC+GPSDECIMATIONFACTOR=<n>` — unsigned decimal integer (`0` disables GPS).                                                     |
| **Read**        | `ATC+GPSDECIMATIONFACTOR=?` → `ATC+GPSDECIMATIONFACTOR=<n>` then `OK`.                                                           |
| **Help**        | `ATC+GPSDECIMATIONFACTOR?` → short description, then `OK`.                                                                       |
| **Errors**      | `AT_PARAM_ERROR` if the value is missing or not a decimal integer.                                                               |
| **Default**     | `8` when no stored configuration exists.                                                                                         |


**PC example (acquire GPS every 4th uplink)**

```
ATC+GPSDECIMATIONFACTOR=4\r\n
```

Expected response:

```
OK
```

---

### HWSTATUS


| Item            | Detail                                              |
| --------------- | --------------------------------------------------- |
| **Description** | Hardware self-test status. **Read only.**           |
| **Write**       | Not supported.                                      |
| **Read**        | `ATC+HWSTATUS=?` → `ATC+HWSTATUS=<code>` then `OK`. |
| **Help**        | `ATC+HWSTATUS?` → short description, then `OK`.     |



| Value    | Meaning                                                     |
| -------- | ----------------------------------------------------------- |
| `0`      | All hardware OK.                                            |
| Non-zero | Error code (specific code indicates which hardware failed). |


**PC example (read hardware status)**

```
ATC+HWSTATUS=?\r\n
```

Expected response (all OK):

```
ATC+HWSTATUS=0
OK
```

---

### SAMPLETILT


| Item            | Detail                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------- |
| **Description** | Samples tilt (inclination) from the onboard inclinometer sensor and outputs the readings. Action only. |
| **Write**       | Not supported.                                                                                  |
| **Read**        | Not supported.                                                                                  |
| **Action**      | `ATC+SAMPLETILT` — no parameters. Triggers an inclinometer sample.                               |
| **Help**        | `ATC+SAMPLETILT?` → short description, then `OK`.                                               |


Output on success (two lines, then `OK`):

```
tilt_x=<float value>
tilt_y=<float value>
OK
```

Output on sensor error (one line, then `OK`):

```
INCLINATION_SENSOR_ERROR
OK
```

**PC example (sample tilt)**

```
ATC+SAMPLETILT\r\n
```

Expected response:

```
tilt_x=-0.02
tilt_y=1.34
OK
```

---

### GPSFIX


| Item            | Detail                                                                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description** | Polls the GPS module to obtain a GPS fix. May take up to 60 seconds to respond. Action only.                                                               |
| **Write**       | Not supported.                                                                                                                                             |
| **Read**        | Not supported.                                                                                                                                             |
| **Action**      | `ATC+GPSFIX` — no parameters. Triggers a GPS fix acquisition.                                                                                               |
| **Help**        | `ATC+GPSFIX?` → short description, then `OK`.                                                                                                              |


Output on successful fix (three lines, then `OK`):

```
latitude=<double value>
longitude=<double value>
altitude=<float value>
OK
```

Output when fix cannot be obtained (one line, then `OK`):

```
NO_GPS_FIX
OK
```

Output when GPS module does not respond (one line, then `OK`):

```
NO_DATA_FROM_GPS_MODULE
OK
```

**PC example (get GPS fix)**

```
ATC+GPSFIX\r\n
```

Expected response:

```
latitude=35.689487
longitude=51.389046
altitude=1200.5
OK
```

---

### ABORTGPSFIX


| Item            | Detail                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Description** | Aborts an ongoing GPS fix acquisition if the device is in the GPS acquisition loop (e.g., after `ATC+GPSFIX`). Action only.          |
| **Write**       | Not supported.                                                                                                                       |
| **Read**        | Not supported.                                                                                                                       |
| **Action**      | `ATC+ABORTGPSFIX` — no parameters. Aborts the current GPS fix acquisition.                                                           |
| **Help**        | `ATC+ABORTGPSFIX?` → short description, then `OK`.                                                                                  |


**PC example (abort GPS fix)**

```
ATC+ABORTGPSFIX\r\n
```

Expected response:

```
OK
```

---

### FULLSAMPLE


| Item            | Detail                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| **Description** | Samples all onboard sensors (tilt, compass, temperature, battery) and outputs all readings. Action only.      |
| **Write**       | Not supported.                                                                                                |
| **Read**        | Not supported.                                                                                                |
| **Action**      | `ATC+FULLSAMPLE` — no parameters. Triggers a full multi-sensor sample.                                        |
| **Help**        | `ATC+FULLSAMPLE?` → short description, then `OK`.                                                             |


Output on success (six lines, then `OK`). Any value may be `INVALID` if the corresponding sensor reading failed:

```
tilt_x=<float value>
tilt_y=<float value>
compass_heading=<float value>
temperature=<float value>
battery_charge_percent=<integer value>
battery_voltage_v=<float value>
OK
```

**PC example (full sample)**

```
ATC+FULLSAMPLE\r\n
```

Expected response:

```
tilt_x=0.01
tilt_y=1.22
compass_heading=180.5
temperature=24.3
battery_charge_percent=85
battery_voltage_v=3.70
OK
```


