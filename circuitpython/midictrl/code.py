# SPDX-FileCopyrightText: Copyright (c) 2024 Tod Kurt
# SPDX-License-Identifier: MIT
"""
picotouch_bizcard_midictrl.py -- 
10 Jun 2024 - @todbot / Tod Kurt
Part of https://github.com/todbot/picotouch_bizcard
"""

import time, random
import board
import busio
import pwmio
import touchio
import usb_midi
import tmidi  # https://github.com/todbot/CircuitPython_TMIDI

enable_pressure = True
press_min = 1500
press_range = 1024

midi_chan = 1  # which MIDI channel to send on
midi_octave = 4  # adjust up/dwon with X- and O- keys

# possible scales, must all be 8 in length
scale_major = (0, 2, 4, 5,  7, 9, 11, 12)  # major / iolian
scale_minor = (0, 2, 3, 5,  7, 9, 11, 12)
scale_blues = (0, 3, 5, 6,  7, 10, 12, 15)  # blues
scale_mixolydian = (0, 2, 4, 5,  7, 9, 10, 12) # mixolydian
scale_pentatonic = (0, 3, 5, 7,  10, 12, 15, 17)

midi_scale = scale_pentatonic

pad_to_scale = (4,5,6,7, 0,1,2,3)   # map pad index to scale 

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

uart = busio.UART(tx=midi_out_pin, baudrate=31250, timeout=0.0001)

midi_uart = tmidi.MIDI(midi_out=uart)
midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])


touchins = []
leds = []
num_pads = len(touch_pins)

for pin in touch_pins:
    touchin = touchio.TouchIn(pin)
    touchins.append(touchin)

for pin in led_pins:
    led = pwmio.PWMOut(pin, frequency=25000, duty_cycle=0)
    leds.append(led)

def gamma_correct(x):
    """simple and dumb brightness gamma-correction, for 0.0-1.0"""
    return (x*x)

def set_led(n, val=1.0):
    leds[n].duty_cycle = int(65535 * gamma_correct(val))

def set_all_leds(val=1.0):
    val = int(65535 * gamma_correct(val))
    for led in leds:
        led.duty_cycle = val
    
def dim_all_leds(amount=0.95):
    """Dim all LEDs by an amount"""
    for led in leds:
        led.duty_cycle = int(led.duty_cycle * amount)

def note_on(notenum):
    print("note on :", notenum)
    msg_on = tmidi.Message(tmidi.NOTE_ON, midi_chan - 1, notenum, 127)
    midi_usb.send(msg_on)

def note_off(notenum):
    print("note off:", notenum)
    msg_off = tmidi.Message(tmidi.NOTE_OFF, midi_chan - 1, notenum, 0)
    midi_usb.send(msg_off)

def send_mod_wheel(amount):
    msg_cc = tmidi.Message(tmidi.CC, midi_chan - 1, 1, int(amount) )
    midi_usb.send(msg_cc)


print("picotouch_bizcard_midictrl: startup demo")
demo_cnt = 3
i = 0
demo_led_map = (0,1,2,3, 8,9,10, 7,6,5,4)  # circle around clockwise
for j in range(demo_cnt):
    for i in range(num_pads):
        set_led(demo_led_map[i], 1)
        dim_all_leds(0.7)
        time.sleep(0.02)


print("picotouch_bizcard_midictrl: ready")
last_time = 0
key_pressed = [False] * num_pads
note_pressed = [0] * num_pads
key_rawval = [0] * num_pads  # for pressure

while True:
    now = time.monotonic()
    if now - last_time > 0.2:
        last_time = now
        print(now, [int(t.value) for t in touchins])

    for i, t in enumerate(touchins):
        tv = t.value
        if tv:
            set_led(i, 1)

        # do a polyphonic aftertouch
        if enable_pressure and tv and key_pressed[i]:
            dr = min(max((t.raw_value - key_rawval[i]) - press_min, 0), press_range)
            if dr:
                print("dr:", dr)
                set_all_leds( dr/press_range )
                send_mod_wheel( dr/press_range * 127 )

        if tv and not key_pressed[i]:  # key pressed
            if i < 8:  # note keys
                notenum = midi_octave * 12 + midi_scale[pad_to_scale[i]]
                note_on(notenum)
                note_pressed[i] = notenum
                key_rawval[i] = t.raw_value
            elif i==8:
                print("X key: octave up")
                midi_octave = min(midi_octave+1, 8)
            elif i==9:  # <> key
                send_mod_wheel(127)
            elif i==10:
                print("O key: octave down")
                midi_octave = max(midi_octave-1, 1) 
                    
        if not tv and key_pressed[i]:  # key released
            if i < 8:
                notenum = note_pressed[i]
                note_off(notenum)
            elif i==9: # <> key
                send_mod_wheel(0)
                
                
        key_pressed[i] = tv

    dim_all_leds(0.95)
    
