/*
 * Copyright (c) 2024 Ciro Cattuto
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ccattuto_charmatrix (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

// All output pins must be assigned. If not used, assign to 0.
assign uio_out = 0;
assign uio_oe  = 0;
assign uo_out[3:1] = 0;
assign uo_out[7:5] = 0;

// UART signals
wire uart_rx, uart_tx;
assign uart_rx = ui_in[3];
assign uart_tx = uo_out[4];

// LED strip signal
assign lde = uo_out[0];

// clock
wire clk20;
assign clk20 = clk;

// reset
wire boot_reset;
assign boot_reset = ~rst_n;

reg [19:0] counter = 0;
reg refresh_trigger = 0;

always @(posedge clk20) begin
  counter <= counter + 1;
  // trigger LED refresh every 2^16 ticks (~150 Hz)
  refresh_trigger <= (&counter[15:0] == 1) ? 1 : 0;
end

//wire uart_tx_en, uart_rx_en;
wire uart_rx_en;
//assign uart_tx_en = 1;
assign uart_rx_en = 1;

// // UART TX
// reg [7:0]   uart_tx_data;
// reg         uart_tx_valid;
// wire        uart_tx_ready;

// UART RX
wire [7:0]  uart_rx_data;
wire        uart_rx_valid;
wire        uart_rx_error;
wire        uart_rx_overrun;
reg         uart_rx_ready;

// UARTTransmitter #(
//     .CLOCK_RATE(24000000),
//     .BAUD_RATE(115200)
// ) uart_tx_inst (
//     .clk(clk48),
//     .reset(boot_reset),       // reset
//     .enable(uart_tx_en),      // TX enable
//     .valid(uart_tx_valid),    // start of TX
//     .in(uart_tx_data),        // data to transmit
//     .out(uart_tx),            // TX signal
//     .ready(uart_tx_ready)     // read for TX data
// );

UARTReceiver #(
    .CLOCK_RATE(20000000),
    .BAUD_RATE(9600)
) uart_rx_inst (
    .clk(clk20),
    .reset(boot_reset),        // reset
    .enable(uart_rx_en),      // RX enable
    .in(uart_rx),             // RX signal
    .ready(uart_rx_ready),    // ready to consume RX data
    .out(uart_rx_data),       // RX wires
    .valid(uart_rx_valid),    // RX completed
    .error(uart_rx_error),    // RX error
    .overrun(uart_rx_overrun) // RX overrun
);

  
reg [7:0] char_index;
wire [34:0] char_data;

reg [3:0] color_index;
wire [23:0] color_data;

char_rom #(.DATA_WIDTH(35), .ADDR_WIDTH(8)) led_rom (
    .address(char_index),
    .data(char_data)
);

color_rom #(.DATA_WIDTH(24), .ADDR_WIDTH(4)) col_rom (
    .address(color_index),
    .data(color_data)
);

wire led;
reg valid = 0;
wire ready;
reg latch = 0;

ws2812b_driver ws2812b (
  .clk20(clk20),            // 20 MHz input clock
  .reset(boot_reset),
  .data_in(data),
  .valid(valid),
  .latch(latch),
  .ready(ready),
  .led(led)                 // Output signal to the LED strip
);

localparam IDLE = 0, LOAD_DATA = 1, WAIT_READY = 2, WAIT_STARTED = 3;
reg [2:0] state;

localparam NUM_LEDS = 140;
reg [7:0] led_index;
reg [7:0] char_led_index;
reg [23:0] data;

always @(posedge clk20) begin
  if (boot_reset) begin
    led_index <= 0;
    char_led_index <= 0;
    data <= 24'b0;
    state <= IDLE;
  end else begin
    case (state)
      IDLE: begin
        led_index <= 0;
        char_led_index <= 0;
        textbuf_index <= 0;
        valid <= 0;
        latch <= 0;
        char_index <= textbuf[textbuf_index];
        color_index <= colorbuf[textbuf_index];
        if (refresh_trigger) begin
          state <= LOAD_DATA;
        end
      end

      LOAD_DATA: begin
        data <= (char_data[char_led_index]) ? color_data : 24'b0;

        latch <= (led_index == NUM_LEDS - 1) ? 1 : 0;

        state <= WAIT_READY;
      end

      WAIT_READY: begin
        if (ready) begin
          valid <= 1;

          if (char_led_index < 35-1) begin
            char_led_index <= char_led_index + 1;
          end else begin
            char_led_index <= 0;
            textbuf_index <= textbuf_index + 1;
            char_index <= textbuf[textbuf_index + 1];
            color_index <= colorbuf[textbuf_index + 1];
          end

          led_index <= led_index + 1;

          state <= WAIT_STARTED;
        end
      end

      WAIT_STARTED: begin
        if (!ready) begin
          valid <= 0;

          if (led_index < NUM_LEDS) begin
            state <= LOAD_DATA;
          end else begin
            state <= IDLE;
          end
        end
      end
    endcase
  end
end

reg [7:0] textbuf[0:3];
reg [3:0] colorbuf[0:3];
reg [0:3] textbuf_index;


wire rng;
reg [3:0] rnd_color; // 4-bit shift register
always @(posedge counter[16]) begin
  rnd_color <= {rnd_color[2:0], rng};
end

lfsr_rng lfsr(
  .clk(counter[16]),
  .reset(boot_reset),
  .random_bit(rng)
);

reg [2:0] digit_index;

always @(posedge clk20) begin
  if (boot_reset) begin
    uart_rx_ready <= 0;
    digit_index <= 0;
    textbuf[0] <= 48;
    textbuf[1] <= 49;
    textbuf[2] <= 50;
    textbuf[3] <= 51;
    colorbuf[0] <= 0;
    colorbuf[1] <= 1;
    colorbuf[2] <= 2;
    colorbuf[3] <= 3;
  end else begin
    if (!(uart_rx_valid & uart_rx_ready)) begin
      uart_rx_ready <= 1; 
    end else begin        
      uart_rx_ready <= 0;
      rgb_led0_r <= ~rgb_led0_r;
      textbuf[digit_index] <= uart_rx_data;
      colorbuf[digit_index] <= rnd_color;
      if (digit_index == 3) begin
        digit_index <= 0;
      end else begin
        digit_index <= digit_index + 1;
      end
    end
  end
end

endmodule
