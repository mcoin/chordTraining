#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Random chord generator to train with jazz voicings
TV 2013-07-28
'''

import wx
import random
import collections
import re
from subprocess import call, Popen
import os
from os.path import expanduser


class StayOn:
	def __init__(self):
		# Use the PyMouse framework to move the mouse periodically
		try:
			from pymouse import PyMouse
			self.pyMouseEnabled = True
		except:
			# Give up in case the PyMouse framework cannot be found
			self.pyMouseEnabled = False
			return

		# Total time elapsed since the mouse was last moved to avoid letting the screensavec start
		self.mouseElapsedTime = 0
	
		# Time period after which the mouse should be moved in order to prevent the screensaver from starting (s)
		self.mouseRefreshPeriod = 30
		
		# Mouse object to prevent the screensaver from starting
		self.mouse = PyMouse()
		
		# Mouse displacement
		self.mouseDx = (0,1)
		
		# Movement amplitude
		self.amplitude = 1
		
	def isEnabled(self):
		return self.pyMouseEnabled
	
	def moveMouse(self, elapsedTime):
		# elapsedTime: Time elapsed since last call (in s)
		if self.pyMouseEnabled:
			self.mouseElapsedTime += elapsedTime
			if self.mouseElapsedTime >= self.mouseRefreshPeriod:
				self.mouseElapsedTime = 0
				position = self.mouse.position()
				self.mouse.move(position[0] + self.mouseDx[0]*self.amplitude, position[1] + self.mouseDx[1]*self.amplitude)
				if self.mouseDx == (0,1):
					self.mouseDx = (1,0)
				elif self.mouseDx == (1,0):
					self.mouseDx = (0,-1)
				elif self.mouseDx == (0,-1):
					self.mouseDx = (-1,0)
				elif self.mouseDx == (-1,0):
					self.mouseDx = (0,1)
		
# Exception thrown when no image may be determined for the score of a chord/progression
class NoImage(Exception):
	def __init__(self):
	    pass

class Chord:
	def __init__(self, pitch = '-', quality = '-', mode = '-'):
		self.pitch = pitch
		self.quality = quality
		self.mode = mode
		
		self.pitches = ['C', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'F#', 'B', 'E', 'A', 'D', 'G']
	
		self.name = None
		self.fileName = None
		self.scalePitch = None
		self.scaleKind = None
		self.scaleFileName = None
		self.updateScale = True
		
	def SetPitch(self, pitch):
		self.pitch = pitch
		self.updateScale = True

	def SetQuality(self, quality):
		self.quality = quality
		self.updateScale = True
	
	def SetMode(self, mode):
		self.mode = mode
		self.updateScale = True
	
	def GetPitch(self):
		return self.pitch
	
	def ConvertToLy(self, pitch):
		lyPitch = pitch
		lyPitch = re.sub(r"(.)b", r"\1f", lyPitch)
		lyPitch = re.sub(r"(.)#", r"\1s", lyPitch)
		return lyPitch
	
	def GetLyPitch(self):
		return self.ConvertToLy(self.pitch)

	def GetScalePitch(self):
		self.DetermineScale()
		return self.scalePitch
	
	def GetLyScalePitch(self):
		self.DetermineScale()
		return self.ConvertToLy(self.scalePitch)

	def GetScaleKind(self):
		self.DetermineScale()
		return self.scaleKind

	def GetQuality(self):
		return self.quality
	
	def GetMode(self):
		return self.mode
	
	def GenerateRandom(self, listPitches, listQualities, currentMode):
		self.SetMode(currentMode)
		
		if len(listPitches) == 0 or len(listQualities) == 0:
			self.SetPitch("-")
			self.SetQuality("-")
			return

		pitch = random.choice(listPitches)
		self.SetPitch(pitch)
		
		quality = random.choice(listQualities)
		self.SetQuality(quality)

		self.updateScale = True

	def GetName(self):
		if self.mode == 'Chord':
			self.name = self.pitch + " " + self.quality
		elif self.mode == 'II-V-I' or self.mode == 'V-I':
			try:
				indexPitch = self.pitches.index(self.pitch)
			except:
				return '- -'
			progression = ''
			
			if self.mode == 'II-V-I':
				indexIIpitch = indexPitch - 2
				IIpitch = self.pitches[indexIIpitch]
				progression += IIpitch + ' min7' + '\n'
			
			indexVpitch = indexPitch - 1
			Vpitch = self.pitches[indexVpitch]	
			progression += Vpitch + ' 7' + '\n'
			
			progression += self.pitch + ' Maj7'
			self.name = progression
		else:
			self.name = "<Unknown mode>"
			
		return self.name

	def DetermineScale(self):
		if not self.updateScale:
			return
		self.updateScale = False
		
		if self.mode == 'Chord':
			if self.quality == 'Maj7' or self.quality == '7' or self.quality == 'min7':
				if self.quality == 'Maj7':
					self.scalePitch = self.pitch
					self.scaleKind = "Major"
				elif self.quality == '7':
					indexVpitch = self.pitches.index(self.pitch)
					indexPitch = indexVpitch + 1
					if indexPitch >= len(self.pitches): 
						indexPitch -= len(self.pitches)
					self.scalePitch = self.pitches[indexPitch]
					self.scaleKind = "Major"
				elif self.quality == 'min7':
					indexIIpitch = self.pitches.index(self.pitch)
					indexPitch = indexIIpitch + 2
					if indexPitch >= len(self.pitches): 
						indexPitch -= len(self.pitches)
					self.scalePitch = self.pitches[indexPitch]
					self.scaleKind = "Major"
			elif (self.quality == 'dim7'):
				index = self.pitches.index(self.pitch) % 3
				self.scalePitch = self.pitches[index]
				self.scaleKind = "Diminished"

			self.scale = self.scalePitch + " " + self.scaleKind
		elif self.mode == 'II-V-I' or self.mode == 'V-I':
			self.scalePitch = self.pitch
			self.scaleKind = "Major"
			self.scale = self.scalePitch + " " + self.scaleKind
		else:
			self.scale = "<Unknown mode>"

	def GetScale(self):
		self.DetermineScale()			
		return self.scalePitch + " " + self.scaleKind

	def GetBaseFileName(self):
		if self.mode == 'Chord':
			self.fileName = "chord_" + self.GetLyPitch() + "_" + self.GetQuality() + "_res%s%s"
		elif self.mode == 'II-V-I':
			self.fileName = "prog_II-V-I_" + self.GetLyPitch() + "_res%s%s"
		elif self.mode == 'V-I':
			self.fileName = "prog_V-I_" + self.GetLyPitch() + "_res%s%s"
		else:
			raise
		
		return self.fileName

	def GetImgName(self, res):
		return self.GetBaseFileName() % (str(res), '.preview.png')
	
	def GetLyName(self, res):
		return self.GetBaseFileName() % (str(res), '.ly')

	def GetBaseScaleFileName(self):
		self.DetermineScale()
		self.scaleFileName = "scale_" + self.GetLyScalePitch() + "_" + self.GetScaleKind() + "_res%s%s"
		
		return self.scaleFileName

	def GetScaleImgName(self, res):
		return self.GetBaseScaleFileName() % (str(res), '.preview.png')
	
	def GetLyScaleName(self, res):
		self.DetermineScale()
		return self.GetBaseScaleFileName() % (str(res), '.ly')


class ChordStack():
	def __init__(self):
		# Number of previous and next items in the stack
		self.nbFurtherItems = 10
		# Total number of elements
		self.nbElements = self.nbFurtherItems + 1 + self.nbFurtherItems
		# Index of the current item
		self.curr = 0 + self.nbFurtherItems
		# Index of the previous item
		self.prev = self.curr - 1
		# Index of the next item
		self.next = self.curr + 1
		# List of Chord objects
		self.elements = []
		# Dummy Chord object to return when at end of stack
		self.dummy = Chord()
		
	def AddElement(self, listPitches, listQualities, currentMode):
		""" Add an item to the stack """
		self.elements.append(Chord())
		# TODO: Prevent repetitions
		self.elements[-1].GenerateRandom(listPitches, listQualities, currentMode)
		
	def Initialize(self, listPitches, listQualities, currentMode):
		""" Allocate items according to the current definitions """
		for i in range(0, self.nbElements):
# 			self.elements.append(Chord().GenerateRandom(listPitches, listQualities, currentMode))
			# TODO: Prevent repetitions
			self.AddElement(listPitches, listQualities, currentMode)
		
	def Next(self):
		""" Shift indices to display the next item """
		if self.curr < self.nbElements - 1:
			self.curr += 1
		
	def Prev(self):
		""" Shift indices to display the previous item """
		if self.curr > 0:
			self.curr -= 1
			
	def UpdateStack(self, listPitches, listQualities, currentMode):
		""" Remove old elements and append new ones """
		self.elements.pop(0)
		# TODO: Prevent repetitions
		self.AddElement(listPitches, listQualities, currentMode)
		
	def RecreateNext(self, listPitches, listQualities, currentMode):
		""" Redefine elements up the list in case of a change in properties """
		# Remove the last elements in the list up to the next chord
		del self.elements[self.nbFurtherItems + 1:]
		# Add new elements conforming to the new prescriptions
		for i in range(0, self.nbFurtherItems - 1):
			# TODO: Prevent repetitions
			self.AddElement(listPitches, listQualities, currentMode)

	def GetCurrent(self):
		""" Return the current chord object """
		return self.elements[self.curr]
	
	def GetPrev(self):
		""" Return the previous chord object """
		if self.curr > 0:
			return self.elements[self.curr - 1]
		else:
			return self.dummy
		
	def GetNext(self):
		""" Return the next chord object """
		if self.curr < self.nbElements - 1:
			return self.elements[self.curr + 1]
		else:
			return self.dummy
				
class ChordTraining(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(ChordTraining, self).__init__(*args, **kwargs) 

		# Default settings (overridden by settings from file ~/.chord_training/settings, if it exists)
		# self.pitches = {'C': 1, 'F': 1, 'Bb': 1, 'Eb': 1, 'Ab': 1, 'Db': 1, 'F#': 1, 'B': 1, 'E': 0, 'A': 0, 'D': 0, 'G': 0}
		self.pitches = collections.OrderedDict()
		self.pitches['C'] = True
		self.pitches['F'] = True
		self.pitches['Bb'] = True
		self.pitches['Eb'] = True
		self.pitches['Ab'] = True
		self.pitches['Db'] = True
		self.pitches['F#'] = True
		self.pitches['B'] = False
		self.pitches['E'] = False
		self.pitches['A'] = False
		self.pitches['D'] = False
		self.pitches['G'] = False
		# self.qualities = {'min7': 1, '7': 1, 'Maj7': 1}
		self.qualities = collections.OrderedDict()
		self.qualities['min7'] = True
		self.qualities['7'] = True
		self.qualities['Maj7'] = True
		self.qualities['min'] = False
		self.qualities['Maj'] = False
		self.qualities['7sus4'] = False
		self.qualities['dim7'] = False
		self.qualities['min7b5'] = False
		self.qualities['aug'] = False

		self.modes = collections.OrderedDict()
		self.modes['Chord'] = True
		self.modes['II-V-I'] = False
		self.modes['V-I'] = False

		self.duration = 5  # s
		self.durationMin = 1  # s
		self.durationMax = 10  # s
		self.elapsedTime = 0  # ms
		self.refreshPeriod = 50  # ms

		#  Display chord/scale score by default
		self.displayScore = True
		self.displayScale = True
		# Default image in case no proper chord is selected or when the score 
		# is inactive
		self.defaultImage = wx.EmptyImage(5, 5).ConvertToBitmap()
		# Resolution for the score images
		self.scoreRes = 150
		
		self.hSpacerLength = 50
		self.vSpacerLength = 25
		
		# Default window size
		self.windowSizeX = 500
		self.windowSizeY = 400
		
		# Use only one thread on slower machines 
		# when generating scores using lilypond
		self.singleThread = True

		# Default font size for chord names
		self.fontSize = 64
		self.fontSizes = collections.OrderedDict()
		self.fontSizes['24'] = False
		self.fontSizes['36'] = False
		self.fontSizes['48'] = False
		self.fontSizes['64'] = True
		self.fontSizes['72'] = False
		self.fontSizes['96'] = False
		self.fontSizes['128'] = False
		self.fontSizes['144'] = False
		self.fontSizeMin = int(self.fontSizes.keys()[0])
		self.fontSizeMax = int(self.fontSizes.keys()[-1])
		
		# Default resolution for scores
		self.scoreRes = 150
		self.scoreRess = collections.OrderedDict()
		self.scoreRess['100'] = False
		self.scoreRess['150'] = True
		self.scoreRess['200'] = False
		self.scoreRess['300'] = False
		self.scoreResMin = int(self.scoreRess.keys()[0])
		self.scoreResMax = int(self.scoreRess.keys()[-1])
		
		# Path to file where the settings are saved		
		home = expanduser("~")
		self.directory = os.path.join(home, ".chord_training")
		# Create directory in case it doesn't exist
		if not os.path.isdir(self.directory):
			os.makedirs(self.directory)
		self.savefile = os.path.join(self.directory, "settings")	

		# Trick the system to disable screen savers during training
		self.moveMouse = True
		
		# Prevent the screensaver from starting
		self.stayOn = StayOn()
		
		# Set pause to off
		self.pause = False  
		
		# Attempt to read other settings from the savefile, in case it exists
		self.LoadSettings()
		
		# Override setting in case the feature is unavailable
		if not self.stayOn.isEnabled():
			self.moveMouse = False
		
		self.SetChord()
		
		# Set up the menus
		self.InitMenus()
		
		# Set up the layout
		self.InitUI()
		
		# Set up the timer to refresh the display
		self.SetTimer()

		# Define keyboard shortcuts
		self.KeyBindings()

		# Set elapsed time so that the layout is refreshed immediately at the start of the program
		self.elapsedTime = self.duration * 1000
		self.changedLayout = True
		
		# Indicators for new parameters (when True leads to a renewal of the upcoming chords in the stack)
		self.changedParameters = False
		
		self.Centre()
		self.Show(True)
		
	def SaveSettings(self, event=None):
		
		f = open(self.savefile, "w")
		
		f.write("#Chord Training settings\n")
		f.write("Tones:\n")
		for tone in self.pitches.keys():
			f.write("\t%s\t%s\n" % (tone, self.pitches[tone]))
		f.write("Qualities:\n")
		for quality in self.qualities.keys():
			f.write("\t%s\t%s\n" % (quality, self.qualities[quality]))
		f.write("Mode:\n")
		for mode in self.modes.keys():
			if self.modes[mode]:
				f.write("\t%s\n" % mode)
		f.write("Duration:\n")
		f.write("%d\n" % self.duration)
		f.write("WindowSize:\n")
		size = self.GetSize()
		f.write("\t%d\t%d\n" % (size.x, size.y))
		f.write("FontSize:\n")
		f.write("\t%d\n" % self.fontSize)
		f.write("ScoreResolution:\n")
		f.write("\t%d\n" % self.scoreRes)
		f.write("SingleThread:\n")
		f.write("\t%r\n" % self.singleThread)
		f.write("DisplayScore:\n")
		f.write("\t%s\n" % self.displayScore)
		f.write("DisplayScale:\n")
		f.write("\t%s\n" % self.displayScale)
		f.write("StayOn:\n")
		f.write("\t%s\n" % self.moveMouse)
								
		f.close()


	def LoadSettings(self):
		try:
			context = None
			with open(self.savefile) as f:
				for line in f:
					line = line.rstrip()
					match = re.match(r"^\s*#", line)
					if match is not None:
						continue
					match = re.match(r"^\s*(?P<section>\w+)\s*:$", line)
					if match is not None:
						context = match.group('section')
						continue
					items = line.split()
					
					if context == "Tones":
						tone = items[0]
						try:
							state = items[1].lower() == 'true'
						except:
							state = False
						self.pitches[tone] = state
					elif context == "Qualities":
						quality = items[0]
						try:
							state = items[1].lower() == 'true'
						except:
							state = False
						self.qualities[quality] = state		      
					elif context == "Mode":
						mode = items[0]
						for modeTest in self.modes.keys():
							if mode == modeTest:
								self.modes[modeTest] = True
							else:
								self.modes[modeTest] = False
					elif context == "Duration":
						duration = int(items[0])
						self.duration = duration
					elif context == "WindowSize":
						self.windowSizeX = int(items[0])
						self.windowSizeY = int(items[1])
					elif context == "FontSize":
						self.fontSize = int(items[0])
						for fontSize in self.fontSizes.keys():
							if int(fontSize) == self.fontSize:
								self.fontSizes[fontSize] = True
							else:
								self.fontSizes[fontSize] = False
					elif context == "ScoreResolution":
						self.scoreRes = int(items[0])
						for scoreRes in self.scoreRess.keys():
							if int(scoreRes) == self.scoreRes:
								self.scoreRess[scoreRes] = True
							else:
								self.scoreRess[scoreRes] = False
					elif context == "SingleThread":
						if items[0].lower() == 'false':
							self.singleThread = False
						else:
							self.singleThread = True
					elif context == "DisplayScore":
						if items[0].lower() == 'false':
							self.displayScore = False
						else:
							self.displayScore = True
					elif context == "DisplayScale":
						if items[0].lower() == 'false':
							self.displayScale = False
						else:
							self.displayScale = True
					elif context == "StayOn":
						if items[0].lower() == 'false':
							self.moveMouse = False
						else:
							self.moveMouse = True								
		except:
			pass

		# Check that the data read makes sense
		# There should be only one mode selected
		nbModes = 0
		for mode in self.modes.keys():
			if self.modes[mode]:
				nbModes += 1
		if nbModes != 1:
			first = True
			for mode in self.modes:
				if first:
					self.modes[mode] = True
				else:
					self.modes[mode] = False
				first = False
				
		# The duration should be an integer value between durationMin and durationMax
		if (self.duration < self.durationMin or self.duration > self.durationMax):
			self.duration = int((self.durationMax - self.durationMin) / 2 + 1)
			
		# Check that the given font size is legal
		nbFontSizes = 0
		for fontSize in self.fontSizes.keys():
			if self.fontSizes[fontSize]:
				nbFontSizes += 1
		if nbFontSizes != 1:
			first = True
			for fontSize in self.fontSizes.keys():
				if first:
					self.fontSizes[fontSize] = True
					self.fontSize = int(fontSize)
					first = False
				else:
					self.fontSizes[fontSize] = False

		# Check that the given score resolution is legal
		nbScoreRess = 0
		for scoreRes in self.scoreRess.keys():
			if self.scoreRess[scoreRes]:
				nbScoreRess += 1
		if nbScoreRess != 1:
			first = True
			for scoreRes in self.scoreRess.keys():
				if first:
					self.scoreRess[scoreRes] = True
					self.scoreRes = int(scoreRes)
					first = False
				else:
					self.scoreRess[scoreRes] = False
	
	def UpdateFontSize(self):
		if self.fontSize != self.fontSizeOld:
			self.font = wx.Font(self.fontSize, wx.SWISS, wx.NORMAL, wx.NORMAL)
			self.chordDisplay.SetFont(self.font)
			
			self.fontSmaller = wx.Font(self.getSmallerFontsize(self.fontSize), wx.SWISS, wx.NORMAL, wx.NORMAL)
			self.chordDisplayPrev.SetFont(self.fontSmaller)
			self.chordDisplayNext.SetFont(self.fontSmaller)

			self.fontStatus = wx.Font(self.getSmallerFontsize(self.fontSize), wx.SWISS, wx.NORMAL, wx.NORMAL)
			
			self.scaleNameTitle.SetFont(self.fontSmaller)
			self.scaleName.SetFont(self.font)
			self.status.SetFont(self.fontStatus)

			self.fontSizeOld = self.fontSize
# 			self.changedLayout = True
			
	def PrepareImage(self, currChord, imageMode):
		try:
			# Set the image for the score
			if imageMode == "Chord" and not self.displayScore:
				raise NoImage
			elif imageMode == "Scale" and not self.displayScale:
				raise NoImage
			else:
				try:
					if imageMode == "Chord":
						imageFile = currChord.GetImgName(self.scoreRes)
					elif imageMode == "Scale":
						imageFile = currChord.GetScaleImgName(self.scoreRes)
					else:
						raise
				except:
					raise NoImage
			imageFile = os.path.join(self.directory, imageFile)
			try:
				with open(imageFile): pass
				png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
			except IOError:
				raise NoImage

		except NoImage:
			png = self.defaultImage
			# Only attempt to generate the score if: 
			# - there is a proper chord
			# - the score is enabled
			if imageMode == "Chord" and currChord.GetPitch() != "-" and self.displayScore:
				self.GenerateImage(currChord)
			elif imageMode == "Scale" and currChord.GetPitch() != "-" and self.displayScale:
				self.GenerateScaleImage(currChord)
				
		if imageMode == "Chord":		
			self.chordImage.SetBitmap(png)
		elif imageMode == "Scale":		
			self.scaleImage.SetBitmap(png)
					
	def GenerateImage(self, chord):
		basisHeader = '''
