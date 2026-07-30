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
meaning and values of these parameter are explained in `Serial Protocol.md`

user can add, edit and remove configuration profiles.
after the board is connected, user select on of perviously defined profiles and then the software configs the device with values of that profile. 

profiles are saved in a json file, store in same directory as executable. 
