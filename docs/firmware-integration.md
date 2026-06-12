# Firmware Integration

The `owntech/` directory contains the PlatformIO project that runs on the SPIN board. It bridges high-level commands sent by the supervisor to the hardware control loops implemented on the microcontroller.

## Project Contents

- `main.cpp` – entry point implementing PWM generation, command parsing, and device state updates.
- `Twist_Class.py` – optional Python helper for interacting with the board; useful during development and interactive testing.
- `find_devices.py` – lightweight script for enumerating connected devices when running firmware-side tests.
- `platformio.ini` – PlatformIO configuration describing the target board, frameworks, libraries, and build flags.

## Build and Flash Workflow

1. Install PlatformIO (CLI or IDE plugin).
2. From `owntech/`, run `platformio run` to compile the firmware.
3. Connect the SPIN board via USB and run `platformio run --target upload` to flash.
4. Monitor serial output with `platformio device monitor` to verify handshake messages with the supervisor.

## Protocol Alignment

Ensure the command identifiers, payload formats, and default timing values in `main.cpp` match the expectations encoded in `Shield_Class.py`. When modifying the firmware:

- Update the Python communication layer accordingly.
- Document new features or telemetry fields in [comm-protocol.md](comm-protocol.md).
- Adjust JSON configuration defaults if required (e.g., new safe ranges or initial duty cycle).

## Testing Firmware Changes

- Use `SPIN_COMM_test_script.py` for rapid command validation without powering the complete test bench.
- Run controlled sweeps with reduced voltage/current limits after flashing to confirm stability.
- Capture oscilloscope traces to confirm PWM duty and phase align with requested values.

Keeping firmware and Python layers synchronized avoids unexpected behaviour during automated sweeps and simplifies troubleshooting.
