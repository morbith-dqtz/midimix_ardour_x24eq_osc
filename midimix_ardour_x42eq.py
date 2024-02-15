#!/usr/bin/env python3
#-*- coding:utf-8 -*-

"""
midimix_ardour_x42eq OSC

Copyright (C) 2024  Morbith Darklink QofTzade

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

midimix_ardour_x42eq implements a OSC interface betwen Ardour DAW /
x42 EQ and AKAI MIDIMIX surface

x42 Parametric EQ module
https://github.com/x42/fil4.lv2

Usually shipped with x42-plugins in your preferred linux distro

Ardour Digital Audio Workstation
https://github.com/Ardour/ardour

AKAI MIDIMIX
https://www.akaipro.com/midimix

> MIX/EQ modes toggling with SOLO + strip on MIDIMIX
> Controls up to 8 EQs per strip
> Support 3 banks for 8 strip pagination
> Uses JACK as rtmidi backend

Ardour OSC must be enabled :
Preferences / Control Surfaces / Open Sound Control

MIX main controls :

* REC/MUTE using the labeled MIDIMIX buttons
* 1st line of knobs conrols the gain of each strip
* 2nd line of knobs conrols the panning of each strip
* 3rd line of knobs enables solo of each strip (+50 to trigger on)
* faders controls the volume of each strip
* bank UP/DOWN with BANK RIGHT/BANK LEFT on MIDIMIX
* MASTER controls the master volume

EQ mode for x42-EQ :

'Output Gain'     : fader at MIDIMIX strip 1
'Enable'          : REC  on MIDIMIX strip 1
'Reset Peak Hold' : REC  on MIDIMIX strip 2

'Highpass'        : MUTE on MIDIMIX strip 1
'High pass freq'  : 1st knob at MIDIMIX strip 1
'High pass Q'     : 2nd knob at MIDIMIX strip 1

'Lowpass'         : MUTE on MIDIMIX strip 2
'Lowpass freq'    : 1st knob at MIDIMIX strip 2
'Lowpass Q'       : 2nd knob on MIDIMIX strip 2

'Lowshelf'        : MUTE on MIDIMIX strip 3
'Lowshelf freq'   : 1st knob on MIDIMIX strip 3
'Lowshelf Q'      : 2nd knob on MIDIMIX strip 3
'Lowshelf Gain'   : fader at MIDIMIX strip 3

'Section 1'       : MUTE on MIDIMIX strip 4
'Section 1 freq'  : 1st knob on MIDIMIX strip 4
'Section 1 Q'     : 2nd knob on MIDIMIX strip 4
'Section 1 Gain'  : fader on MIDIMIX strip 4

'Section 2'       : MUTE on MIDIMIX strip 5
'Section 2 freq'  : 1st knob on MIDIMIX strip 5
'Section 2 Q'     : 2nd knob on MIDIMIX strip 5
'Section 2 Gain'  : fader on MIDIMIX strip 5

'Section 3'       : MUTE on MIDIMIX strip 6
'Section 3 freq'  : 1st knob on MIDIMIX strip 6
'Section 3 Q'     : 2nd knob on MIDIMIX strip 6
'Section 3 Gain'  : fader on MIDIMIX strip 6

'Section 4'       : MUTE on MIDIMIX strip 7
'Section 4 freq'  : 1st knob on MIDIMIX strip 7
'Section 4 Q'     : 2nd knob on MIDIMIX strip 7
'Section 4 Gain'  : fader on MIDIMIX strip 7

'Highshelf'       : MUTE on MIDIMIX strip 8
'Highshelf freq'  : 1st knob on MIDIMIX strip 8
'Highshelf Q'     : 2nd knob on MIDIMIX strip 8
'Highshelf Gain'  : fader on MIDIMIX strip 8

At EQ mode you can still adjust some MIX controls :

MIX strip volume with MIDIMIX Master fader
MIX triger SOLO with 3rd knob at strip 8 (+50 enables SOLO)
MIX panning with 3rd knob at strip 1
MIX mute with MIDIMIX MUTE at strip 8
"""

