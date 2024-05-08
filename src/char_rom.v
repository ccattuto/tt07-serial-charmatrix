module char_rom #(
    parameter DATA_WIDTH = 35,     // Width of ROM data (35 bits for each character)
    parameter ADDR_WIDTH = 7,      // Address width
    parameter ADDR_MIN = 32,
    parameter ADDR_MAX = 126
)(
    input wire [ADDR_WIDTH-1:0] address,
    output wire [DATA_WIDTH-1:0] data
);

reg [DATA_WIDTH-1:0] mem [0:ADDR_MAX-ADDR_MIN+2];

initial begin
    $readmemb("font.bin", mem);  // load char bitmaps from file
end

always @(address) begin
    if (address >= ADDR_MIN && address <= ADDR_MAX) begin
        data <= mem[address-ADDR_MIN];
    end else begin
        data <= mem[ADDR_MAX-ADDR_MIN+1];
    end
end

endmodule
