# Supervisor Module

`supervisor_v2_2.py` contains the `Supervisor` class that coordinates every automated sequence. It loads parameters from JSON, establishes all instrument connections, runs voltage or duty sweeps, and persists measurements.

## Responsibilities

- Parse configuration files and expose parameters as attributes.
- Instantiate a shared PyVISA resource manager for all SCPI instruments.
- Manage instrument lifecycles (open, configure, close) for power supplies, DMMs, and oscilloscopes.
- Communicate with the SPIN board through the Shield API to adjust PWM settings.
- Execute sweep routines by sequencing voltage ramps, phase or duty sweeps, and data acquisition.
- Export results (CSV, plots) while keeping metadata under the configured output folder.

## Initialization Flow

1. Load the JSON file referenced in the constructor argument (defaults to `parameters.json`).
2. Create the results directory referenced by `dataOutputFolder` inside the JSON.
3. Assign every configuration key (delays, voltage limits, sweep ranges, instrument addresses) to instance attributes for later use.
4. Instantiate a single `visa.ResourceManager` stored as `self.rm`.
5. Prepare placeholders for instrument handles that are populated during `open_all_devices()`.

## Device Management

- `open_all_devices()` sequences the connection attempts and inserts short delays to avoid bus contention.
- Dedicated `open_*` and `close_*` helpers encapsulate resource acquisition and release for each instrument.
- Connections leverage identifiers from the configuration file, allowing quick retargeting of hardware.
- Always call `close_all_devices()` and `close_rm_manager()` in error handlers to leave equipment in a safe state.

## Running Tests

Typical sweep execution uses the following pattern:

1. Call `open_all_devices()`.
2. Issue warm-up commands (set voltage, initialize PWM) using the stored configuration parameters.
3. Execute the requested sweep loop (phase or duty) while logging samples.
4. Persist buffered measurements (`SaveEachFrameDATA` / `SaveEachFramePICTURE`) into the results folder.
5. Return hardware to the initial state and close resources.

Custom algorithms can reuse the existing private methods for ramping voltages, iterating phase/duty steps, or coordinating data capture. Ensure additional routines respect the same sequencing so the DMM buffer is read before voltages ramp down.

## Extending the Supervisor

- Add new configuration keys to the JSON template and mirror them in the constructor so they are available across methods.
- Introduce helper methods for new sweep profiles to maintain readability of the main sequence.
- Wrap long-running operations with logging statements to aid troubleshooting (`print` is currently used; structured logging can be added later).
- Keep device-specific code inside helpers or under `lib/` to avoid mixing orchestration and low-level drivers.

## Related Scripts

- `supervisor_script_v1_2.py` demonstrates how to launch a test by creating a supervisor instance and calling the sequence routines.
- `InitZplus_V5.py` provides a command-line entry point that can call supervisor functionality via arguments like `run` or `single`.

Consult [configuration.md](configuration.md) for details about the JSON parameters consumed by the supervisor.