import rtmidi
import mido
import asyncio
import aiosc
import time
import sys
import signal
import argparse
from threading import Thread

faders         = ( 19, 23, 27, 31, 49, 53, 57, 61, 62 )
mutes          = ( 1, 4, 7, 10, 13, 16, 19, 22 )
recs           = ( 3, 6, 9, 12, 15, 18, 21, 24 )
knobs          = ( 16, 17, 18, 20, 21, 22, 24, 25, 26,
                  28, 29, 30, 46, 47, 48, 50, 51, 52,
                  54, 55, 56, 58, 59, 60)
b_left         = 25
b_right        = 26
b_solo         = 27

tick_time      = 0.001
osc            = None
transport      = None
loop           = None
check_running  = False
respawn        = True
get_note       = None

note_press     = { 'note' :  None,  'state' : False }
operation      = { 'mode' : 'mixer', 'strip' : None , 'plugin_pos' : None }
plugin_list    = ()
plugin_desc    = ()

bank = {
'current' : 0,
0 :  { 'led_stat_mix' : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
	19 : False, 21 : False, 22 : False, 24 : False
	},
	'led_stat_eq'  : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
  19 : False, 21 : False, 22 : False, 24 : False
	},
},
1 :  { 'led_stat_mix' : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
	19 : False, 21 : False, 22 : False, 24 : False
	},
	'led_stat_eq'  : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
	19 : False, 21 : False, 22 : False, 24 : False
	},
},
2 :  { 'led_stat_mix' : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
	19 : False, 21 : False, 22 : False, 24 : False
	},
	'led_stat_eq'  : {
	1  : False, 3  : False, 4  : False, 6  : False,
	7  : False, 9  : False, 10 : False, 12 : False,
	13 : False, 15 : False, 16 : False, 18 : False,
	19 : False, 21 : False, 22 : False, 24 : False
	},
}
}

eq_leds = {
'Enable'          : { 'led'    :  3 },
'Reset Peak Hold' : { 'led'    :  6 },
'Highpass'        : { 'led'    :  1 },
'Lowpass'         : { 'led'    :  4 },
'Lowshelf'        : { 'led'    :  7 },
'Section 1'       : { 'led'    : 10 },
'Section 2'       : { 'led'    : 13 },
'Section 3'       : { 'led'    : 16 },
'Section 4'       : { 'led'    : 19 },
'Highshelf'       : { 'led'    : 22 },
}

eq_led_trigger = {
3  : { 'option' :  1 },
6  : { 'option' :  4 },
1  : { 'option' :  5 },
4  : { 'option' :  8 },
7  : { 'option' :  11 },
10 : { 'option' :  15 },
13 : { 'option' :  19 },
16 : { 'option' :  23 },
19 : { 'option' :  27 },
22 : { 'option' :  31 }
}

