module char_rom #(
    parameter DATA_WIDTH = 35,     // Width of ROM data (35 bits for each character)
    parameter ADDR_WIDTH = 8       // Address width
)(
    input wire [ADDR_WIDTH-1:0] address,
    output wire [DATA_WIDTH-1:0] data
);

reg [DATA_WIDTH-1:0] mem [0:2**ADDR_WIDTH-1];

integer i;
initial begin
    //for (i = 0; i < 2**ADDR_WIDTH; i++) begin
    //    mem[i] = {DATA_WIDTH{1'b0}};
    //end
    $readmemb("font.bin", mem);  // load char bitmaps from file
end

assign data = mem[address];

endmodule
