/* First-party AXI GPIO read helper. Platform/BSP provides DATA address.
 * Native self-test:
 * cc -std=c11 -DPULSE_METER_SELFTEST pulse_meter_mmio.c -o /tmp/pulse_test
 */
#include <stdint.h>

uint32_t pulse_meter_read(volatile const uint32_t *gpio_data)
{
    return *gpio_data;
}
#ifdef PULSE_METER_SELFTEST
#include <assert.h>
#include <stdio.h>
int main(void)
{
    volatile uint32_t mock_data = 123;
    assert(pulse_meter_read(&mock_data) == 123u);
    puts("PASS pulse_meter_mmio self-test");
    return 0;
}
#endif