eq_fad_knob  = {
# highpass
16 : { 'min' :    5.00000, 'incremento' :   9.803100, 'plugin_opt' :  6 },
17 : { 'min' :    0.00000, 'incremento' :   0.011020, 'plugin_opt' :  7 },
# lowpass
20 : { 'min' :  500.00000, 'incremento' : 153.543300, 'plugin_opt' :  9 },
21 : { 'min' :    0.00000, 'incremento' :   0.011020, 'plugin_opt' : 10 },
# low shelf
24 : { 'min' :   25.00000, 'incremento' :   2.952750, 'plugin_opt' : 12 },
25 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 13 },
27 : { 'min' :  -18.00000, 'incremento' :   0.283464, 'plugin_opt' : 14 },
# frequency 1
28 : { 'min' :   20.00000, 'incremento' :  15.590550, 'plugin_opt' : 16 },
29 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 17 },
31 : { 'min' :	-18.00000, 'incremento'	:   0.283464, 'plugin_opt' : 18 },
# frequency 2
46 : { 'min' :   40.00000, 'incremento' :  31.181100, 'plugin_opt' : 20 },
47 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 21 },
49 : { 'min' :	-18.00000, 'incremento'	:   0.283464, 'plugin_opt' : 22 },
# frequency 3
50 : { 'min' :  100.00000, 'incremento' :  77.952750, 'plugin_opt' : 24 },
51 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 25 },
53 : { 'min' :  -18.00000, 'incremento' :   0.283464, 'plugin_opt' : 26	},
# frequency 4
54 : { 'min' :  200.00000, 'incremento' : 155.905510, 'plugin_opt' : 28 },
55 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 29 },
57 : { 'min' :  -18.00000, 'incremento' :   0.283464, 'plugin_opt' : 30	},
# highshelf
58 : { 'min' : 1000.00000, 'incremento' : 118.110200, 'plugin_opt' : 32 },
59 : { 'min' :    0.06250, 'incremento' :   0.031000, 'plugin_opt' : 33 },
61 : { 'min' :  -18.00000, 'incremento' :   0.283464, 'plugin_opt' : 34 },
# general gain
19 : { 'min' :  -18.00000, 'incremento' :   0.283464, 'plugin_opt' :  2 }
}

def signal_handler(sig, frame):
	global respawn
	global loop
	print('')
	print('ByeBye, mix you later!')
	respawn = False
	apaga_leds()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def reset_bank_state():
	global bank
	for current in [ bank[0], bank[1], bank[2] ]:
		for mix_mode in [ current['led_stat_mix'], current['led_stat_eq'] ]:
			for led in mix_mode:
				mix_mode[led] = False
	set_led_status()

def apaga_leds():
	apaga_led(b_right)
	apaga_led(b_left)
	for led in bank[0]['led_stat_mix']:
		apaga_led(led)

def enciende_led(led):
	note = mido.Message('note_on', channel=0, note=led, velocity=127)
	mmix_out.send(note)

def apaga_led(led):
	note = mido.Message('note_on', channel=0, note=led, velocity=0)
	mmix_out.send(note)

def get_plugin_list(*args):
	global plugin_list
	plugin_list = args

def get_plugin_desc(*args):
	global plugin_desc
	plugin_desc = plugin_desc + (args, )

def set_mixer_mode():
	operation['mode']       = 'mixer'
	operation['strip']      = None
	operation['plugin_pos'] = None
	apaga_led(b_left)
	apaga_led(b_right)
	set_led_status()
	return None

def espera_indice_modulo_eq(note = None):
	global operation
	global plugin_desc
	if note not in recs:
		if debug:
			print("That button is not a valid choice")
		return

	pos_modulo = recs.index(note)

	if((pos_modulo + 1) > len(operation['plugin_pos'])):
		if debug:
			print("That button is not a valid choice")
		return

	operation['plugin_pos'] = operation['plugin_pos'][pos_modulo]

	if debug:
		print("Entering EQ mode for strip {} at {}".format(operation['strip'],operation['plugin_pos'] ))


	operation['mode'] = 'EQ'
	osc.send('/strip/plugin/descriptor', operation['strip'], operation['plugin_pos'])
	time.sleep(tick_time * 10)

	current = bank['current']

	for led in bank[current]['led_stat_eq'].keys():
		bank[current]['led_stat_eq'][led] = False

	for val in plugin_desc:
		try:
			led = eq_leds[val[5]]['led']
			if val[12] > 0:
				bank[current]['led_stat_eq'][led] = True
			else:
				bank[current]['led_stat_eq'][led] = False
		except:
			pass

	set_led_status()
	plugin_desc = ()
	plugin_list = ()

