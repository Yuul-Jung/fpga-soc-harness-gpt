# Smart fan / motor PWM — integration note

## Implemented, independently testable
`rtl/smart_fan_peripheral.v` provides 8-bit PWM, input synchronizer and a 1-second tach pulse counter. `tb/tb_smart_fan_peripheral.v` self-checks PWM, tach and enable. `sw/fan_mmio.c` provides portable memory-mapped GPIO helpers with a native self-test.

At default `CLK_HZ=100_000_000`, `PWM_PRESCALE=16`, PWM frequency is about 24.414 kHz. The PWM duty comparison spans 0/256 through 255/256 (100% not representable). Tach pulses are counted in one-second windows; RPM calculation depends on pulses per revolution and belongs in software.

## Planned MicroBlaze V SoC integration (not yet built)
- AXI GPIO control channel 1: 9 output bits. `gpio_io_o[7:0]` to `duty`, `gpio_io_o[8]` to `enable`.
- AXI GPIO status channel 1: 32 input bits from `tach_pulses_per_sec`.
- All controller logic shares a correctly constrained 100 MHz clock; synchronous active-high `rst`.
- In Vivado, instantiate the standalone controller under a **connection-only shell top** with the required MicroBlaze V, AXI interconnect, 2 AXI GPIOs and validated clock/reset IP. Do not place functional logic in the top.
- Integrate `fan_mmio.c` into the Vitis program and bind *platform-generated* AXI GPIO data addresses. Initialize GPIO direction registers/driver in Vitis; do not hardcode guessed addresses.
- Do not infer the MicroBlaze V ISA/configuration, resource utilization, or real board timing from this RTL simulation.

## Physical interface safety
- Basys3 IO uses 3.3 V; **do not directly attach 5V/12V tach signals or inductive loads**.
- Use a compatible motor/fan driver, conditioned tach sensor and verified power wiring.
- Map board pins only after matching the actual Basys3 master XDC and the external board connector.
- Check common ground or electrical isolation as the interface requires. Test with a function generator / low-voltage logic first.

## Local verification commands
```bash
iverilog -g2012 -s tb_smart_fan_peripheral -o /tmp/fan_tb.vvp \
  capstones/smart_fan/rtl/smart_fan_peripheral.v \
  capstones/smart_fan/tb/tb_smart_fan_peripheral.v
vvp /tmp/fan_tb.vvp
cc -std=c11 -Wall -Wextra -DFAN_MMIO_SELFTEST \
  capstones/smart_fan/sw/fan_mmio.c -o /tmp/fan_mmio_test
/tmp/fan_mmio_test
```
