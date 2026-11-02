// Original reusable RTL: count synchronized rising edges per window.
// For FPGA use, pulse_in must be electrically level conditioned to 3.3V.
// Outputs update only on posedge clk; sample_valid is a one-clock strobe.
module pulse_event_meter #(
    parameter integer WINDOW_CYCLES = 100_000_000
)(
    input wire clk,
    input wire rst,
    input wire pulse_in,
    output reg [31:0] event_count,
    output reg sample_valid
);
    localparam integer CW = WINDOW_CYCLES > 1 ? $clog2(WINDOW_CYCLES) : 1;
    reg [CW-1:0] timer;
    reg [31:0] accum;
    reg sync0, sync1, sync_prev;
    wire pulse_rise = sync1 && !sync_prev;
    always @(posedge clk) begin
        if (rst) begin
            timer <= 0;
            accum <= 0;
            event_count <= 0;
            sample_valid <= 0;
            sync0 <= 0;
            sync1 <= 0;
            sync_prev <= 0;
        end else begin
            sync0 <= pulse_in;
            sync1 <= sync0;
            sync_prev <= sync1;
            sample_valid <= 0;
            if (timer == WINDOW_CYCLES - 1) begin
                timer <= 0;
                // Include the sample arriving on the snapshot boundary.
                event_count <= accum + pulse_rise;
                accum <= 0;
                sample_valid <= 1;
            end else begin
                timer <= timer + 1'b1;
                if (pulse_rise) accum <= accum + 1'b1;
            end
        end
    end
endmodule