def search_eq_strip(strip_id = None):
	global bank
	global plugin_list
	global plugin_desc
	global operation

	osc.send('/strip/plugin/list', strip_id)
	time.sleep(tick_time)

	if len(plugin_list) < 4:
		if debug:
			print("There are no plugins at that strip, fallback to mixer mode")
		set_mixer_mode()
		return

	plugin_names = plugin_list[4::3]

	if 'x42-eq - Parametric Equalizer Mono' not in plugin_names and \
	'x42-eq - Parametric Equalizer Stereo' not in plugin_names:
			if debug:
				print("Could't find x24 EQ at that strip, fallback to mixer mode")
			set_mixer_mode()
			return

	m_pos = []
	if 'x42-eq - Parametric Equalizer Mono' not in  plugin_names:
		for i in range(0,len(plugin_names)):
			if plugin_names[i] == 'x42-eq - Parametric Equalizer Stereo':
				m_pos.append(i + 1)
	else:
		for i in range(0,len(plugin_names)):
			if plugin_names[i] == 'x42-eq - Parametric Equalizer Mono':
				m_pos.append(i + 1)

	if len(m_pos) > 1:
		if debug:
			print("There are more than one EQ at that strip")

		if len(m_pos) > 8:
			if debug:
				print("Too many EQs at that strip, fallback to mixer mode")
			set_mixer_mode()
			return

		operation['mode']       = 'read_keypress'
		operation['strip']      = strip_id
		apaga_leds()

		for i in recs[0:len(m_pos)]:
			enciende_led(i)
		return m_pos

	else:
		pos = m_pos[0]

	osc.send('/strip/plugin/descriptor', strip_id, pos)
	time.sleep(tick_time * 10)

	current = bank['current']

	for led in bank[current]['led_stat_eq'].keys():
		bank[current]['led_stat_eq'][led] = False

	for val in plugin_desc:
		try:
			led = eq_leds[val[5]]['led']
			if val[12] > 0:
				bank[current]['led_stat_eq'][led] = True
			else:
				bank[current]['led_stat_eq'][led] = False
		except:
			pass

	if debug:
		print("EQ plugin found at {}".format(pos))

	return pos

