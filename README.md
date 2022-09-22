# RIGOL DS1054Z + DG800/DG900 Bode Plot in Python

This project is based on the excellent work of [ailr16](https://github.com/ailr16) [(ailr16/BodePlot-DS1054Z)](https://github.com/ailr16/BodePlot-DS1054Z) and [jbtronics](https://github.com/jbtronics) [(jbtronics/DS1054_BodePlotter)](https://github.com/jbtronics/DS1054_BodePlotter)

## Requirements: ##
Oscilloscope: RIGOL DS1054Z

AWG: RIGOL DG800/DG900 Series

The scope and function generator can be connected by either USB-TMC or LAN.

## Instructions ##
1. Connect CH1 of the function generator to the input of the DUT
2. Connect CH1 of the scope to CH1 of the function generator (input of the DUT)
3. Connect CH2 of the scope to the output of the DUT

4. Modify the config.txt as per your requirements.

| parameter | possible values | example |
| ------------- | ------------- | ------------- |
| start_freq  | number  | 1000 |
| end_freq  | number  | 800000 |
| steps  | number  | 20 |
| vpp  | number  | 5 |
| sweep  | 'log' or 'linear'  | log |
| scale  | 'db', 'v' or 'both'  | db |
| scope_id  | VISA address  | TCPIP::192.168.1.2::INSTR |
| awg_id  | VISA address  | USB0::0x1AB1::0x0643::DG8A24131337::INSTR |

5. execute the script. e.g `python3.10 BodePlot.py`

## Screenshots ##

![command output](https://github.com/DanielStoelzner/RIGOL-DS1054Z-DG800-DG900-Bode-Plot/blob/main/Screenshots/cmd.png)

![plots](https://github.com/DanielStoelzner/RIGOL-DS1054Z-DG800-DG900-Bode-Plot/blob/main/Screenshots/plots.png)
