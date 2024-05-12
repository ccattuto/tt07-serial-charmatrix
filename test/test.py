# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
import cocotb.result
from cocotb.triggers import Timer, Edge, with_timeout
from cocotb.utils import get_sim_time
import random


@cocotb.test(timeout_time=25, timeout_unit='ms')
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 50 ns (20 MHz)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # signals
    uart_rx = dut.ui_in[3]
    led = dut.uo_out[0]

    # reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    uart_rx.value = 1 # keep RX high
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await Timer(1, units="us")
    dut.rst_n.value = 1
    await Timer(1, units="us")

    assert led.value == 0

    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)

    await Timer(1.2, units="ms")
    await do_tx(uart_rx, 9600, ord('A'))
    #await Edge(dut.user_project.uart_rx_ready)
    #assert dut.user_project.uart_rx_ready.value == 1

    c1 = await get_char(dut, led)
    c2 = await get_char(dut, led)
    c3 = await get_char(dut, led)
    c4 = await get_char(dut, led)


async def do_tx(uart_rx, baud, data):
    # prepare random test data
    TEST_BITS_LSB = [(data >> s) & 1 for s in range(8)]

    # send start bit (0), 8 data bits, stop bit (1)
    for tx_bit in [0] + TEST_BITS_LSB + [1]:
        uart_rx.value = tx_bit
        await Timer(int(1.0 / baud * 1e12), units="ps")

async def get_char(dut, led):
    cseq = []
    for count in range(35):
        bitseq = await get_24bits(dut, led)
        dut._log.info(f"{count}: {bitseq}")
        cseq.append( 0 if sum(bitseq) == 0 else 1 )

    for i in range(7):
        linestring = "".join(["O" if x==1 else "." for x in cseq[i*5:(i+1)*5]])
        dut._log.info(linestring)

    return "".join([str(x) for x in cseq])
        
async def get_24bits(dut, led):
    bitseq = []

    for i in range(24):
        while led.value == 0:
            await Edge(dut.uo_out)
        t1 = get_sim_time('ns')
        
        while led.value == 1:
            await Edge(dut.uo_out)
        t2 = get_sim_time('ns')

        pulse_ns = t2-t1
        assert(pulse_ns > 300)
        assert(pulse_ns < 900)
        #dut._log.info(pulse_ns)

        bitseq.append( 1 if (pulse_ns > 625) else 0 )

    return bitseq

async def ledreset(dut, led):
    reset_detected = 0
    while not reset_detected:
        while led.value == 1:
            await Edge(dut.uo_out)
        try:
            await with_timeout(Edge(dut.uo_out), 50, 'us')
        except cocotb.result.SimTimeoutError:
            reset_detected = 1
    