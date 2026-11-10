// SPDX-License-Identifier: MIT
`default_nettype none
module bringup_counter (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       enable,
    output reg  [7:0] count
);
    // Synchronous, active-low reset. This is an environment smoke-test block.
    always @(posedge clk) begin
        if (!rst_n)
            count <= 8'd0;
        else if (enable)
            count <= count + 8'd1;
    end
endmodule
`default_nettype wire