#(set-default-paper-size "a4")

\\version "2.16.2"

\\include "english.ly"
'''
		basisUpperBeginning = '''
upper = \\relative c' {
  \\clef treble
  \\key c \\major
  %\\time 4/4
'''
		basisUpperContentChord = '''  
  r1
  r
  <chordForm1>1
  <chordForm2>1 
'''
		basisContentII_V_I = '''  
  <IIchordForm1>2
  <IIchordForm2>2 
  <VchordForm1>2
  <VchordForm2>2
  <IchordForm1>2
  <IchordForm2>2
'''
		basisContentV_I = '''  
  <VchordForm1>2
  <VchordForm2>2
  <IchordForm1>2
  <IchordForm2>2
'''
		basisUpperEnd = '''
}
'''
		basisLowerBeginning = '''
lower = \\relative c {
  \\clef bass
  \\key c \\major
  %\\time 4/4
'''
		basisLowerContentChord = '''  
  <chordForm1>1
  <chordForm2>1 
  r1
  r
'''
		basisLowerEnd = '''
}
'''
		basisFooter = '''
\\score {
  \\new PianoStaff %\\with { \\remove "Staff_symbol_engraver" } 
  <<
    \\set PianoStaff.instrumentName = #""
    \\new Staff  = "upper" \\transpose c c \\upper
    \\new Staff = "lower" \\transpose c c \\lower
  >>
  \\layout { }
  %\\midi { }
}
'''
		if chord.GetMode() == 'Chord':
			lyfile = chord.GetLyName(self.scoreRes)
			content = basisHeader + \
			basisUpperBeginning + \
			basisUpperContentChord + \
			basisUpperEnd + \
			basisLowerBeginning + \
			basisLowerContentChord + \
			basisLowerEnd + \
			basisFooter
		elif chord.GetMode() == 'II-V-I':
			lyfile = chord.GetLyName(self.scoreRes)
			content = basisHeader + \
			basisUpperBeginning + \
			basisContentII_V_I + \
			basisUpperEnd + \
			basisLowerBeginning + \
			basisContentII_V_I + \
			basisLowerEnd + \
			basisFooter
		elif chord.GetMode() == 'V-I':
			lyfile = chord.GetLyName(self.scoreRes)
			content = basisHeader + \
			basisUpperBeginning + \
			basisContentV_I + \
			basisUpperEnd + \
			basisLowerBeginning + \
			basisContentV_I + \
			basisLowerEnd + \
			basisFooter
		else:
			# Unsupported mode
			raise
		
		lyfile = os.path.join(self.directory, lyfile)
		f = open(lyfile, "w")
				
		if chord.GetMode() == 'Chord':
			# Substitute the chord placeholder with the actual chord definition for the appropriate qualities (in C)
			if chord.GetQuality() == "Maj7":
				content = re.sub(r"chordForm1", r"b c e g", content)
				content = re.sub(r"chordForm2", r"e g a d", content)
			elif chord.GetQuality() == "7":
				content = re.sub(r"chordForm1", r"e a bf d", content)
				content = re.sub(r"chordForm2", r"bf d e a", content)
				content = re.sub(r"\\key c \\major", r"\\key f \\major", content)
			elif chord.GetQuality() == "min7":
				content = re.sub(r"chordForm1", r"ef g bf d", content)
				content = re.sub(r"chordForm2", r"bf d ef g", content)
				content = re.sub(r"\\key c \\major", r"\\key bf \\major", content)
			elif chord.GetQuality() == "dim7":
				content = re.sub(r"chordForm1", r"c ef gf a", content)
				content = re.sub(r"chordForm2", r"c ef gf b", content)
			else:
				# TODO: Other qualities not yet implemented...
				content = re.sub(r"chordForm1", r"c e g", content)
				content = re.sub(r"chordForm2", r"c e g", content)
				scalePitch = 'C'
		elif chord.GetMode() == 'II-V-I':
			content = re.sub(r"IIchordForm1", r"f a c e", content)
			content = re.sub(r"IIchordForm2", r"c e f a", content)
			content = re.sub(r"VchordForm1", r"f a b e", content)
			content = re.sub(r"VchordForm2", r"b, e f a", content)
			content = re.sub(r"IchordForm1", r"e g a d", content)
			content = re.sub(r"IchordForm2", r"b c e g", content)
		elif chord.GetMode() == 'V-I':
			content = re.sub(r"VchordForm1", r"f a b e", content)
			content = re.sub(r"VchordForm2", r"b e f a", content)
			content = re.sub(r"IchordForm1", r"e g a d", content)
			content = re.sub(r"IchordForm2", r"b c e g", content)
		else:
			# Unsupported mode
			raise
		
		# Transpose if needed
		if chord.GetPitch() != 'C':
			content = re.sub(r"transpose c c", r"transpose c %s" % chord.GetLyPitch().lower(), content)
		f.write(content)
		f.close()

		self.CallLilypond(lyfile)
		
	def GenerateScaleImage(self, chord):
		basisHeader = '''
