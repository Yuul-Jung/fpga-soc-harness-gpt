`timescale 1ns/1ps
// Simulation-only self-checking testbench. 64 cycles is one test window.
module tb_pulse_event_meter;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1;
    reg pulse_in=0;
    wire [31:0] event_count;
    wire sample_valid;
    pulse_event_meter #(.WINDOW_CYCLES(64)) dut (
        .clk(clk), .rst(rst), .pulse_in(pulse_in),
        .event_count(event_count), .sample_valid(sample_valid)
    );
    task send_pulse;
        begin
            @(negedge clk); pulse_in=1;
            repeat (4) @(negedge clk);
            pulse_in=0;
            repeat (5) @(negedge clk);
        end
    endtask
    initial begin
        repeat (4) @(negedge clk);
        rst=0;
        send_pulse();
        send_pulse();
        wait (sample_valid === 1'b1);
        if (event_count !== 32'd2)
            $fatal(1, "Expected 2 events, got %0d", event_count);
        repeat (2) @(negedge clk);
        $display("PASS pulse_event_meter");
        $finish;
    end
    initial begin
        #20000;
        $fatal(1, "test timeout");
    end
endmodule
