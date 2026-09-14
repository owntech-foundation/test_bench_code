# Operations Guide

This runbook explains how to prepare the environment, execute sweeps, and collect resulting data using the automated supervisor.

## Prerequisites

- Python environment created from `requirements.txt` (virtual environment recommended).
- PlatformIO installed if firmware updates are required.
- Instruments connected via USB or LAN and recognized by PyVISA (`python -m pyvisa.info`).

## Typical Workflow

1. **Validate Connections**
   - `python InitZplus_V5.py list` to print current VISA addresses.
   - Confirm the Shield device appears with the expected VID/PID.

2. **Refresh Configuration**
   - Update `base-config.json` with any new addresses or limits.
   - `python Opposition_GenerateJson_v1_4.py` to regenerate sweep profiles.

3. **Run a Dry Test**
   - `python InitZplus_V5.py single` for a steady-state check at a safe voltage.
   - Observe instrument readings to verify polarity and scaling.

4. **Execute Automated Sweeps**
   - `python InitZplus_V5.py run` or call `Supervisor` directly with a generated JSON file.
   - Monitor console output for progress messages and warnings.

5. **Collect Data**
   - Results are stored under the path specified by `dataOutputFolder` inside the JSON file.
   - Inspect CSV exports and plots with `lib/plot_res.py` or custom analysis notebooks.

## Safety Notes

- Start with conservative voltage/current limits when testing new DUTs.
- Ensure cooling and current monitoring before enabling continuous sweeps.
- Always stop the sequence gracefully to allow the supervisor to ramp down voltages.

## Automating Runs

- Use shell scripts or CI pipelines to call the supervisor with multiple JSON profiles.
- Capture supervisor stdout/stderr into log files for traceability.
- Schedule downtime to re-home instruments or apply firmware updates between long test batches.

## Post-Processing

- `lib/ReadCSV.py` and `lib/align-plots.py` help align and visualize data sets.
- Archive raw CSV files together with the matching JSON configurations for reproducibility.

Refer to [troubleshooting.md](troubleshooting.md) if instruments fail to connect or sweeps abort unexpectedly.
