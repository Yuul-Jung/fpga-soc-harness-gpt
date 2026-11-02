# Reusable first-party RTL library

This library is independently authored for this harness. It does **not** copy source code from discovered repositories.

- `rtl/pulse_event_meter.v`: pulse synchronizer + 32-bit event counter and 1-window snapshot
- `tb/tb_pulse_event_meter.v`: self-checking Icarus Verilog testbench
- `sw/pulse_meter_mmio.c`: portable C memory-mapped read helper with native self-test

Targets: standalone RTL on Basys3 (100MHz clock), prospective MicroBlaze V via AXI GPIO (32 input bits). Real Block Design, pin assignment, timing closure, and board execution are **not** provided.

The first-party source cannot be treated as vendor-verified RTL or as a redesign of any referenced candidate. The external source is **inspiration** only.
