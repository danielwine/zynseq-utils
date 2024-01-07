# -*- coding: utf-8 -*-
#******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Controller (zynthian_controller)
# 
# zynthian controller
# 
# Copyright (C) 2015-2023 Fernando Moyano <jofemodo@zynthian.org>
#
#******************************************************************************
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
# 
#******************************************************************************

import math
import liblo
import logging

# Zynthian specific modules
# from zyncoder.zyncore import lib_zyncore
# from zyngui import zynthian_gui_config

class zynthian_controller:

	def __init__(self, engine, symbol, name=None, options=None):
		self.engine = engine
		self.symbol = symbol
		if name:
			self.name = self.short_name = name
		else:
			self.name = self.short_name = symbol

		self.processor = None
		self.reset()

		if options:
			self.set_options(options)


	def reset(self):
		self.group_symbol = None
		self.group_name = None

		self.value = 0 # Absolute value of the control
		self.value_default = None # Default value to use when reset control
		self.value_min = None # Minimum value of control range
		self.value_mid = None # Mid-point value of control range (used for toggle controls)
		self.value_max = None # Maximum value of control range
		self.value_range = None # Span of permissible values 
		self.nudge_factor = None # Factor to scale each up/down nudge #TODO: This is not set if configure is not called or options not passed
		self.labels = None # List of discrete value labels
		self.ticks = None # List of discrete value labels
		self.range_reversed = False # Flag if ticks order is reversed
		self.is_toggle = False # True if control is Boolean toggle
		self.is_integer = True # True if control is Integer
		self.is_logarithmic = False # True if control uses logarithmic scale
		self.is_dirty = True # True if control value changed since last UI update
		self.not_on_gui = False # True to hint to GUI to show control
		self.display_priority = 0 # Hint of order in which to display control (higher comes first)

		# Parameters to send values if engine-specific send method not available
		self.midi_chan = None # MIDI channel to send CC messages from control
		self.midi_cc = None # MIDI CC number to send CC messages from control
		self.midi_feedback = None # [chan,cc] for MIDI control feedback
		self.osc_port = None # OSC destination port
		self.osc_path = None # OSC path to send value to
		self.graph_path = None # Complex map of control to engine parameter

		self.label2value = None # Dictionary for fast conversion from discrete label to value
		self.value2label = None # Dictionary for fast conversion from discrete value to label


	def set_options(self, options):
		if 'processor' in options:
			self.processor = options['processor']
		if 'symbol' in options:
			self.symbol = options['symbol']
		if 'name' in options:
			self.name = options['name']
		if 'short_name' in options:
			self.short_name = options['short_name']
		if 'group_name' in options:
			self.group_name = options['group_name']
		if 'group_symbol' in options:
			self.group_symbol = options['group_symbol']
		if 'value' in options:
			self.value = options['value']
		if 'value_default' in options:
			self.value_default = options['value_default']
		if 'value_min' in options:
			self.value_min = options['value_min']
		if 'value_max' in options:
			self.value_max = options['value_max']
		if 'labels' in options:
			self.labels = options['labels']
		if 'ticks' in options:
			self.ticks = options['ticks']
		if 'is_toggle' in options:
			self.is_toggle = options['is_toggle']
		if 'is_integer' in options:
			self.is_integer = options['is_integer']
		if 'nudge_factor' in options:
			self.nudge_factor = options['nudge_factor']
		if 'is_logarithmic' in options:
			self.is_logarithmic = options['is_logarithmic']
		if 'midi_chan' in options:
			self.midi_chan = options['midi_chan']
		if 'midi_cc' in options:
			self.midi_cc = options['midi_cc']
		if 'osc_port' in options:
			self.osc_port = options['osc_port']
		if 'osc_path' in options:
			self.osc_path = options['osc_path']
		if 'graph_path' in options:
			self.graph_path = options['graph_path']
		if 'not_on_gui' in options:
			self.not_on_gui = options['not_on_gui']
		if 'display_priority' in options:
			self.display_priority = options['display_priority']
		self._configure()


	def _configure(self):
		#Configure Selector Controller
		self.range = None
		if self.labels:
			#Generate ticks if needed ...
			if not self.ticks:
				n = len(self.labels)
				self.ticks = []
				if self.value_min == None:
					self.value_min = 0
				if self.value_max == None:
					self.value_max = n - 1
				value_range = self.value_max - self.value_min
				if n == 1:
					self.ticks.append(self.value_min)
				elif self.is_integer:
					for i in range(n):
						self.ticks.append(self.value_min + int(i * value_range / (n - 1)))
				else:
					for i in range(n):
						self.ticks.append(self.value_min + i * value_range / (n - 1))

			#Calculate min, max
			if self.ticks[0] <= self.ticks[-1]:
				if self.value_min == None:
					self.value_min = self.ticks[0]
				if self.value_max == None:
					self.value_max = self.ticks[-1]
				self.range_reversed = False
			else:
				self.value_min = self.ticks[-1]
				self.value_max = self.ticks[0]
				self.range_reversed = True

			#Generate dictionary for fast conversion labels=>values
			self.label2value = {}
			self.value2label = {}
			for i in range(len(self.labels)):
				self.label2value[str(self.labels[i])] = self.ticks[i]
				self.value2label[str(self.ticks[i])] = self.labels[i]

		#Common configuration
		if self.value_min == None:
			self.value_min = 0
		if self.value_max == None:
			self.value_max = 127
		self.value_range = self.value_max - self.value_min

		if self.value_mid == None:
			if self.is_integer:
				self.value_mid = self.value_min + int(self.value_range / 2)
			else:
				self.value_mid = self.value_min + self.value_range / 2

		self._set_value(self.value)
		if self.value_default is None:
			self.value_default = self.value

		if not self.nudge_factor:
			if self.is_logarithmic:
				self.nudge_factor = 1 / 200 #TODO: Use number of divisions
			elif not self.is_integer and not self.is_toggle:
				self.nudge_factor = self.value_range / 200 # This overrides specified nudge_factor but mostly okay
			else:
				self.nudge_factor = 1

		if self.midi_feedback is None and self.midi_chan is not None and self.midi_cc is not None:
			self.midi_feedback = [self.midi_chan, self.midi_cc]

	def setup_controller(self, chan, cc, val, maxval=127):
		self.midi_chan = chan

		# OSC Path / MIDI CC
		if isinstance(cc, str):
			self.osc_path = cc
		else:
			self.midi_cc = cc

		self.value = val
		self.is_toggle = False
		self.is_integer = True
		self.is_logarithmic = False

		# Numeric
		if isinstance(maxval, int):
			self.value_max = maxval
		elif isinstance(maxval, float):
			self.value_max = maxval
			self.is_integer = False
		# Selector
		elif isinstance(maxval, str):
			self.labels = maxval.split('|')
		elif isinstance(maxval, list):
			if isinstance(maxval[0], list):
				self.labels = maxval[0]
				self.ticks = maxval[1]
			else:
				self.labels = maxval

		# Detect toggle (on/off)
		if self.labels and len(self.labels) == 2:
			self.is_toggle = True
			if not self.ticks:
				self.value_max = 127

		self._configure()


	def get_path(self):
		if self.osc_path:
			return str(self.osc_path)
		elif self.graph_path:
			return str(self.graph_path)
		elif self.midi_chan is not None and self.midi_cc is not None:
			return "{}#{}".format(self.midi_chan,self.midi_cc)
		else:
			return None


	def set_midi_chan(self, chan):
		self.midi_chan = chan


	#TODO: I think get_ctrl_array is an unused function
	def get_ctrl_array(self):
		title = self.short_name
		if self.midi_chan:
			chan = self.midi_chan
		else:
			chan = 0
		if self.midi_cc:
			ctrl = self.midi_cc
		elif self.osc_path:
			ctrl = self.osc_path
		elif self.graph_path:
			ctrl = self.graph_path
		else:
			ctrl = None
		
		if self.labels:
			val = self.get_value2label()
			if self.ticks:
				minval = [self.labels, self.ticks]
				maxval = None
			else:
				minval = self.labels
				maxval = None
		else:
			val = self.value
			minval = self.value_min
			maxval = self.value_max
		return [title, chan, ctrl, val, minval, maxval]


	def get_value(self):
		return self.value


	def nudge(self, val, send=True):
		if self.nudge_factor is None:
			return False
		if self.ticks:
			index = self.get_value2index() + val
			if index < 0: index = 0
			if index >= len(self.ticks) : index = len(self.ticks) - 1
			self.set_value(self.ticks[index], send)
		elif self.is_logarithmic and self.value_range:
			log_val = math.log10((9 * self.value - (10 * self.value_min - self.value_max)) / self.value_range)
			log_val = min(1, max(0, log_val + val * self.nudge_factor))
			self.set_value((math.pow(10, log_val) * self.value_range + (10 * self.value_min - self.value_max)) / 9)
		else:
			self.set_value(self.value + val * self.nudge_factor, send)
		return True


	def _set_value(self, val):
		if isinstance(val, str):
			self.value = self.get_label2value(val)
			return

		elif self.is_toggle:
			if val == self.value_min or val == self.value_max:
				if self.is_integer:
					self.value = int(val)
				else:
					self.value = val
			else:
				if val < self.value_mid:
					self.value = self.value_min
				else:
					self.value = self.value_max
			return

		elif self.ticks:
			#TODO Do something here?
			pass

		elif self.is_integer:
			val = int(val)

		if val > self.value_max:
			self.value = self.value_max
		elif val < self.value_min:
			self.value = self.value_min
		else:
			self.value = val


	def set_value(self, val, send=True):
		old_val = self.value
		self._set_value(val)
		if old_val == self.value:
			return

		if self.engine:
			if self.midi_cc:
				mval = self.get_ctrl_midi_val()

			if send:
				try:
				# Send value using engine method...
					self.engine.send_controller_value(self)
				except:
					try:
						# Send value using OSC/MIDI ...
						if self.osc_path:
							#logging.debug("Sending OSC Controller '{}', {} => {}".format(self.symbol, self.osc_path, self.get_ctrl_osc_val()))
							liblo.send(self.engine.osc_target,self.osc_path, self.get_ctrl_osc_val())

						elif self.midi_cc:
							#logging.debug("Sending MIDI Controller '{}', CH{}#CC{}={}".format(self.symbol, self.midi_chan, self.midi_cc, mval))
							lib_zyncore.ui_send_ccontrol_change(self.midi_chan, self.midi_cc, mval)

					except Exception as e:
						logging.warning("Can't send controller '{}' => {}".format(self.symbol, e))


		if self.midi_feedback:
			# Send feedback to MIDI controllers
			#TODO: Set midi_feeback to MIDI learn
			try:
				lib_zyncore.ctrlfb_send_ccontrol_change(self.midi_feedback[0], self.midi_feedback[1], mval)

			except Exception as e:
				logging.warning("Can't send controller feedback '{}' => Val={}".format(self.symbol, e))
			
		self.is_dirty = True


	# Get index of list entry closest to given value
	def get_value2index(self, val=None):
		if val is None:
			val = self.value
		try:
			if self.ticks:
				index = 0
				dval = abs(self.ticks[0] - val)
				for i in range(1, len(self.ticks)):
					ndval = abs(self.ticks[i] - val)
					if ndval < dval:
						dval = ndval
						index = i
					else:
						break
				return index
			else:
				return None
		except Exception as e:
			logging.error(e)


	def get_value2label(self, val=None):
		if val == None:
			val = self.value
		i = self.get_value2index(val)
		if i is not None:
			return self.labels[i]
		else:
			return val


	def get_label2value(self, label):
		try:
			if self.ticks:
				return self.label2value[str(label)]
			else:
				logging.error("No labels/ticks defined")

		except Exception as e:
			logging.error(e)


	def get_ctrl_midi_val(self):
		try:
			if self.value_range == 0:
				return 0
			elif self.is_logarithmic:
				val = int(127 * math.log10((9 * self.value - (10 * self.value_min - self.value_max)) / self.value_range))
			else:
				val = min(127, int(127 * (self.value - self.value_min) / self.value_range))
		except Exception as e:
			logging.error(e)
			val = 0

		return val


	def get_ctrl_osc_val(self):
		if self.is_toggle:
			return self.value > 0
		return self.value


	def reset_value(self):
		"""Reset value to default"""
		self.set_value(self.value_default)

	#--------------------------------------------------------------------------
	# State management functions
	#--------------------------------------------------------------------------

	def get_state(self, full=True):
		"""Get controller state as dictionary

		full : True to get state of all parameters or false for off-default values
		"""

		#TODO: Move this to processor (used by processor and audio mixer)
		state = {}
		
		# Value
		if full:
			if math.isnan(self.value):
				state['value'] = None
			else:
				state['value'] = self.value
		elif self.value != self.value_default:
			state['value'] = self.value

		return state


	#----------------------------------------------------------------------------
	# MIDI CC processing
	#----------------------------------------------------------------------------

	def midi_control_change(self, val):
		#if self.ticks:
		#	self.set_value(val)
		if self.is_logarithmic:
			value = self.value_min + self.value_range * (math.pow(10, val/127) - 1) / 9
		else:
			value = self.value_min + val * self.value_range / 127
		self.set_value(value)



#******************************************************************************
