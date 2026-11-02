// Smart fan peripheral: 8-bit PWM and synchronized tach pulse counter
// Original first-party teaching RTL. Not an AXI slave.
// 100MHz / (16 * 256) = 24,414.0625 Hz PWM when defaults are used.
module smart_fan_peripheral #(
    parameter integer CLK_HZ = 100_000_000,
    parameter integer PWM_PRESCALE = 16
) (
    input  wire        clk,
    input  wire        rst,       // synchronous active-high reset
    input  wire [7:0]  duty,      // 0..255: 0..255/256 PWM high fraction
    input  wire        enable,
    input  wire        tach_in,   // conditioned 3.3V digital pulse
    output wire        pwm_out,
    output reg  [31:0] tach_pulses_per_sec
);
    localparam integer DIV_W = (PWM_PRESCALE > 1) ? $clog2(PWM_PRESCALE) : 1;
    localparam integer SEC_W = (CLK_HZ > 1) ? $clog2(CLK_HZ) : 1;

    reg [DIV_W-1:0] prescale_count;
    reg [7:0] pwm_phase;
    reg [SEC_W-1:0] sec_count;
    reg [31:0] tach_accum;
    reg tach_sync_0, tach_sync_1, tach_prev;

    // Asynchronous tach input is sampled by two flip-flops (CDC).
    wire tach_rise = tach_sync_1 && !tach_prev;
    assign pwm_out = enable && (pwm_phase < duty);

    always @(posedge clk) begin
        if (rst) begin
            prescale_count <= 0;
            pwm_phase <= 0;
            sec_count <= 0;
            tach_accum <= 0;
            tach_pulses_per_sec <= 0;
            tach_sync_0 <= 0;
            tach_sync_1 <= 0;
            tach_prev <= 0;
        end else begin
            // Prescaler -> PWM phase register -> digital comparator output
            if (prescale_count == PWM_PRESCALE - 1) begin
                prescale_count <= 0;
                pwm_phase <= pwm_phase + 1'b1;
            end else begin
                prescale_count <= prescale_count + 1'b1;
            end

            tach_sync_0 <= tach_in;
            tach_sync_1 <= tach_sync_0;
            tach_prev <= tach_sync_1;

            // One-second snapshot register, includes pulse on boundary clock.
            if (sec_count == CLK_HZ - 1) begin
                sec_count <= 0;
                tach_pulses_per_sec <= tach_accum + tach_rise;
                tach_accum <= 0;
            end else begin
                sec_count <= sec_count + 1'b1;
                if (tach_rise)
                    tach_accum <= tach_accum + 1'b1;
            end
        end
    end
endmodule