def event_recenable(origen, evento, strip_id, valor):
	global bank
	vel = 0
	if valor == 1.0:
		vel = 127
	strip_bank = ( strip_id // 8 )
	if strip_id % 8 == 0:
		strip_bank -= 1
	if strip_bank < 3 :
		bank_led = (strip_id - 1) - (8 * strip_bank)
		led  = recs[bank_led]
		if vel == 127:
			bank[strip_bank]['led_stat_mix'][led] = True
		else:
			bank[strip_bank]['led_stat_mix'][led] = False
		if operation['mode'] == 'mixer':
			note = mido.Message('note_on', channel=0, note=led, velocity=vel)
			mmix_out.send(note)

def event_mute(origen, evento, strip_id, valor):
	global bank
	vel = 0
	if valor == 1.0:
		vel = 127
	strip_bank = ( strip_id // 8 )
	if strip_id % 8 == 0:
		strip_bank -= 1
	if strip_bank < 3 :
		bank_led = (strip_id - 1) - (8 * strip_bank)
		led  = mutes[bank_led]
		if vel == 127:
			bank[strip_bank]['led_stat_mix'][led] = True
			bank[strip_bank]['led_stat_eq'][21]   = True
		else:
			bank[strip_bank]['led_stat_mix'][led] = False
			bank[strip_bank]['led_stat_eq'][21] = False
		if operation['mode'] == 'mixer':
			if strip_bank == bank['current']:
				note = mido.Message('note_on', channel=0, note=led, velocity=vel)
				mmix_out.send(note)

def trigger_mute(led_id):
	global bank
	current = bank['current']
	if operation['mode'] == 'mixer':
		strip_id   = ( mutes.index(led_id) + 1 ) + ( 8 * current )
	else:
		strip_id = operation['strip']
		led_id = mutes[(operation['strip'] % 8) - 1]
		
	if bank[current]['led_stat_mix'][led_id] == True:
		osc.send('/strip/mute', strip_id, 0)
		bank[current]['led_stat_mix'][led_id] = False
		bank[current]['led_stat_eq'][21] = False
		
	else:
		osc.send('/strip/mute', strip_id, 1)
		bank[current]['led_stat_mix'][led_id] = True
		bank[current]['led_stat_eq'][21] = True

def trigger_rec(led_id, strip_id = None):
	global bank
	current = bank['current']
	if strip_id == None:
		strip_id =  recs.index(led_id) + 1 + ( 8 * current )
	if bank[current]['led_stat_mix'][led_id] == True:
		osc.send('/strip/recenable', strip_id, 0)
		bank[current]['led_stat_mix'][led_id] = False
	else:
		osc.send('/strip/recenable', strip_id, 1)
		bank[current]['led_stat_mix'][led_id] = True

def set_led_status():
	global bank
	current = bank['current']
	if operation['mode'] == 'mixer':
		if debug:
			print("Setting leds at mixer mode")

		for led in bank[current]['led_stat_mix']:
			if bank[current]['led_stat_mix'][led]:
				enciende_led(led)
			else:
				apaga_led(led)

		if bank['current'] == 1:
			enciende_led(b_left)
			apaga_led(b_right)
		elif bank['current'] == 2:
			apaga_led(b_left)
			enciende_led(b_right)
		else:
			apaga_led(b_left)
			apaga_led(b_right)

	if operation['mode'] == 'EQ':
		if debug:
			print("Setting leds at EQ mode")

		for led in bank[current]['led_stat_eq']:
			if bank[current]['led_stat_eq'][led]:
				enciende_led(led)
			else:
				apaga_led(led)

		strip_muted = bank[current]['led_stat_mix'][ mutes[(operation['strip'] % 8) - 1] ]
		if strip_muted:
			enciende_led(24)

def operar_led( led_id = None):
		global bank
		current = bank['current']
		if operation['mode'] == 'EQ':
			led_status = bank[current]['led_stat_eq']
		if operation['mode'] == 'mixer':
			led_status = bank[current]['led_stat_mix']

		led = led_status.get(led_id)

		if led is not None:
			if not led :
				led_status[led_id] = True
				enciende_led(led_id)
				time.sleep(tick_time)
			else:
				led_status[led_id] = False
				apaga_led(led_id)
				time.sleep(tick_time)
		else:
			led_status[led_id] = True
			enciende_led(led)

def surface_callback(msg):
	global bank
	global note_press
	global operation
	global get_note
	try:
		if msg.type == 'note_on':
			if debug_controls:
				print("note_on : %s" % msg.note)
			if note_press['state'] :
				if debug_controls:
					print("note_on : %s (multinote) " % msg.note)
				if note_press['note']  == b_solo:
					if ( msg.note - 1 ) in  mutes:
						strip_id =  ( mutes.index(msg.note - 1) + 1 ) + (8 * bank['current'])
						if operation['mode'] == 'mixer':
							if debug:
								print('EQ mode at strip {}'.format(strip_id))
							operation['mode']       = 'EQ'
							operation['strip']      = strip_id
							operation['plugin_pos'] = search_eq_strip(strip_id)

							if operation['plugin_pos'] is not None:
								enciende_led(b_left)
								enciende_led(b_right)
								set_led_status()
							return
						else:
							if operation['strip'] != strip_id:
								if debug:
									print('EQ mode at stip {}'.format(strip_id))
								operation['mode']  = 'EQ'
								operation['strip'] = strip_id
								operation['plugin_pos'] = search_eq_strip(strip_id)

								if operation['plugin_pos'] is not None:
									enciende_led(b_left)
									enciende_led(b_right)
									set_led_status()
								return
							else:
								set_mixer_mode()
								return
						return
					if msg.note in  recs:
						strip_id =  ( recs.index(msg.note) + 1 ) + (8 * bank['current'])
						if debug:
							print ("ignoring solo + rec at strip {}".format(strip_id))
						return

			if not note_press['state'] :
				if operation['mode'] == 'read_keypress':
					espera_indice_modulo_eq(msg.note)
					return

				bank_op = False
				if msg.note == b_left:
					if bank['current'] > 0:
						bank['current'] -= 1
					if debug:
						print('Bank down, set : {}'.format(bank['current']))
					bank_op = True
					set_led_status()
					return

				if msg.note == b_right:
					if bank['current'] < 2:
						bank['current'] += 1
					if debug:
						print('Bank up, set: {}'.format(bank['current']))
					bank_op = True
					set_led_status()
					return

				note_press['note']  = msg.note
				note_press['state'] = True
				if operation['mode'] == 'mixer' and not bank_op:
					if msg.note in mutes:
						trigger_mute(msg.note)
					elif msg.note in recs:
						trigger_rec(msg.note)
					else:
							return
					operar_led(msg.note)
				if operation['mode'] == 'EQ' and not bank_op:
					if msg.note == 24:
						if debug:
							print("Muting strip in the MIX")
						current = bank['current']
						trigger_mute(msg.note)
						strip_muted = bank[current]['led_stat_mix'][ mutes[(operation['strip'] % 8) - 1] ]
						if strip_muted:
							enciende_led(24)
						else:
							apaga_led(24)
					else:
						if msg.note != 27:
							option = eq_led_trigger[msg.note]['option']
							current = bank['current']
							if bank[current]['led_stat_eq'][msg.note] == True:
								valor = 0
							else:
								valor = 1
							operar_led(msg.note)
							osc.send('/strip/plugin/parameter', operation['strip'], operation['plugin_pos'], option, valor)
	except Exception as e:
			print("Exception Error : {}".format(e))

	if msg.type == 'note_off':
		if debug_controls:
			print("note_off : %s" % msg.note)
		if note_press['note'] == msg.note:
			note_press['note']  = None
			note_press['state'] = False

	if msg.type == 'control_change':
		if debug_controls:
			print("CC from : {}, value : {}".format(msg.control, msg.value))
		if operation['mode'] == 'mixer':
			if msg.control in faders:
				if msg.control == 62:
					osc.send("/master/gain", -193 + (1.622 * msg.value))
				else:
					strip_id = (int(faders.index(msg.control) + 1)) + ( 8 * bank['current'] )
					osc.send("/strip/fader", strip_id, 0.0 + (0.79 * ( int(msg.value) / 100)))
			if msg.control in knobs:
				knob = "{:.2f}".format(knobs.index(msg.control) / 3 % 1)
				if knob == '0.00':
					action = '/strip/trimdB'
					valor = float( -20.00000 + ( 0.31496 * msg.value) )
				if knob == '0.33':
					action = '/strip/pan_stereo_position'
					valor = float( 1.00000 - (0.00787 * msg.value) )
				if knob == '0.67':
					action = '/strip/solo'
					if msg.value > 90:
						valor = 1.0
					else:
						valor = 0.0
				strip_id = int(knobs.index(msg.control) / 3 + 1) + ( 8 * bank['current'] )
				osc.send(action, strip_id, valor)

		if operation['mode'] == 'EQ':
			if msg.control == 62:
				osc.send("/strip/fader", operation['strip'], 0.0 + (0.79 * ( int(msg.value) / 100)))
			elif msg.control == 18:
				valor = float( 1.00000 - (0.00787 * msg.value) )
				osc.send('/strip/pan_stereo_position', operation['strip'], valor)
			elif  msg.control == 60:
				if msg.value > 90:
					valor = 1.0
				else:
					valor = 0.0
				osc.send('/strip/solo', operation['strip'], valor)
			else:
				option = eq_fad_knob[msg.control]['plugin_opt']
				valor  = float( eq_fad_knob[msg.control]['min'] + ( eq_fad_knob[msg.control]['incremento'] * msg.value ) )
				osc.send('/strip/plugin/parameter', operation['strip'], operation['plugin_pos'], option, valor)

def load_project(origen, evento, valor):
	if valor == ' ':
		if debug:
			print("Loading new project")
		osc.error_received("LoadNewProject")
		apaga_leds()
		time.sleep(tick_time)

class ArdourOSCServer(aiosc.OSCProtocol):
	def __init__(self):
		handlers = {
					'/strip/plugin/list'       : get_plugin_list,
					'/strip/plugin/descriptor' : get_plugin_desc,
					'/strip/recenable'         : event_recenable,
					'/strip/mute'              : event_mute,
					'/master/name'             : load_project
				}

		if debug_osc_msg:
			handlers.update({'//*'                      : self.echo})

		super().__init__(handlers)

	def echo(self, addr, path, *args):
			print("incoming message from {}: {} {}".format(addr, path, args))

	def connection_made(self, transport):
		self.transport = transport

	def connection_lost(self, exception):
		self.id = None
		if exception is not None:
			if debug:
				print("exception :: {}".format(exception))
		loop.stop()

	def error_received(self, exception):
		self.id = None
		if debug:
			print("error :: {}".format(exception))
		transport.abort()

async def main():
	global osc
	global transport
	global loop
	loop = asyncio.get_running_loop()
	transport, osc = await loop.create_datagram_endpoint(ArdourOSCServer,
		remote_addr=('127.0.0.1', 3819))

	if osc is not None:
		osc.send("/set_surface/24/159/19/0/0/0/0/0")

	if osc is not None:
		try:
			await loop.create_future()
		except:
			pass

def run_main_async():
	apaga_led(b_left)
	apaga_led(b_right)
	try:
		asyncio.run(main())
	except:
		pass

def start_loop():
	while respawn:
			server_thread = None
			server_thread = Thread(target = run_main_async)
			server_thread.start()
			if debug:
				print("Starting new thread")
			server_thread.join()
			if debug:
				print("Thread ended")
			time.sleep(2)
	apaga_leds()
	time.sleep(0.5)
	sys.exit(0)

def interact():
	import code
	import rlcompleter
	import readline
	readline.parse_and_bind("tab: complete")
	code.InteractiveConsole(locals=globals()).interact(banner="")

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='turn on script messages')
parser.add_argument('--debug_controls', action='store_true', help='turn on debug for control buttons / sliders and knobs')
parser.add_argument('--debug_osc_msg', action='store_true', help='turn on debug for control buttons / sliders and knobs')
parser.add_argument('--debug_all', action='store_true', help='turn on all previous debug flags')
parser.add_argument('--dev_mode', action='store_true', help='spawn a python shell to inspect call functions and experiment')
parser.add_argument('--list_ports', action='store_true', help='list midi ports and exit')
parser.add_argument('--midimix_in', default='system:midi_capture_1', help='Sets the INPUT MIDI port where the MIDIMIX surface is attached')
parser.add_argument('--midimix_out', default='system:midi_playback_1', help='Sets the OUTPUT MIDI port where the MIDIMIX surface is attached')

args = parser.parse_args()

dev_mode       = args.dev_mode
debug_controls = args.debug_controls
debug          = args.debug
debug_osc_msg  = args.debug_osc_msg
debug_all      = args.debug_all

if debug_all:
	debug_controls = True
	debug          = True
	debug_osc_msg  = True

midimix_in  = args.midimix_in
midimix_out = args.midimix_out

mido.set_backend('mido.backends.rtmidi/UNIX_JACK')
mmix_in    = mido.open_input(midimix_in, callback=surface_callback)
mmix_out   = mido.open_output(midimix_out)

if args.list_ports:
	print("===========================")
	print("Input MIDI ports")
	print("===========================")
	for port in mido.get_input_names():
		print(port)
	print("===========================")
	print("")
	print("===========================")
	print("Output MIDI ports")
	print("===========================")
	for port in mido.get_output_names():
		print(port)
	print("===========================")

	sys.exit(0)

if not dev_mode:
	start_loop()
else:
	print("")
	print("====================================================")
	print(">>>> To start the main loop run start_loop()")
	print("====================================================")
	print("")
	interact()
