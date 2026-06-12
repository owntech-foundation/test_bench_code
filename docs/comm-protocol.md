# Communication Protocol

The `comm_protocol/` directory contains the tooling required to discover and communicate with the SPIN board (Shield device). It combines Python helpers with C++ support files.

## Directory Layout

- `src/find_devices.py` – scans available USB serial ports, filters by VID/PID, and returns candidate devices for the supervisor.
- `src/Shield_Class.py` – Python abstraction for the Shield device, wrapping serial communication, framing, and command helpers.
- `src/comm_protocol.{h,cpp}` – native helpers referenced by the Python bindings when more performant processing is needed.
- `src/SPIN_COMM_test_script.py` – standalone script used to validate communication outside of the full supervisor workflow.
- `supervisor_old/` – archived supervisor versions that still rely on the same communication layer for reference.

## Device Discovery

`find_devices.py` enumerates serial ports via `pyserial`, matching VID/PID values stored in the configuration (`shield_vid`, `shield_pid`). The returned port string is then opened by the supervisor to instantiate `Shield_Device`.

## Shield Device API

`Shield_Class.py` exposes methods to:

- Open and close the serial connection with configured baud rate and timeout.
- Send structured commands that configure PWM frequency, duty cycle, dead time, and phase shift.
- Read acknowledgements or status frames from the board.
- Handle reconnection logic when the SPIN board resets.

The supervisor uses these methods to keep firmware aligned with the electrical sweeps. Ensure command payloads stay in sync with the firmware protocol described in [firmware-integration.md](firmware-integration.md).

## Standalone Testing

Use `SPIN_COMM_test_script.py` to replicate Shield interactions without orchestrating the full test bench. This aids troubleshooting when the supervisor appears unresponsive but instruments are reachable.

## Extending the Protocol

- Document any new command identifiers in both the Python class and firmware code.
- Maintain backward compatibility when possible; add version negotiation if the protocol evolves.
- Update automated runbooks to include new calibration or setup steps introduced by protocol changes.
