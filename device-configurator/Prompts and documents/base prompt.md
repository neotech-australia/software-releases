the aim of this project is to develop a utility desktop software that is used to configure embedded boards (through COM port).
the primarly target platform is windows, but supporting linux and/or mac is a cherry on top. 
the communication protocol between this app and the board is described in `Serial Protocol.md` file.
use python customTkinter library for development.
you may use pyserial or simular libraries for serial communication.
the application have GUI and CLI working modes.
the logical and protocol stuff should be separated from UI stuff. so both CLI and GUI mode use same controller logic. and hence the logical functionality of app can be tested with CLI version before starting GUI development. 
in short, this software connect to a embedded board with COM port, reads paramters of device, and sends configuration parameters. 

## about the parent project

embedded baords are IoT remote sensores that measure some quantities and send them to the gateway via loraWAN protocol. this companion PC software is used for initial setup and provisioning of the device. many of configuarion paramtes are related to LoraWAN.

