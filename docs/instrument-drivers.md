# Instrument Drivers

Reusable hardware abstractions live in the `lib/` directory. They provide thin, testable wrappers around SCPI-capable instruments, keeping the supervisor logic focused on orchestration.

## Key Modules

- `PSU.py` and `NGL202.py` – power supply helpers for the TDK Lambda and Rohde & Schwarz models. They cover channel configuration, voltage/current setpoints, and ramping utilities.
- `DMM.py` and `KEYTHLEY2000.py` – digital multimeter interfaces supporting measurement mode selection, buffer reads, and integration with PyVISA resources.
- `Oscillo_v1b.py` and `scope_class.py` – oscilloscope control for Siglent devices, including acquisition setup, triggering, data capture, and CSV export.
- `Instrument.py` – shared utilities or base classes that enforce common behaviour (timeouts, command formatting).
- `align-plots.py`, `plot_res.py`, and `ReadCSV.py` – post-processing helpers for aligning traces, plotting results, and loading CSV exports.

## Design Principles

- Each driver expects an already-open PyVISA resource; connection management is delegated to the supervisor.
- Methods map directly to SCPI commands so advanced users can correlate actions with instrument manuals.
- Drivers expose Pythonic wrappers (e.g., `set_voltage`, `read_current`) to simplify high-level routines.
- Optional plotting scripts operate on structured data stored in the results folder, enabling offline analysis without hardware access.

## Adding New Instruments

1. Create a new module under `lib/` following the existing naming pattern.
2. Accept a PyVISA resource object in the constructor and configure common settings (terminations, timeouts).
3. Implement idn checks to help catch misconfigured VISA addresses.
4. Provide low-level methods for SCPI commands alongside convenience wrappers tailored to expected workflows.
5. Update the supervisor to use the new driver where appropriate and add configuration keys for any new parameters.

## Interactions with Supervisor

During a sweep the supervisor calls the following sequences:

- Power supply driver sets initial voltage, ramps up/down, and enforces current limits.
- DMM drivers switch measurement mode and read buffers once sweeps end.
- Oscilloscope driver prepares captures, performs automatic measurements (`ScopeAutoMeasure`), and optionally saves traces.

Keep driver methods idempotent and defensive so repeated calls (e.g., retries) do not leave hardware in inconsistent states.
