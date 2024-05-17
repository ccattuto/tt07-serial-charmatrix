# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
import cocotb.result
from cocotb.triggers import Timer, Edge, with_timeout
from cocotb.utils import get_sim_time
import random


@cocotb.test(timeout_time=50, timeout_unit='ms')
async def test_2chars(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # GPIO config
    do_gpio_config(dut, num_chars=2)

    # reset
    await do_reset(dut)

    assert led.value == 0

    # wait for LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    await check_led_reset(dut, led)

    assert c1.bitmap == get_char_bitmap(0)
    assert c2.bitmap == get_char_bitmap(0)
    
    # send byte over UART
    await Timer(1.2, units="ms")
    dut._log.info("Sending: C")
    await do_tx(uart_rx, 9600, ord('C'))

    # send two more bytes over UART
    await Timer(0.3, units="ms")
    dut._log.info("Sending: ir")
    await do_tx(uart_rx, 9600, ord('i'))
    await do_tx(uart_rx, 9600, ord('r'))

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(ord('i'))
    assert c2.bitmap == get_char_bitmap(ord('r'))

    # send one more byte over UART
    dut._log.info("Sending: o")
    await do_tx(uart_rx, 9600, ord('o'))

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(ord('r'))
    assert c2.bitmap == get_char_bitmap(ord('o'))


@cocotb.test(timeout_time=50, timeout_unit='ms')
async def test_4chars(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # GPIO config
    do_gpio_config(dut, num_chars=4)

    # reset
    await do_reset(dut)

    assert led.value == 0

    # wait for LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(0)
    assert c2.bitmap == get_char_bitmap(0)
    assert c3.bitmap == get_char_bitmap(0)
    assert c4.bitmap == get_char_bitmap(0)

    # send byte over UART
    await Timer(1.2, units="ms")
    dut._log.info("Sending: C")
    await do_tx(uart_rx, 9600, ord('C'))

    # send two more bytes over UART
    await Timer(0.3, units="ms")
    dut._log.info("Sending: ir")
    await do_tx(uart_rx, 9600, ord('i'))
    await do_tx(uart_rx, 9600, ord('r'))

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(0)
    assert c2.bitmap == get_char_bitmap(ord('C'))
    assert c3.bitmap == get_char_bitmap(ord('i'))
    assert c4.bitmap == get_char_bitmap(ord('r'))

    # send two more bytes over UART
    dut._log.info("Sending: oX")
    await do_tx(uart_rx, 9600, ord('o'))
    await do_tx(uart_rx, 9600, ord('X'))

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(ord('i'))
    assert c2.bitmap == get_char_bitmap(ord('r'))
    assert c3.bitmap == get_char_bitmap(ord('o'))
    assert c4.bitmap == get_char_bitmap(ord('X'))


@cocotb.test(timeout_time=60, timeout_unit='ms')
async def test_8chars(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # GPIO config
    do_gpio_config(dut, num_chars=8)

    # reset
    await do_reset(dut)

    assert led.value == 0

    # wait for LED matrix update
    clist = []
    for i in range(8):
        clist.append( await get_char(dut, led) )
    await check_led_reset(dut, led)
    assert [c.bitmap for c in clist] == [get_char_bitmap(0)] * 8

    # send 9 bytes over UART
    for i in range(10):
        dut._log.info(f"Sending: {i}")
        await do_tx(uart_rx, 9600, ord('0') + i)

    # wait for next refresh
    await wait_led_reset(dut, led)

    # parse LED matrix update
    clist = []
    for i in range(8):
        clist.append( await get_char(dut, led) )
    await check_led_reset(dut, led)

    # check LED matrix state
    assert [c.bitmap for c in clist] == [get_char_bitmap(ord('2') + i) for i in range(8)]


@cocotb.test(timeout_time=10, timeout_unit='ms')
async def test_uart_loopback(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    uart_tx = dut.uo_out[4]

    # GPIO config
    do_gpio_config(dut, uart_loopback=1)

    # reset
    await do_reset(dut)

    # send byte to UART receiver
    await Timer(0.1, units="ms")
    TEST_BYTE = 0xA5
    dut._log.info("Sending: 0xA5")
    await do_tx(uart_rx, 9600, TEST_BYTE)

    # check byte from UART transmitter
    rx_byte = await do_rx(dut, uart_tx, 9600)
    dut._log.info("Received 0x%02X" % rx_byte)
    assert rx_byte == TEST_BYTE


async def trigger_refresh(dut, uart_rx):
    dut._log.info("Sending CR")
    await do_tx(uart_rx, 9600, 13)

@cocotb.test(timeout_time=50, timeout_unit='ms')
async def test_uart_refresh(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # GPIO config
    do_gpio_config(dut, num_chars=2, ext_refresh=1)

    # reset
    await do_reset(dut)

    assert led.value == 0

    # send 4 bytes over UART
    await Timer(0.2, units="ms")
    dut._log.info("Sending: Hiya")
    await do_tx(uart_rx, 9600, ord('H'))
    await do_tx(uart_rx, 9600, ord('i'))
    await do_tx(uart_rx, 9600, ord('y'))
    await do_tx(uart_rx, 9600, ord('a'))

    # check that matrix does not refresh
    dut._log.info("Wait for 20 ms...")
    did_timeout = False
    try:
        await with_timeout(Edge(dut.uo_out), 20, 'ms')
    except cocotb.result.SimTimeoutError:
        did_timeout = True
        dut._log.info("Correctly timed out")
    assert did_timeout
    assert led.value == 0

    # send CR over UART to trigger refresh
    f = cocotb.start_soon(trigger_refresh(dut, uart_rx))

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    await check_led_reset(dut, led)
    await f

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(ord('y'))
    assert c2.bitmap == get_char_bitmap(ord('a'))


@cocotb.test(timeout_time=50, timeout_unit='ms')
async def test_uart_color(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # GPIO config
    do_gpio_config(dut, num_chars=4, fixed_color=1)

    # reset
    await do_reset(dut)

    assert led.value == 0

    # wait for LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(0)
    assert c2.bitmap == get_char_bitmap(0)
    assert c3.bitmap == get_char_bitmap(0)
    assert c4.bitmap == get_char_bitmap(0)

    assert c1.color == COLOR_LIST[0]
    assert c2.color == COLOR_LIST[0]
    assert c3.color == COLOR_LIST[0]
    assert c4.color == COLOR_LIST[0]

    # send color command + printable chars over UART
    await Timer(0.25, units="ms")
    dut._log.info("Sending: [color 7] Da")
    await do_tx(uart_rx, 9600, 0x80 | 0x07)
    await do_tx(uart_rx, 9600, ord('D'))
    await do_tx(uart_rx, 9600, ord('a'))

    # send color command + printable char over UART
    dut._log.info("Sending: [color 10] n")
    await do_tx(uart_rx, 9600, 0x80 | 0x0A)
    await do_tx(uart_rx, 9600, ord('n'))

    # send color command + printable char over UART
    dut._log.info("Sending: [color 15] i")
    await do_tx(uart_rx, 9600, 0x80 | 0x0F)
    await do_tx(uart_rx, 9600, ord('i'))

    # wait for next refresh
    await wait_led_reset(dut, led)

    # parse LED matrix update
    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)
    await check_led_reset(dut, led)

    # check LED matrix state
    assert c1.bitmap == get_char_bitmap(ord('D'))
    assert c2.bitmap == get_char_bitmap(ord('a'))
    assert c3.bitmap == get_char_bitmap(ord('n'))
    assert c4.bitmap == get_char_bitmap(ord('i'))

    assert c1.color == COLOR_LIST[7]
    assert c2.color == COLOR_LIST[7]
    assert c3.color == COLOR_LIST[10]
    assert c4.color == COLOR_LIST[15]


# HELPER FUNCTIONS

async def do_reset(dut):
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.rst_n.value = 0
    await Timer(1, units="us")
    dut.rst_n.value = 1
    await Timer(1, units="us")

def do_gpio_config(dut, num_chars=2, uart_loopback=0, led_dimmer=0, ext_refresh=0, fixed_color=0):
    dut._log.info("GPIO config")
    # GPIO IN
    dut.ui_in.value = 0
    # keep RX high
    dut.ui_in[3].value = 1
    # config: UART loopback
    dut.ui_in[2].value = uart_loopback
    # config: num chars
    dut.ui_in[0].value = (num_chars // 2 - 1) & 1
    dut.ui_in[1].value = (num_chars // 2 - 1) >> 1
    # config: no LED dimmer
    dut.ui_in[4].value = led_dimmer & 1
    dut.ui_in[5].value = led_dimmer >> 1
    # config: internal/external refresh trigger
    dut.ui_in[6].value = ext_refresh
    # config: random/fixed character color
    dut.ui_in[7].value = fixed_color

    # GPIO IN/OUT
    dut.uio_in.value = 0

CHAR_ROM = [s.strip()[::-1] for s in open('font.bin').readlines()]
def get_char_bitmap(c):
    if c >= 32 and c <= 126:
        i = c - 32
    else:
        i = -1
    return CHAR_ROM[i]

COLOR_LIST = [
    "000000001100110000000000",
    "010011001100110000000000",
    "100110011100110000000000",
    "110011001011001000000000",
    "110011000110011000000000",
    "110011000001100100000000",
    "110011000000000000110011",
    "110011000000000001111111",
    "110011000000000011001100",
    "011111110000000011001100",
    "001100110000000011001100",
    "000000000001100111001100",
    "000000000110011011001100",
    "000000001011001011001100",
    "000000001100110010011001",
    "000000001100110001001100"
]

async def do_tx(uart_rx, baud, data):
    # prepare random test data
    TEST_BITS_LSB = [(data >> s) & 1 for s in range(8)]

    # send start bit (0), 8 data bits, stop bit (1)
    for tx_bit in [0] + TEST_BITS_LSB + [1]:
        uart_rx.value = tx_bit
        await Timer(int(1.0 / baud * 1e12), units="ps")

async def do_rx(dut, uart_tx, baud):
    await Edge(dut.uo_out)
    assert uart_tx.value == 0

    # wait 1/2 bit
    await Timer(int(0.5 / baud * 1e12), units="ps")
    # check start bit
    assert uart_tx.value == 0

    # 8 data bits
    data = 0
    for i in range(8):
        await Timer(int(1.0 / baud * 1e12), units="ps")
        data = (data << 1) | (1 if uart_tx.value == 1 else 0)

    # check stop bit
    await Timer(int(1.0 / baud * 1e12), units="ps")
    assert uart_tx.value == 1

    return data

# class to hold character's bitmap & color
class Char():
    def __init__(self, bitmap, color):
        self.bitmap = bitmap
        self.color = color

# read 5x7 character
async def get_char(dut, led):
    cseq = []
    color_set = set()
    for count in range(35):
        bitseq = await get_GRB(dut, led)
        if sum(bitseq):
            cseq.append(1)
            color_set.add("".join([str(x) for x in bitseq]))
        else:
            cseq.append(0)
        dut._log.info(f"{count}: {bitseq}")

    # same color for all LEDS in a given character, and a valid color
    assert len(color_set) == 1
    assert list(color_set)[0] in COLOR_LIST

    # print character
    print()
    for i in range(7):
        linestring = "".join(["O" if x==1 else "." for x in cseq[i*5:(i+1)*5]])
        dut._log.info(linestring)
    print()

    bitmap = "".join([str(x) for x in cseq])
    color = list(color_set)[0]

    return Char(bitmap, color)

# read 24 color bits (G / R / B)
async def get_GRB(dut, led):
    bitseq = []

    for i in range(24):
        while led.value == 0:
            await Edge(dut.uo_out)
        t1 = get_sim_time('ns')

        while led.value == 1:
            await Edge(dut.uo_out)
        t2 = get_sim_time('ns')

        pulse_ns = t2-t1
        # check pulse duration
        assert pulse_ns > 300
        assert pulse_ns < 900

        # decode bit
        bitseq.append( 1 if (pulse_ns > 625) else 0 )

    return bitseq

async def check_led_reset(dut, led):
        did_timeout = False
        assert led.value == 0
        try:
            await with_timeout(Edge(dut.uo_out), 50, 'us')
        except cocotb.result.SimTimeoutError:
            did_timeout = True
        
        assert did_timeout
        assert led.value == 0

async def wait_led_reset(dut, led):
        low_time = 0
        while low_time < 50:
            try:
                await with_timeout(Edge(dut.uo_out), 1, 'us')
                if led.value == 1:
                    low_time = 0
            except cocotb.result.SimTimeoutError:
                if led.value == 0:
                    low_time += 1
            