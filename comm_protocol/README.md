# Power Test Bench Communication Library

This repository contains a communication library for the power test bench of the Twist board converter developed by LAAS-CNRS.

## License

This library is distributed under the terms of the GNU Lesser General Public License (LGPL) version 2.1 or later. See the [LICENSE](LICENSE) file for details.

## Overview

The `comm_protocol.h` file serves as the main entry point of the OwnTech Power API. It provides communication protocols and data structures for interacting with the power test bench.

## Communication Protocol

The communication protocol consists of commands and messages exchanged between the test bench and external systems. These commands and messages are used to configure settings, send control signals, and receive measurements.

# Twist Board Protocol

The Twist Board Protocol is a communication protocol used to control and configure the Twist board, a hardware device designed for various electrical control applications. This protocol allows users to send commands to the Twist board via serial communication to perform specific actions and configurations.

## Commands

Once you have created your python twist object, in the example below considered as `twistObject`,
you can use the following commands with the Twist Board Protocol:

1. **IDLE**
   - Python-side command: `twistObject.sendCommand("IDLE")`
   - Serial-side output: `d_i`

2. **POWER_OFF**
   - Python-side command: `twistObject.sendCommand("POWER_OFF")`
   - Serial-side output: `d_f`

3. **POWER_ON**
   - Python-side command: `twistObject.sendCommand("POWER_ON")`
   - Serial-side output: `d_o`

4. **LEG**
   - Python-side command: `twistObject.sendCommand("LEG", "LEG_IDENTIFIER", "STATE")`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "STATE" = `"ON"`, `"OFF"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_l_{STATE}`

5. **CAPA**
   - Python-side command: `twistObject.sendCommand("CAPA", "LEG_IDENTIFIER", "STATE")`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "STATE" = `"ON"`, `"OFF"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_c_{STATE}`

6. **DRIVER**
   - Python-side command: `twistObject.sendCommand("DRIVER", "LEG_IDENTIFIER", "STATE")`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "STATE" = `"ON"`, `"OFF"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_v_{STATE}`

7. **BUCK**
   - Python-side command: `twistObject.sendCommand("BUCK", "LEG_IDENTIFIER", "STATE")`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "STATE" = `"ON"`, `"OFF"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_b_{STATE}`

8. **BOOST**
   - Python-side command: `twistObject.sendCommand("BOOST", "LEG_IDENTIFIER", "STATE")`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "STATE" = `"ON"`, `"OFF"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_t_{STATE}`

9. **REFERENCE**
   - Python-side command: `twistObject.sendCommand("REFERENCE", "LEG_IDENTIFIER", "VARIABLE", VALUE)`
   - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
   - Possible "VARIABLE" = `"V1"`, `"V2"`, `"VH"`, `"I1"`, `"I2"`, `"IH"`
   - Serial-side output: `s_{LEG_IDENTIFIER}_r_{VARIABLE}_{VALUE:.5f}`

10. **DUTY**
    - Python-side command: `twistObject.sendCommand("DUTY", "LEG_IDENTIFIER", VALUE)`
    - Possible "LEG_IDENTIFIER" = `"LEG1"`, `"LEG2"`
    - `VALUE` = float up to 5 decimals
    - Serial-side output: `s_{LEG_IDENTIFIER}_d_{VALUE:.5f}`
    - Example: `s_LEG1_d_0.02233`

11. **CALIBRATE**
    - Python-side command: `twistObject.sendCommand("CALIBRATE", "VARIABLE", GAIN, OFFSET)`
    - Possible "VARIABLE" = `"V1"`, `"V2"`, `"VH"`, `"I1"`, `"I2"`, `"IH"`
    - `GAIN` = float value up to 8 decimals
    - `OFFSET` = float value up to 8 decimals
    - Serial-side output: `k_{VARIABLE}_g_{GAIN:.8f}_o_{OFFSET:.8f}`
    - Example: `k_V1_g_22.03409353_o_0.11349874`

These are the Python-side commands that can be sent to the Twist board using the `sendCommand` method along with their corresponding serial-side output formats. Use these commands to control and configure the Twist board via serial communication.
