// Self-checking RTL testbench (simulation only; not synthesized).
// CLK_HZ=4096 accelerates the 1-second accumulation window.
`timescale 1ns/1ps
module tb_smart_fan_peripheral;
    reg clk = 0;
    always #5 clk = ~clk;

    reg rst = 1;
    reg [7:0] duty = 8'd128;
    reg enable = 1;
    reg tach_in = 0;
    wire pwm_out;
    wire [31:0] tach_pulses_per_sec;
    integer high_count = 0;
    integer low_count = 0;
    integer i;

    smart_fan_peripheral #(
        .CLK_HZ(4096),
        .PWM_PRESCALE(1)
    ) dut (
        .clk(clk), .rst(rst), .duty(duty), .enable(enable),
        .tach_in(tach_in), .pwm_out(pwm_out),
        .tach_pulses_per_sec(tach_pulses_per_sec)
    );

    task pulse_tach;
        begin
            tach_in = 1;
            repeat (5) @(negedge clk);
            tach_in = 0;
            repeat (8) @(negedge clk);
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        rst = 0;

        // 2 PWM periods at 50% duty: exactly 256 high and 256 low samples.
        for (i=0; i<512; i=i+1) begin
            @(negedge clk);
            if (pwm_out === 1'b1)
                high_count = high_count + 1;
            else if (pwm_out === 1'b0)
                low_count = low_count + 1;
            else
                $fatal(1, "PWM X/Z state");
        end
        if (high_count != 256 || low_count != 256)
            $fatal(1, "Incorrect PWM 50-percent duty: high=%0d low=%0d",
                   high_count, low_count);

        pulse_tach();
        pulse_tach();
        // Continue past the first counter snapshot boundary.
        repeat (3700) @(negedge clk);
        if (tach_pulses_per_sec !== 32'd2)
            $fatal(1, "Expected 2 tach pulses, got %0d", tach_pulses_per_sec);

        duty = 0;
        repeat (32) begin
            @(negedge clk);
            if (pwm_out !== 1'b0) $fatal(1, "Duty zero must be low");
        end
        enable = 0;
        duty = 255;
        repeat (32) begin
            @(negedge clk);
            if (pwm_out !== 1'b0) $fatal(1, "Disabled PWM must be low");
        end
        $display("PASS smart_fan_peripheral PWM/TACH");
        $finish;
    end
endmodule
