# Troubleshooting

Use this guide to diagnose common issues encountered while operating the test bench.

## Instrument Connection Failures

- **Symptom:** `VisaIOError` while opening a resource.
  - Confirm the instrument appears in `python -m pyvisa.info` output.
  - Check `base-config.json` for stale VISA addresses (LAN IP changes are common).
  - Verify USB cables and hub power; some instruments require direct connections.

- **Symptom:** Shield device not detected.
  - Re-run `InitZplus_V5.py list` and look for the configured VID/PID.
  - Press the reset button on the SPIN board and wait for the OS to re-enumerate the serial port.
  - Ensure no other application (serial monitor) is holding the port open.

## Sweep Execution Issues

- **Symptom:** Supervisor aborts during voltage ramp.
  - Confirm `VoltageLimit` and `CurrentLimit` reflect the DUT capability.
  - Inspect the power supply driver for overcurrent protection events.
  - Reduce `voltage_step` or increase delays (`delay`, `delay2`) to allow settling.

- **Symptom:** Phase or duty sweep values drift.
  - Check firmware alignment (see [firmware-integration.md](firmware-integration.md)).
  - Use `SPIN_COMM_test_script.py` to send single commands and validate responses.
  - Inspect oscilloscope traces to confirm requested PWM changes actually occur.

## Data Capture Problems

- **Symptom:** Empty CSV output.
  - Ensure `SaveEachFrameDATA` is enabled in the JSON profile.
  - Confirm the DMM buffer read routine runs before `close_all_devices()`.

- **Symptom:** Plots missing or corrupted.
  - Validate that Matplotlib is installed and the environment has an available backend.
  - Check that `dataOutputFolder` exists and the process has write permissions.

## Firmware Misbehaviour

- **Symptom:** Supervisor commands return unexpected acknowledgements.
  - Reflash the SPIN firmware (`platformio run --target upload`).
  - Align command IDs between `Shield_Class.py` and `owntech/main.cpp`.
  - Power-cycle the board to clear residual state.

Document additional findings or lab-specific quirks in this file to build institutional knowledge over time.
