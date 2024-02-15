# midimix_ardour_x24eq_osc
Pythonic OSC interface to drive Ardour DAW &amp; x24 parametric EQ from AKAI MIDIMIX

Implements a OSC interface betwen Ardour DAW / x42 EQ and AKAI MIDIMIX surface

x42 Parametric EQ module
https://github.com/x42/fil4.lv2

Usually shipped with x42-plugins in your preferred linux distro

Ardour Digital Audio Workstation
https://github.com/Ardour/ardour

AKAI MIDIMIX
https://www.akaipro.com/midimix

* MIX/EQ modes toggling with SOLO + strip on MIDIMIX
* Controls up to 8 EQs per strip
* Support 3 banks for 8 strip pagination
* Uses JACK as rtmidi backend

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

* 'Output Gain'     : fader at MIDIMIX strip 1
* 'Enable'          : REC  on MIDIMIX strip 1
* 'Reset Peak Hold' : REC  on MIDIMIX strip 2

* 'Highpass'        : MUTE on MIDIMIX strip 1
* 'High pass freq'  : 1st knob at MIDIMIX strip 1
* 'High pass Q'     : 2nd knob at MIDIMIX strip 1

* 'Lowpass'         : MUTE on MIDIMIX strip 2
* 'Lowpass freq'    : 1st knob at MIDIMIX strip 2
* 'Lowpass Q'       : 2nd knob on MIDIMIX strip 2

* 'Lowshelf'        : MUTE on MIDIMIX strip 3
* 'Lowshelf freq'   : 1st knob on MIDIMIX strip 3
* 'Lowshelf Q'      : 2nd knob on MIDIMIX strip 3
* 'Lowshelf Gain'   : fader at MIDIMIX strip 3

* 'Section 1'       : MUTE on MIDIMIX strip 4
* 'Section 1 freq'  : 1st knob on MIDIMIX strip 4
* 'Section 1 Q'     : 2nd knob on MIDIMIX strip 4
* 'Section 1 Gain'  : fader on MIDIMIX strip 4

* 'Section 2'       : MUTE on MIDIMIX strip 5
* 'Section 2 freq'  : 1st knob on MIDIMIX strip 5
* 'Section 2 Q'     : 2nd knob on MIDIMIX strip 5
* 'Section 2 Gain'  : fader on MIDIMIX strip 5

* 'Section 3'       : MUTE on MIDIMIX strip 6
* 'Section 3 freq'  : 1st knob on MIDIMIX strip 6
* 'Section 3 Q'     : 2nd knob on MIDIMIX strip 6
* 'Section 3 Gain'  : fader on MIDIMIX strip 6

* 'Section 4'       : MUTE on MIDIMIX strip 7
* 'Section 4 freq'  : 1st knob on MIDIMIX strip 7
* 'Section 4 Q'     : 2nd knob on MIDIMIX strip 7
* 'Section 4 Gain'  : fader on MIDIMIX strip 7

* 'Highshelf'       : MUTE on MIDIMIX strip 8
* 'Highshelf freq'  : 1st knob on MIDIMIX strip 8
* 'Highshelf Q'     : 2nd knob on MIDIMIX strip 8
* 'Highshelf Gain'  : fader on MIDIMIX strip 8

At EQ mode you can still adjust some MIX controls :

* MIX strip volume with MIDIMIX Master fader
* MIX triger SOLO with 3rd knob at strip 8 (+50 enables SOLO)
* MIX panning with 3rd knob at strip 1
* MIX mute with MIDIMIX MUTE at strip 8
