/*
 * Portable AXI GPIO data register access helpers.
 * The board-specific BSP must configure one 9-bit GPIO output and
 * one 32-bit GPIO input, and pass the correct mapped DATA addresses.
 * Native self-test: cc -std=c11 -DFAN_MMIO_SELFTEST fan_mmio.c -o fan_test
 */
#include <stdint.h>

uint32_t fan_control_word(uint8_t duty, int enabled)
{
    return (uint32_t)duty | (enabled ? (1u << 8) : 0u);
}

void fan_set_control(volatile uint32_t *gpio_output_data,
                     uint8_t duty, int enabled)
{
    *gpio_output_data = fan_control_word(duty, enabled);
}

uint32_t fan_get_tach_pulses(volatile const uint32_t *gpio_input_data)
{
    return *gpio_input_data;
}

#ifdef FAN_MMIO_SELFTEST
#include <assert.h>
#include <stdio.h>
int main(void)
{
    volatile uint32_t control = 0;
    volatile uint32_t status = 42;
    fan_set_control(&control, 128, 1);
    assert(control == 0x180u);
    assert(fan_get_tach_pulses(&status) == 42u);
    fan_set_control(&control, 0, 0);
    assert(control == 0u);
    puts("PASS fan_mmio self-test");
    return 0;
}
#endif
