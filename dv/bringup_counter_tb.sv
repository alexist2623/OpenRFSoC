// SPDX-License-Identifier: MIT
`timescale 1ns/1ps
module bringup_counter_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg enable = 1'b0;
    wire [7:0] count;
    integer expected = 0;
    integer cycle;

    bringup_counter dut (.clk(clk), .rst_n(rst_n), .enable(enable), .count(count));
    always #5 clk = ~clk;

    task automatic check_count(input integer value);
        begin
            @(posedge clk);
            #1;
            if (count !== value[7:0])
                $fatal(1, "count=%0d expected=%0d", count, value);
        end
    endtask

    initial begin
        check_count(0);
        @(negedge clk);
        rst_n = 1'b1;
        // More than 256 enabled cycles exercise wraparound, with back-to-back
        // disabled intervals verifying that the register holds its value.
        for (cycle = 0; cycle < 420; cycle = cycle + 1) begin
            enable = ((cycle % 7) >= 2);
            if (enable)
                expected = (expected + 1) % 256;
            check_count(expected);
            @(negedge clk);
        end
        // Reset must dominate enable after a nonzero count.
        rst_n = 1'b0;
        enable = 1'b1;
        check_count(0);
        $display("PASS: reset, enable/hold, wraparound and reset priority");
        $finish;
    end

    initial begin
        #10000;
        $fatal(1, "Simulation timeout");
    end
endmodule
