// SPDX-License-Identifier: MIT
// Functional segmentation only. No 2 GHz physical timing closure is implied.
`default_nettype none
module dac14_segment_decoder (
    input wire clk,
    input wire rst_n,
    input wire [13:0] code,
    output reg [30:0] unary,
    output reg [8:0] binary
);
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            unary <= 31'd0;
            binary <= 9'd0;
        end else begin
            binary <= code[8:0];
            for (i = 0; i < 31; i = i + 1)
                unary[i] <= (code[13:9] > 5'(i));
        end
    end
endmodule
`default_nettype wire
