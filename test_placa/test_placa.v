// Diagnóstico independiente del procesador: reloj, displays, LEDs y botones.
module test_placa (
  input  wire       i_Clk,
  output wire [3:0] o_LED,
  input  wire [3:0] i_Switch,
  output wire       o_Segment1_A, o_Segment1_B, o_Segment1_C, o_Segment1_D,
  output wire       o_Segment1_E, o_Segment1_F, o_Segment1_G,
  output wire       o_Segment2_A, o_Segment2_B, o_Segment2_C, o_Segment2_D,
  output wire       o_Segment2_E, o_Segment2_F, o_Segment2_G,
  input  wire       i_SPI_SCLK,
  input  wire       i_SPI_MOSI,
  input  wire       i_SPI_CS_n,
  output wire       o_SPI_MISO
);
  reg [23:0] divider_q = 24'd0;
  reg [7:0]  count_q = 8'd0;

  // 12,500,000 cycles at 25 MHz = 0.5 seconds per count.
  always @(posedge i_Clk) begin
    if (divider_q == 24'd12_499_999) begin
      divider_q <= 24'd0;
      count_q   <= count_q + 8'd1;
    end else begin
      divider_q <= divider_q + 24'd1;
    end
  end

  assign o_LED = i_Switch;
  assign o_SPI_MISO = 1'b1;

  function [6:0] hex2seg;
    input [3:0] hex;
    begin
      case (hex)
        4'h0: hex2seg = 7'b0111111;
        4'h1: hex2seg = 7'b0000110;
        4'h2: hex2seg = 7'b1011011;
        4'h3: hex2seg = 7'b1001111;
        4'h4: hex2seg = 7'b1100110;
        4'h5: hex2seg = 7'b1101101;
        4'h6: hex2seg = 7'b1111101;
        4'h7: hex2seg = 7'b0000111;
        4'h8: hex2seg = 7'b1111111;
        4'h9: hex2seg = 7'b1101111;
        4'hA: hex2seg = 7'b1110111;
        4'hB: hex2seg = 7'b1111100;
        4'hC: hex2seg = 7'b0111001;
        4'hD: hex2seg = 7'b1011110;
        4'hE: hex2seg = 7'b1111001;
        4'hF: hex2seg = 7'b1110001;
        default: hex2seg = 7'b0000000;
      endcase
    end
  endfunction

  wire [6:0] seg1 = hex2seg(count_q[7:4]);
  wire [6:0] seg2 = hex2seg(count_q[3:0]);
  // Go Board seven-segment outputs are active-low.
  assign {o_Segment1_G, o_Segment1_F, o_Segment1_E, o_Segment1_D,
          o_Segment1_C, o_Segment1_B, o_Segment1_A} = ~seg1;
  assign {o_Segment2_G, o_Segment2_F, o_Segment2_E, o_Segment2_D,
          o_Segment2_C, o_Segment2_B, o_Segment2_A} = ~seg2;
endmodule
