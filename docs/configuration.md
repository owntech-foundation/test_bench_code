# Configuration Files

The test bench relies on JSON configuration files to set instrument addresses, sweep parameters, delays, and output paths. This document explains how configuration data is organized and generated.

## Base Template (`base-config.json`)

- Stores VISA resource addresses for the power supply, DMMs, oscilloscope, and Shield VID/PID.
- Defines default sweep envelopes such as `VoltageLimit`, `PhaseInit`, `PhaseFinal`, and `PhaseStep`.
- Contains delays (`delay`, `delay2`, `delay3`, `delay_com`, `delayOscillo`) used throughout the supervisor.
- Includes output settings like `dataOutputFolder`, `SaveEachFrameDATA`, and `SaveEachFramePICTURE`.

Before running any automation, update this file with the actual instrument identifiers reported by `pyvisa-info` or the listing utilities described below.

## Generated Profiles

`Opposition_GenerateJson_v1_4.py` expands the base template into a tree of scenario-specific JSON files. Each file encodes a pair of sweep settings (e.g., a voltage level plus a phase or duty sweep). The default layout looks like:

```
PhaseShift/
  Voltage_40/
    PhaseShift_Voltage_40V_*.json
  Voltage_60/
    ...
DutyShift/
  Voltage_40/
    ...
```

The supervisor consumes these generated files to know which profile to execute. Keep generated JSONs version-controlled only if they represent stable reference runs; otherwise treat them as build artifacts.

## CLI Helpers

- `InitZplus_V5.py list` – enumerates connected instruments and prints their VISA addresses; use this output to populate `base-config.json`.
- `InitZplus_V5.py single` – runs a single operating point defined in the base config for quick validation.
- `InitZplus_V5.py run` – iterates through all generated JSON files to execute full automated sweeps.
- `Opposition_GenerateJson_v1_4.py` – regenerates sweep profiles after adjusting the base configuration.

## Supervisor Consumption

When `Supervisor` is instantiated:

1. It reads a JSON file (commonly one of the generated profiles).
2. Every key is mirrored into an attribute, making configuration data accessible inside sweep logic, device setup, and logging routines.
3. The path in `dataOutputFolder` is created under the repository root to store CSV and plot outputs.

Ensure each generated JSON references the correct instrument names and contains consistent ranges; otherwise the supervisor will error out or drive equipment to unintended states.

## Best Practices

- Keep a pristine `base-config.json` documenting the lab default; copy it before experiments.
- Use semantic naming for generated files to capture the scenario (voltage, phase range, timestamp).
- Store calibration constants or hardware-specific tweaks in their own section to avoid duplication across profiles.
- Review values after firmware or hardware updates as VISA addresses and timing requirements may change.