#(set-default-paper-size "a4")

\\version "2.16.2"

\\include "english.ly"
'''
		basisUpperBeginning = '''
notes = \\relative c' {
  scaleDefinition 
}

upper = \\relative c' {
  \\clef treble
  \\key c \\major
  %\\time 4/4
'''
		basisUpperContentMajorScale = '''  
\\transpose c c \\notes
'''

		basisUpperEnd = '''
}
'''
		basisFooter = '''
\\score {
  \\upper
  \\layout { }
  %\\midi { }
}
'''
		if chord.GetScaleKind() == 'Major' or chord.GetScaleKind() == 'Diminished':
			lyfile = chord.GetLyScaleName(self.scoreRes)
			content = basisHeader + \
			basisUpperBeginning + \
			basisUpperContentMajorScale + \
			basisUpperEnd + \
			basisFooter
			if chord.GetScaleKind() == 'Major':
				content = re.sub(r"scaleDefinition", r"c d e f g a b c", content)
			elif chord.GetScaleKind() == 'Diminished':
				content = re.sub(r"scaleDefinition", r"c d ef f gf af a b c", content)
		else:
			# Unsupported mode
			raise
		
		lyfile = os.path.join(self.directory, lyfile)
		f = open(lyfile, "w")
		
		# Transpose if needed
		if chord.GetScalePitch() != 'C':
			content = re.sub(r"transpose c c", r"transpose c %s" % chord.GetLyScalePitch().lower(), content)
		f.write(content)
		f.close()

		self.CallLilypond(lyfile)
		
	def CallLilypond(self, lyfile):
		try:
			catOutputFile = os.path.join(self.directory, "cat_outputFile")
			f = open(catOutputFile, "w")
	
			rc = call(["cat", lyfile], stdout=f)
			f.close()
		
			print "rc = %s" % rc
			# The lilypond call apparently won't work properly without an explicit stdout redirection...
			lilypondOutputFile = os.path.join(self.directory, "lilypond_outputFile")
			f = open(lilypondOutputFile, "w")			
			proc = Popen(["lilypond", "--png", "-dresolution=" + str(self.scoreRes), "-dpreview", lyfile], stdout=f, cwd=self.directory)
			# Do not continue after starting the lilypond process
			# (useful on slower machines, e.g. raspberryPi 
			if self.singleThread:
				proc.wait()
				
			f.close()
			print "rc = %s" % rc
		except:
			print "Call to lilypond failed."
					
	def OnTimer(self, whatever):
		if self.pause:
			return
		self.elapsedTime += self.refreshPeriod

		# Move the mouse by one pixel so as to avoid the screensaver
		if self.moveMouse:
			self.stayOn.moveMouse(self.refreshPeriod/1000.)

		# Update time gauge
		value = self.elapsedTime/self.duration/1000.*100.
		self.timeGauge.SetValue(min(value, self.timeGaugeMax))
		
		if self.elapsedTime <= self.duration * 1000:
			return
		self.elapsedTime = 0

		# Renew upcoming chords in the stack upon changes in the parameters
		if self.changedParameters:
			self.chordStack.RecreateNext(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
			self.changedParameters = False

		# Current chord
		currChord = self.chordStack.GetCurrent()
		
		# Previous and next chords
		prevChord = self.chordStack.GetPrev()
		nextChord = self.chordStack.GetNext()
		
		# Update mode
		currChord.SetMode(self.CurrentMode())
		prevChord.SetMode(self.CurrentMode())
		nextChord.SetMode(self.CurrentMode())
		
		# Update chord display
		self.chordDisplay.SetLabel(currChord.GetName())
		self.chordDisplayPrev.SetLabel(prevChord.GetName())
		self.chordDisplayNext.SetLabel(nextChord.GetName())
		
		# Update scale name
		self.scaleName.SetLabel(currChord.GetScale())
		
		self.PrepareImage(currChord, "Chord")

		self.PrepareImage(currChord, "Scale")

		self.UpdateFontSize()
			
		# Reset the sizer's size (so that the text window has the right size)		
		if self.changedLayout:
			self.changedLayout = False
			self.FitLayout()
			
		# TEST
# 		mode = self.CurrentMode()
# 		tmp = Chord(self.chord.GetPitch(), self.chord.GetQuality(), mode)
# 		tmp.GenerateRandom(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
# 		tmp = ""
# 		tmp += self.chordStack.GetPrev().GetName()
# 		tmp += " / "
# 		tmp += self.chordStack.GetCurrent().GetName()
# 		tmp += " / "
# 		tmp += self.chordStack.GetNext().GetName()
# 		self.status.SetLabel(tmp)

 		# Append a new chord to the stack		
 		self.chordStack.UpdateStack(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
		# Shift the stack so that the next chord is displayed on the next call
# 		self.chordStack.Next()
		
	def getSmallerFontsize(self, fontsize):
		return fontsize/2
	
	def InitMenus(self):
		# Menus
		menubar = wx.MenuBar()

		# Menu: FILE
		fileMenu = wx.Menu()

		fileMenu.Append(wx.ID_NEW, '&New')
		fileMenu.Append(wx.ID_OPEN, '&Open')
		fileMenu.Append(wx.ID_SAVE, '&Save')
		self.Bind(wx.EVT_MENU, self.SaveSettings, id=wx.ID_SAVE)

# 		fileMenu.Append(wx.ID_EXIT, '&Quit')
# 		self.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)

		qmi = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit\tCtrl+W')
		fileMenu.AppendItem(qmi)

		self.Bind(wx.EVT_MENU, self.OnQuit, qmi)

		menubar.Append(fileMenu, '&File')

		# Menu: MODE
		modeMenu = wx.Menu()
		self.modeMenuId = {}
		self.modeMenuIdRev = {}
		for mode in self.modes.keys():
			self.modeMenuId[mode] = wx.NewId()
			self.modeMenuIdRev[self.modeMenuId[mode]] = mode
			modeMenu.Append(self.modeMenuId[mode], mode, "", wx.ITEM_RADIO)
			modeMenu.Check(self.modeMenuId[mode], self.modes[mode])
			self.Bind(wx.EVT_MENU, self.MenuSetMode, id=self.modeMenuId[mode])
		menubar.Append(modeMenu, '&Mode')

		# Menu: TONES
		self.tonesMenu = wx.Menu()
		self.tonesMenuId = {}
		self.tonesMenuIdRev = {}
		for tone in self.pitches.keys():
			self.tonesMenuId[tone] = wx.NewId()
			self.tonesMenuIdRev[self.tonesMenuId[tone]] = tone
			self.tonesMenu.Append(self.tonesMenuId[tone], tone, "", wx.ITEM_CHECK)
			self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
			self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesMenuId[tone])
			
		self.tonesMenu.AppendSeparator()
		self.tonesFuncId = {\
						"all" : wx.NewId(),\
						"none" : wx.NewId(),\
						"invert" : wx.NewId()\
						}
		self.tonesMenu.Append(self.tonesFuncId["all"], "All")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["all"])
		self.tonesMenu.Append(self.tonesFuncId["none"], "None")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["none"])
		self.tonesMenu.Append(self.tonesFuncId["invert"], "Invert")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["invert"])
					
		menubar.Append(self.tonesMenu, '&Tones')

		# Menu: QUALITIES
		self.qualitiesMenu = wx.Menu()
		self.qualitiesMenuId = {}
		self.qualitiesMenuIdRev = {}
		for quality in self.qualities.keys():
			self.qualitiesMenuId[quality] = wx.NewId()
			self.qualitiesMenuIdRev[self.qualitiesMenuId[quality]] = quality
			self.qualitiesMenu.Append(self.qualitiesMenuId[quality], quality, "", wx.ITEM_CHECK)
			self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
			self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesMenuId[quality])
			self.qualitiesMenu.Enable(self.qualitiesMenuId[quality], self.modes['Chord'])
				
		menubar.Append(self.qualitiesMenu, '&Qualities')
			
		# Menu: DURATION
		durationMenu = wx.Menu()
		self.durationMenuId = {}
		self.durationMenuIdRev = {}
		self.duration = int(self.duration)
		if self.duration < self.durationMin or self.duration > self.durationMax:
			self.duration = int(0.5 * (self.durationMax - self.durationMin + 1))
		for duration in range(self.durationMin, self.durationMax + 1):
			self.durationMenuId[duration] = wx.NewId()
			self.durationMenuIdRev[self.durationMenuId[duration]] = duration
			durationMenu.Append(self.durationMenuId[duration], "%d" % duration, "", wx.ITEM_RADIO)
			if duration == self.duration:
				durationMenu.Check(self.durationMenuId[duration], True)
			self.Bind(wx.EVT_MENU, self.MenuSetDuration, id=self.durationMenuId[duration])

		menubar.Append(durationMenu, '&Duration')

		# Menu: SETTINGS
		settingsMenu = wx.Menu()
		fontSizeMenu = wx.Menu()
		self.fontSizeMenuId = {}
		self.fontSizeMenuIdRev = {}
		for fontSize in self.fontSizes.keys():
			self.fontSizeMenuId[fontSize] = wx.NewId()
			self.fontSizeMenuIdRev[self.fontSizeMenuId[fontSize]] = fontSize
			fontSizeMenu.Append(self.fontSizeMenuId[fontSize], "%s" % fontSize, "", wx.ITEM_RADIO)
			if int(fontSize) == self.fontSize:
				fontSizeMenu.Check(self.fontSizeMenuId[fontSize], True)
			self.Bind(wx.EVT_MENU, self.MenuSetFontSize, id=self.fontSizeMenuId[fontSize])

		scoreResMenu = wx.Menu()
		self.scoreResMenuId = {}
		self.scoreResMenuIdRev = {}
		for scoreRes in self.scoreRess.keys():
			self.scoreResMenuId[scoreRes] = wx.NewId()
			self.scoreResMenuIdRev[self.scoreResMenuId[scoreRes]] = scoreRes
			scoreResMenu.Append(self.scoreResMenuId[scoreRes], "%s" % scoreRes, "", wx.ITEM_RADIO)
			if int(scoreRes) == self.scoreRes:
				scoreResMenu.Check(self.scoreResMenuId[scoreRes], True)
			self.Bind(wx.EVT_MENU, self.MenuSetScoreRes, id=self.scoreResMenuId[scoreRes])

		singleThreadId = wx.NewId()
		settingsMenu.Append(singleThreadId, "Single &thread", "", wx.ITEM_CHECK)
		settingsMenu.Check(singleThreadId, self.singleThread)
		self.Bind(wx.EVT_MENU, self.MenuSetSingleThread, id=singleThreadId)

		displayScoreId = wx.NewId()
		settingsMenu.Append(displayScoreId, "&Display score", "", wx.ITEM_CHECK)
		settingsMenu.Check(displayScoreId, self.displayScore)
		self.Bind(wx.EVT_MENU, self.MenuSetDisplayScore, id=displayScoreId)

		displayScaleId = wx.NewId()
		settingsMenu.Append(displayScaleId, "D&isplay scale", "", wx.ITEM_CHECK)
		settingsMenu.Check(displayScaleId, self.displayScale)
		self.Bind(wx.EVT_MENU, self.MenuSetDisplayScale, id=displayScaleId)

		stayOnId = wx.NewId()
		settingsMenu.Append(stayOnId, "Disable &Screensaver", "", wx.ITEM_CHECK)
		settingsMenu.Check(stayOnId, self.moveMouse)
		self.Bind(wx.EVT_MENU, self.MenuSetStayOn, id=stayOnId)
		settingsMenu.Enable(stayOnId, self.stayOn.isEnabled())

		settingsMenu.AppendSeparator()

		settingsMenu.AppendMenu(wx.ID_ANY, '&Font size', fontSizeMenu)
		settingsMenu.AppendMenu(wx.ID_ANY, '&Score resolution', scoreResMenu)

		lilypondPathMenu = wx.Menu()
		lilypondPathId = wx.NewId()
		pathToLilypond = "test"
		lilypondPathMenu.Append(lilypondPathId, "%s" % pathToLilypond)
		lilypondPathMenu.Enable(lilypondPathId, False)
		lilypondPathMenu.AppendSeparator()
		editLilypondPathId = wx.NewId()
		lilypondPathMenu.Append(editLilypondPathId, "Edit...")

		settingsMenu.AppendMenu(wx.ID_ANY, '&Path to Lilypond', lilypondPathMenu)

		menubar.Append(settingsMenu, '&Settings')

		self.SetMenuBar(menubar)

	def SetChord(self):
# 		self.chord = Chord(self)

		self.chordStack = ChordStack()
		self.chordStack.Initialize(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
		
		# Chord
		self.fontSize = 0
		for fontSize in self.fontSizes.keys():
			if self.fontSizes[fontSize]:
				if self.fontSize == 0:
					self.fontSize = int(fontSize)
				else:
					self.fontSize = -1
		if self.fontSize <= 0:
			first = True
			for fontSize in self.fontSizes.keys():
				if first:
					self.fontSize = int(fontSize)
					self.fontSizes[fontSize] = True
					first = False
				else:
					self.fontSizes[fontSize] = False
					
		self.fontSizeOld = self.fontSize

		# Font for chord display
		self.font = wx.Font(self.fontSize, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.fontSmaller = wx.Font(self.getSmallerFontsize(self.fontSize), wx.SWISS, wx.NORMAL, wx.NORMAL)

		# Font for the status bar
		self.fontStatus = wx.Font(self.getSmallerFontsize(self.fontSize), wx.SWISS, wx.NORMAL, wx.NORMAL)

	def InitUI(self):

		self.SetSize((self.windowSizeX, self.windowSizeY))
		self.SetTitle('Chord Training')
		
		self.panel = wx.Panel(self, -1)

 		# Spacers to add room around objects 
 		hSpacer = wx.Size(self.hSpacerLength, 0)
 		vSpacer = wx.Size(0, self.vSpacerLength)
 		
		self.SetBackgroundColour(wx.WHITE)
		self.layout = wx.BoxSizer(wx.VERTICAL)

		# Current chord, previous and next
		row = wx.BoxSizer(wx.HORIZONTAL)
		self.chordDisplayPrev = wx.StaticText(self,label="Prev")#,style=wx.BORDER_DOUBLE)
		self.chordDisplayPrev.SetFont(self.fontSmaller)
		self.chordDisplayPrev.SetForegroundColour('GREY')
				
		self.chordDisplay = wx.StaticText(self,label="Chord")#,style=wx.BORDER_DOUBLE)
		self.chordDisplay.SetFont(self.font)
		
		self.chordDisplayNext = wx.StaticText(self,label="Next")#,style=wx.BORDER_DOUBLE)
		self.chordDisplayNext.SetFont(self.fontSmaller)
		self.chordDisplayNext.SetForegroundColour('GREY')
		
		row.Add(self.chordDisplayPrev,1, wx.EXPAND|wx.ALL,10)
		row.Add(self.chordDisplay,2, wx.EXPAND|wx.ALL,10)
		row.Add(self.chordDisplayNext,1, wx.EXPAND|wx.ALL,10)
		self.layout.Add(row, 0, wx.EXPAND) # add row 4 with proportion = 0 and wx.EXPAND

		# Time gauge
		self.timeGaugeMax = 100
		self.timeGaugeCurrent = 0
 		self.timeGauge = wx.Gauge(self, id=wx.NewId(), range=self.timeGaugeMax, style=wx.GA_HORIZONTAL)
 		self.timeGauge.SetRange(self.timeGaugeMax)

 		hboxGauge = wx.BoxSizer(wx.HORIZONTAL)
  		hboxGauge.Add(hSpacer, 0, wx.EXPAND|wx.ALL, 10)
  		hboxGauge.Add(self.timeGauge, 1, wx.EXPAND|wx.ALL, 10)
  		hboxGauge.Add(hSpacer, 0, wx.EXPAND|wx.ALL, 10)

		self.layout.Add(hboxGauge,0,wx.EXPAND) # add gauge
		
		self.maxWidthScale = wx.Size(5, 0)
		self.maxHeightScale = wx.Size(0, 5)

		hboxImgSize = wx.BoxSizer(wx.HORIZONTAL)
		hboxImgSize.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		hboxImgSize.Add(self.maxWidthScale, 1, wx.EXPAND|wx.ALL, 10) # add image
		hboxImgSize.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		self.layout.Add(hboxImgSize, 0, wx.EXPAND)
			
 		self.chordImage = wx.StaticBitmap(self, -1, wx.EmptyImage(5, 5).ConvertToBitmap())
		
		# Chord score
		self.layout.Add(vSpacer)
		hboxImg = wx.BoxSizer(wx.HORIZONTAL)
		hboxImg.Add(self.maxHeightScale, 0, wx.EXPAND|wx.ALL,10)
		hboxImg.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		hboxImg.Add(self.chordImage, 1, wx.EXPAND | wx.ALL, 10) # add image
		hboxImg.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		self.layout.Add(hboxImg,0,wx.EXPAND)
		self.layout.Add(vSpacer)
 
		self.toneIndex = 0
		self.scaleImage = wx.StaticBitmap(self, -1, wx.EmptyImage(5, 5).ConvertToBitmap())

		self.maxWidthScale = wx.Size(5, 0)
		self.maxHeightScale = wx.Size(0, 5)
 
		hboxImgSize2 = wx.BoxSizer(wx.HORIZONTAL)
		hboxImgSize2.Add(hSpacer, 0, wx.EXPAND|wx.ALL, 10)
		hboxImgSize2.Add(self.maxWidthScale, 1, wx.EXPAND|wx.ALL, 10) # add image
		hboxImgSize2.Add(hSpacer, 0, wx.EXPAND|wx.ALL, 10)
		self.layout.Add(hboxImgSize2, 0, wx.EXPAND)
		self.layout.Add(vSpacer)
		 			
		# Scale name 
		row = wx.BoxSizer(wx.HORIZONTAL)
		self.scaleNameTitle = wx.StaticText(self,label="Scale:")
		self.scaleNameTitle.SetFont(self.fontSmaller)
		self.scaleName = wx.StaticText(self,label="")
		self.scaleName.SetFont(self.font)
		self.scaleNameDummy = wx.StaticText(self,label="")
		self.scaleNameDummy.SetFont(self.fontSmaller)
		
		row.Add(self.scaleNameTitle,1, wx.EXPAND|wx.ALL,10)
		row.Add(self.scaleName,2, wx.EXPAND|wx.ALL,10)
		row.Add(self.scaleNameDummy,1, wx.EXPAND|wx.ALL,10)
		self.layout.Add(row, 0, wx.EXPAND) # add row 4 with proportion = 0 and wx.EXPAND

		# Scale score
		self.layout.Add(vSpacer)
		hboxImg2 = wx.BoxSizer(wx.HORIZONTAL)
		hboxImg2.Add(self.maxHeightScale, 0, wx.EXPAND|wx.ALL,10)
		hboxImg2.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		hboxImg2.Add(self.scaleImage, 1, wx.EXPAND|wx.ALL, 10) # add image
		hboxImg2.Add(hSpacer, 0, wx.EXPAND|wx.ALL,10)
		self.layout.Add(hboxImg2, 0, wx.EXPAND)
		self.layout.Add(vSpacer)		

		# Status bar
		self.status = wx.StaticText(self,label="")#,style=wx.BORDER_DOUBLE)
		self.status.SetFont(self.fontStatus)

		statBar = wx.BoxSizer(wx.HORIZONTAL)
		statBar.Add(self.status, 1, wx.EXPAND|wx.ALL,10)
		self.layout.Add(statBar, 0, wx.EXPAND)

	def GetMaxSizeChord(self):
		# Determine the size of the largest image
		maxWidth = 5
		maxHeight = 5

		chord = Chord()
		
		listPitches = self.AvailablePitches()
		
		mode = self.CurrentMode()
		chord.SetMode(mode)
		
		if mode == 'II-V-I' or mode == 'V-I':
			listQualities = ['Maj7']
		else:
			listQualities = self.AvailableQualities()
			
		for pitch in listPitches:
			chord.SetPitch(pitch)
			for quality in listQualities:
				chord.SetQuality(quality)
				imageFile = chord.GetImgName(self.scoreRes)
				imageFile = os.path.join(self.directory, imageFile)
				try:
					png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
					maxWidth = max(maxWidth, png.GetWidth())
					maxHeight = max(maxHeight, png.GetHeight())
				except:
					pass
		
		return (maxWidth, maxHeight)
	
	def FitLayout(self):
		"""Update layout when some objects changed size"""
		
		(maxWidth, maxHeight) = self.GetMaxSizeChord()
		self.maxWidthScale = wx.Size(maxWidth, 0)
		self.maxHeightScale = wx.Size(0, maxHeight)

# 		(maxWidth, maxHeight) = self.GetMaxSizeScale()
# 		self.maxWidthScale = wx.Size(maxWidth, 0)
# 		self.maxHeightScale = wx.Size(0, maxHeight)

		self.SetSizerAndFit(self.layout)

	def SetTimer(self):
		timerId = wx.NewId()
		self.timer = wx.Timer(self, timerId)  # message will be sent to the self.panel
		self.timer.Start(self.refreshPeriod)  # milliseconds
		wx.EVT_TIMER(self, timerId, self.OnTimer)  # call the OnTimer function


	def KeyBindings(self):		
		# Needed to catch key presses (on linux, mac os does not seem to need that...)		
		self.panel.SetFocus()
		 
		# Quit upon pressing ESC
 		self.panel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
# 		lowerPanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
# 		self.upperPanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

	def MenuSetTones(self, evt):
		if evt.GetId() == self.tonesFuncId["all"]:
			for tone in self.pitches.keys():
				self.pitches[tone] = True
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
		elif evt.GetId() == self.tonesFuncId["none"]:
			for tone in self.pitches.keys():
				self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
		elif evt.GetId() == self.tonesFuncId["invert"]:
			for tone in self.pitches.keys():
				self.pitches[tone] = not self.pitches[tone]
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
		else:
			tone = self.tonesMenuIdRev[evt.GetId()]
			self.pitches[tone] = evt.IsChecked()
		# Mark the current parameters as new, so as to renew the chord stack 
		self.changedParameters = True

	def MenuSetQualities(self, evt):
		quality = self.qualitiesMenuIdRev[evt.GetId()]
		self.qualities[quality] = evt.IsChecked()
		# Mark the current parameters as new, so as to renew the chord stack 
		self.changedParameters = True

	def MenuSetMode(self, evt):
		mode = self.modeMenuIdRev[evt.GetId()]
		for modeLoop in self.modes.keys():
			if modeLoop == mode:
				self.modes[modeLoop] = True
			else:
				self.modes[modeLoop] = False
				
		# Disable items in the qualities menu in case the mode 
		# is not set to 'Chord'
		for quality in self.qualities.keys():
		 	self.qualitiesMenu.Enable(self.qualitiesMenuId[quality], self.modes['Chord'])

		# Update the layout
		self.changedLayout = True
		
	def MenuSetDuration(self, evt):
		duration = self.durationMenuIdRev[evt.GetId()]
		self.duration = duration

	def MenuSetFontSize(self, evt):
		fontSize = self.fontSizeMenuIdRev[evt.GetId()]
		for fontSizeLoop in self.fontSizes.keys():
			if fontSizeLoop == fontSize:
				self.fontSizes[fontSizeLoop] = True
				self.fontSize = int(fontSizeLoop)
			else:
				self.fontSizes[fontSizeLoop] = False

		# Update the layout
		self.changedLayout = True

	def MenuSetScoreRes(self, evt):
		scoreRes = self.scoreResMenuIdRev[evt.GetId()]
		for scoreResLoop in self.scoreRess.keys():
			if scoreResLoop == scoreRes:
				self.scoreRess[scoreResLoop] = True
				self.scoreRes = int(scoreResLoop)
			else:
				self.scoreRess[scoreResLoop] = False

		# Update the layout
		self.changedLayout = True

	def MenuSetSingleThread(self, evt):
		self.singleThread = evt.IsChecked()
		
	def MenuSetDisplayScore(self, evt):
		self.displayScore = evt.IsChecked()

		# Update the layout
		self.changedLayout = True
	
	def MenuSetDisplayScale(self, evt):
		self.displayScale = evt.IsChecked()

		# Update the layout
		self.changedLayout = True

	def MenuSetStayOn(self, evt):
		self.moveMouse = evt.IsChecked()
			
	def OnQuit(self, e):
		self.SaveSettings()
		self.Close()

	def OnKeyDown(self, e):
		key = e.GetKeyCode()

		if key == wx.WXK_ESCAPE:
			self.OnQuit(e)
		elif key == wx.WXK_SPACE:
			self.pause = not self.pause
			pauseLabel = "(Paused)"
			if self.pause:
				self.timer.Stop()
				label = pauseLabel
			else:
				self.timer.Start(self.refreshPeriod)  # milliseconds
				label = ""
			self.status.SetLabel(label)
	
	def AvailablePitches(self):
		list = []
		for pitch in self.pitches.keys():
			if self.pitches[pitch]:
				list.append(pitch)
	
		return list
	
	def AvailableQualities(self):
		list = []
		for quality in self.qualities.keys():
			if self.qualities[quality]:
				list.append(quality)
	
		return list
	
	def CurrentMode(self):
		mode = None
		for modeLoop in self.modes.keys():
			if self.modes[modeLoop]:
				mode = modeLoop
				break
			
		return mode
	
def main():
	mw = wx.App()
	ChordTraining(None)
	mw.MainLoop()    


if __name__ == '__main__':
	main()
