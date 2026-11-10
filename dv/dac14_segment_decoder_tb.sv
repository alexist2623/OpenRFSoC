// SPDX-License-Identifier: MIT
`timescale 1ps/1ps
module dac14_segment_decoder_tb;
    reg clk = 0;
    reg rst_n = 0;
    reg [13:0] code = 0;
    wire [30:0] unary;
    wire [8:0] binary;
    integer n, j, reconstructed;
    dac14_segment_decoder dut (.clk(clk), .rst_n(rst_n), .code(code), .unary(unary), .binary(binary));
    always #250 clk = ~clk;
    initial begin
        @(posedge clk); #1;
        if (unary !== 0 || binary !== 0) $fatal(1, "reset mismatch");
        for (n = 0; n < 16384; n = n + 1) begin
            @(negedge clk); rst_n = 1; code = 14'(n);
            @(posedge clk); #1;
            reconstructed = int'(binary);
            for (j = 0; j < 31; j = j + 1) begin
                if (unary[j] !== (j < (n >> 9))) $fatal(1, "thermometer ordering mismatch code=%0d", n);
                if (unary[j]) reconstructed = reconstructed + 512;
            end
            if (reconstructed !== n) $fatal(1, "weighted code mismatch %0d vs %0d", reconstructed, n);
        end
        @(negedge clk); rst_n = 0;
        @(posedge clk); #1;
        if (unary !== 0 || binary !== 0) $fatal(1, "reset at full scale mismatch");
        $display("PASS: all 16384 codes, thermometer ordering and synchronous reset; functional 2 GHz stimulus only");
        $finish;
    end
    initial begin #10000000; $fatal(1, "timeout"); end
endmodule
