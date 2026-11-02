# FPGA SoC pulse counter — first-party starter

Architecture: synchronized external pulse -> 32-bit counter snapshot -> AXI GPIO
input -> MicroBlaze V application reads DATA register. The AXI GPIO, CPU,
clock/reset and board pins are **conceptual only** until a reproducible
Vivado/Vitis design and XDC are added.

## Files
- rtl/pulse_event_meter.v — synthesizable counter, one-second window at 100MHz
- tb/tb_pulse_event_meter.v — Icarus Verilog self-checking simulation
- sw/pulse_meter_mmio.c — application helper, with native C self-test

## Timing
WINDOW_CYCLES=100000000 at 100 MHz means one update per 1 second.
At WINDOW_CYCLES=64 in simulation, a 64-clock test window is used.
event_count is a pulse count per window, not necessarily RPM.
For a sensor producing P pulses per revolution, RPM is
event_count * 60 / P, if the window is one second.

## Physical constraints
FPGA I/O is 3.3V. Route external pulses through a compatible conditioned
driver. Physical pin assignments, interrupt registration and real address map
must come from a tested board design; no invented address or XDC.

## Run in repository root
```bash
iverilog -g2012 -s tb_pulse_event_meter -o /tmp/counter.vvp   capstones/instrument_pulse_counter/rtl/pulse_event_meter.v   capstones/instrument_pulse_counter/tb/tb_pulse_event_meter.v
vvp /tmp/counter.vvp
cc -std=c11 -DPULSE_METER_SELFTEST   capstones/instrument_pulse_counter/sw/pulse_meter_mmio.c -o /tmp/counter_sw
/tmp/counter_sw
```
