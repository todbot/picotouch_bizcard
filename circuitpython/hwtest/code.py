# SPDX-FileCopyrightText: Copyright (c) 2024 Tod Kurt
# SPDX-License-Identifier: MIT
"""
picotouch_bizcard_hwtest.py -- 
10 Jun 2024 - @todbot / Tod Kurt
Part of https://github.com/todbot/picotouch_bizcard
"""

import time, random
import board
import busio
import pwmio
import touchio
import usb_midi
import tmidi

touch_pins = (
    board.GP2, board.GP3, board.GP4, board.GP5,
    board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11,
    board.GP12
)

led_pins = (
    board.GP13, board.GP14, board.GP15, board.GP16, board.GP17,
    board.GP18, board.GP19,  board.GP21,
    board.GP27, board.GP26, board.GP22
)

midi_out_pin = board.GP20

midi_uart = busio.UART(tx=midi_out_pin, baudrate=31250, timeout=0.0001)

touchins = []
leds = []
num_leds = len(led_pins)

for pin in touch_pins:
    touchin = touchio.TouchIn(pin)
    touchins.append(touchin)

for pin in led_pins:
    led = pwmio.PWMOut(pin, frequency=25000, duty_cycle=0)
    leds.append(led)

def set_led(n, val=1.0):
    leds[n].duty_cycle = int(65535 * val)
    
def dim_all_leds(amount=0.95):
    """Dim all LEDs by an amount"""
    for led in leds:
        led.duty_cycle = int(led.duty_cycle * amount)

print("picotouch_bizcard_hwtest: startup demo")
i = 0
demo_led_map = (0,1,2,3, 8,9,10, 7,6,5,4)  # circle around clockwise
for j in range(5):
    for i in range(num_leds):
        set_led(demo_led_map[i], 1)
        dim_all_leds(0.7)
        time.sleep(0.03)

print("picotouch_bizcard_hwtest: ready")
last_time = 0
while True:
    now = time.monotonic()
    if now - last_time > 0.2:
        last_time = now
        print(now, [int(t.value) for t in touchins])

    for i, t in enumerate(touchins):
        if t.value:
            set_led(i, 1)

    dim_all_leds(0.95)
    
