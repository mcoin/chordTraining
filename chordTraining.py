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

def pitch2LyPitch(pitch):
	lyPitch = pitch
	lyPitch = re.sub(r"(.)b", r"\1f", lyPitch)
	lyPitch = re.sub(r"(.)#", r"\1s", lyPitch)
	return lyPitch

def lyPitch2Pitch(lyPitch):
	pitch = lyPitch
	pitch = re.sub(r"(.)f", r"\1b", pitch)
	pitch = re.sub(r"(.)s", r"\1#", pitch)
	return pitch

class Chord:
	def __init__(self, chordTraining):
		self.pitch = "-"
		self.quality = "-"
		self.chordTraining = chordTraining
	
	def SetPitch(self, pitch):
		self.pitch = pitch

	def SetQuality(self, quality):
		self.quality = quality
	
	def GetPitch(self):
		return self.pitch
	
	def GetLyPitch(self):
		return pitch2LyPitch(self.pitch)

	def GetQuality(self):
		return self.quality
	
	def Print(self):
		if self.chordTraining.modes['Chord']:
			return self.pitch + " " + self.quality
		elif self.chordTraining.modes['II-V-I'] or self.chordTraining.modes['V-I']:
			try:
				indexPitch = self.chordTraining.pitches.keys().index(self.pitch)
			except:
				return '- -'
			progression = ''
			
			if self.chordTraining.modes['II-V-I']:
				indexIIpitch = indexPitch - 2
				IIpitch = self.chordTraining.pitches.keys()[indexIIpitch]
				progression += IIpitch + ' min7' + '\n'
			
			indexVpitch = indexPitch - 1
			Vpitch = self.chordTraining.pitches.keys()[indexVpitch]	
			progression += Vpitch + ' 7' + '\n'
			
			progression += self.pitch + ' Maj7'
			return progression
		else:
			return "<Unknown mode>"
		
class ChordTraining(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(ChordTraining, self).__init__(*args, **kwargs) 

		# Default settings (overridden by settings from file ~/.chord_training/settings, if it exists)
		#self.pitches = {'C': 1, 'F': 1, 'Bb': 1, 'Eb': 1, 'Ab': 1, 'Db': 1, 'F#': 1, 'B': 1, 'E': 0, 'A': 0, 'D': 0, 'G': 0}
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
		#self.qualities = {'min7': 1, '7': 1, 'Maj7': 1}
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

		self.duration = 5 # s
		self.durationMin = 1 # s
		self.durationMax = 10 # s
		self.elapsedTime = 0 # ms
		self.refreshPeriod = 500 # ms

		# Do not display chord/scale score
# 		self.displayScore = False
		self.displayScore = True
		# Resolution for the score images
		self.scoreResolution = 150
		
		# Default window size
		self.windowSizeX = 500
		self.windowSizeY = 400
		
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
		
		# Path to file where the settings are saved		
		home = expanduser("~")
		self.directory = os.path.join(home, ".chord_training")
		# Create directory in case it doesn't exist
		if not os.path.isdir(self.directory):
			os.makedirs(self.directory)
		self.savefile = os.path.join(self.directory, "settings")	

		# Attempt to read other settings from the savefile, in case it exists
		self.LoadSettings()
		
		self.InitUI()

		self.Centre()
		self.Show(True)
		
	def SaveSettings(self, event = None):
		
		f = open(self.savefile, "w")
		
		f.write("#Chord Training settings\n")
		f.write("Tones:\n")
		for tone in self.pitches.keys():
			f.write("\t%s\t%s\n" %(tone, self.pitches[tone]))
		f.write("Qualities:\n")
		for quality in self.qualities.keys():
			f.write("\t%s\t%s\n" %(quality, self.qualities[quality]))
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
        f.write("SingleThread:\n")
        f.write("\t%b\n" % self.singleThread)
        		
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
						state = items[1] == 'True' or items[1] == 'true' or items[1] == 'TRUE'
						self.pitches[tone] = state
					elif context == "Qualities":
						quality = items[0]
						state = items[1] == 'True' or items[1] == 'true' or items[1] == 'TRUE'
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
			self.duration = int((self.durationMax - self.durationMin)/2 + 1)
			
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
			
	def GenerateImage(self, chord):
		basisHeader='''
#(set-default-paper-size "a4")

\\version "2.16.2"

\\include "english.ly"
'''
		basisUpperBeginning='''
upper = \\relative c' {
  \\clef treble
  \\key c \\major
  %\\time 4/4
'''
		basisUpperContentChord='''  
  r1
  r
  <chordForm1>1
  <chordForm2>1 
'''
		basisContentII_V_I='''  
  <IIchordForm1>2
  <IIchordForm2>2 
  <VchordForm1>2
  <VchordForm2>2
  <IchordForm1>2
  <IchordForm2>2
'''
		basisContentV_I='''  
  <VchordForm1>2
  <VchordForm2>2
  <IchordForm1>2
  <IchordForm2>2
'''
		basisUpperEnd='''
}
'''
		basisLowerBeginning='''
lower = \\relative c {
  \\clef bass
  \\key c \\major
  %\\time 4/4
'''
		basisLowerContentChord='''  
  <chordForm1>1
  <chordForm2>1 
  r1
  r
'''
		basisLowerEnd='''
}
'''
		basisFooter='''
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
		if self.modes['Chord']:
			lyfile = "chord_" + chord.GetLyPitch() + "_" + chord.GetQuality() + "_res" + str(self.scoreResolution) + ".ly"
			content = basisHeader + \
			basisUpperBeginning + \
			basisUpperContentChord + \
			basisUpperEnd + \
			basisLowerBeginning + \
			basisLowerContentChord + \
			basisLowerEnd + \
			basisFooter
		elif self.modes['II-V-I']:
			lyfile = "prog_II-V-I_" + chord.GetLyPitch() + "_res" + str(self.scoreResolution) + ".ly"
			content = basisHeader + \
			basisUpperBeginning + \
			basisContentII_V_I + \
			basisUpperEnd + \
			basisLowerBeginning + \
			basisContentII_V_I + \
			basisLowerEnd + \
			basisFooter
		elif self.modes['V-I']:
			lyfile = "prog_V-I_" + chord.GetLyPitch() + "_res" + str(self.scoreResolution) + ".ly"
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
				
		if self.modes['Chord']:
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
			else:
				# TODO: Other qualities not yet implemented...
				content = re.sub(r"chordForm1", r"c e g", content)
				content = re.sub(r"chordForm2", r"c e g", content)
				scalePitch = 'C'
		elif self.modes['II-V-I']:
			content = re.sub(r"IIchordForm1", r"f a c e", content)
			content = re.sub(r"IIchordForm2", r"c e f a", content)
			content = re.sub(r"VchordForm1", r"f a b e", content)
			content = re.sub(r"VchordForm2", r"b, e f a", content)
			content = re.sub(r"IchordForm1", r"e g a d", content)
			content = re.sub(r"IchordForm2", r"b c e g", content)
		elif self.modes['V-I']:
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

		try:
			catOutputFile = os.path.join(self.directory, "cat_outputFile")
			f = open(catOutputFile,"w")
	
			rc = call(["cat", lyfile], stdout=f)
			f.close()
		
			print "rc = %s" % rc
			# The lilypond call apparently won't work properly without an explicit stdout redirection...
			lilypondOutputFile = os.path.join(self.directory, "lilypond_outputFile")
			f = open(lilypondOutputFile,"w")			
			proc = Popen(["lilypond", "--png", "-dresolution=" + str(self.scoreResolution), "-dpreview", lyfile], stdout=f, cwd=self.directory)
			# Do not continue after starting the lilypond process
            # (useful on slower machines, e.g. raspberryPi 
            if self.singleThread:
                proc.wait()
            f.close()
			print "rc = %s" % rc
		except:
			print "Call to lilypond failed."
		
	def OnTimer(self, whatever):
		self.elapsedTime += self.refreshPeriod
		if self.elapsedTime < self.duration*1000:
			return
		self.elapsedTime = 0
		if self.pause:
			return
		self.GenerateChord()
		self.chordDisplay.SetLabel(self.chord.Print())

		if self.chord.GetPitch() == "-":
			return
		if self.displayScore:
			if self.modes['Chord']:
				imageFile = "chord_" + self.chord.GetLyPitch() + "_" + self.chord.GetQuality() + "_res" + str(self.scoreResolution) + ".png"
			elif self.modes['II-V-I']:
				imageFile = "prog_II-V-I_" + self.chord.GetLyPitch() + "_res" + str(self.scoreResolution) + ".png"
			elif self.modes['V-I']:
				imageFile = "prog_V-I_" + self.chord.GetLyPitch() + "_res" + str(self.scoreResolution) + ".png"
			else:
				# Unsupported mode
				raise
			imageFile = os.path.join(self.directory, imageFile)
			try:
				with open(imageFile): pass
				png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
			except IOError:
				png = wx.EmptyImage(5, 5).ConvertToBitmap()
				self.GenerateImage(self.chord)
			self.chordImage.SetBitmap(png)
			
		# Update the font size in case it has been modified
		if self.fontSize != self.fontSizeOld:
			self.font = wx.Font(self.fontSize, wx.SWISS, wx.NORMAL, wx.NORMAL)
			self.chordDisplay.SetFont(self.font)
			self.fontSizeOld = self.fontSize
			
		# Reset the sizer's size (so that the text window has the right size)		
		self.panel.Fit()
# 		self.upperPanel.FitInside()
		
	def InitUI(self):
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

# 		fileMenu.AppendSeparator()
# 		imp = wx.Menu()
# 		imp.Append(wx.ID_ANY, 'Import newsfeed list...')
# 		imp.Append(wx.ID_ANY, 'Import bookmarks...')
# 		imp.Append(wx.ID_ANY, 'Import mail...')
# 
# 		fileMenu.AppendMenu(wx.ID_ANY, 'I&mport', imp)

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
		tonesMenu = wx.Menu()
		self.tonesMenuId = {}
		self.tonesMenuIdRev = {}
		for tone in self.pitches.keys():
			self.tonesMenuId[tone] = wx.NewId()
			self.tonesMenuIdRev[self.tonesMenuId[tone]] = tone
			tonesMenu.Append(self.tonesMenuId[tone], tone, "", wx.ITEM_CHECK)
			tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
			self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesMenuId[tone])
		menubar.Append(tonesMenu, '&Tones')

		# Menu: QUALITIES
		qualitiesMenu = wx.Menu()
		self.qualitiesMenuId = {}
		self.qualitiesMenuIdRev = {}
		for quality in self.qualities.keys():
			self.qualitiesMenuId[quality] = wx.NewId()
			self.qualitiesMenuIdRev[self.qualitiesMenuId[quality]] = quality
			qualitiesMenu.Append(self.qualitiesMenuId[quality], quality, "", wx.ITEM_CHECK)
			qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
			self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesMenuId[quality])
		menubar.Append(qualitiesMenu, '&Qualities')

		# Menu: DURATION
		durationMenu = wx.Menu()
		self.durationMenuId = {}
		self.durationMenuIdRev = {}
		self.duration = int(self.duration)
		if self.duration < self.durationMin or self.duration > self.durationMax:
			self.duration = int(0.5*(self.durationMax - self.durationMin + 1))
		for duration in range(self.durationMin, self.durationMax + 1):
			self.durationMenuId[duration] = wx.NewId()
			self.durationMenuIdRev[self.durationMenuId[duration]] = duration
			durationMenu.Append(self.durationMenuId[duration], "%d" % duration, "", wx.ITEM_RADIO)
			if duration == self.duration:
				durationMenu.Check(self.durationMenuId[duration], True)
			self.Bind(wx.EVT_MENU, self.MenuSetDuration, id=self.durationMenuId[duration])

		menubar.Append(durationMenu, '&Duration')

		# Menu: VIEW
		viewMenu = wx.Menu()
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

		viewMenu.AppendMenu(wx.ID_ANY, '&Font size', fontSizeMenu)

		menubar.Append(viewMenu, '&View')

		self.SetMenuBar(menubar)

		self.SetSize((self.windowSizeX, self.windowSizeY))
		self.SetTitle('Chord training')

		self.chord = Chord(self)
		self.panel = wx.Panel(self, -1)

		#self.panel.SetBackgroundColour('#4f5049')
		self.panel.SetBackgroundColour('WHITE')
		self.vbox = wx.BoxSizer(wx.VERTICAL)

		self.upperPanel = wx.Panel(self.panel)
		#self.upperPanel.SetBackgroundColour('#ededab')
 		self.upperPanel.SetBackgroundColour('WHITE')
 		
		self.vbox.Add(self.upperPanel, 0, wx.EXPAND | wx.ALL, 20)
 		
		lowerPanel = wx.Panel(self.panel)
		#lowerPanel.SetBackgroundColour('#ededed')
 		lowerPanel.SetBackgroundColour('WHITE')
 		
		self.vbox.Add(lowerPanel, 1, wx.EXPAND | wx.ALL, 20)
		self.panel.SetSizer(self.vbox)
		
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
		
		#self.chordDisplay = wx.StaticText(self.panel, -1, self.chord.Print(), (45, 25), style=wx.ALIGN_LEFT)
		self.chordDisplay = wx.StaticText(self.upperPanel, -1, self.chord.Print(), (30, 25), style=wx.ALIGN_LEFT)
		self.font = wx.Font(self.fontSize, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.chordDisplay.SetFont(self.font)

		if self.displayScore:
			#imageFile = "chord_C.png"
			#png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
			png = wx.EmptyImage(5, 5).ConvertToBitmap()
			#self.chordImage = wx.StaticBitmap(self.panel, -1, png, (0, 100), (png.GetWidth(), png.GetHeight()))
			self.chordImage = wx.StaticBitmap(lowerPanel, -1, png, (0, 0), (png.GetWidth(), png.GetHeight()))

		TIMER_ID = 100  # pick a number
		self.timer = wx.Timer(self.panel, TIMER_ID)  # message will be sent to the self.panel
		self.timer.Start(self.refreshPeriod)  # milliseconds
		wx.EVT_TIMER(self.panel, TIMER_ID, self.OnTimer)  # call the OnTimer function

		# Set pause to off
		self.pause = False
		
		# Quit upon pressing ESC
 		self.panel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		lowerPanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.upperPanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

	def MenuSetTones(self, evt):
		#tone = self.tonesMenuIdRev[evt]
		#self.pitches[tone] = abs(self.pitches[tone] - 1)
		tone = self.tonesMenuIdRev[evt.GetId()]
		#cb = evt.GetEventObject()
		#print "Event: "
		#print cb
		#print evt.IsChecked()
		#print evt.GetId()
		#print tone
		self.pitches[tone] = evt.IsChecked()
		#print "pitches: " + self.pitches

	def MenuSetQualities(self, evt):
		quality = self.qualitiesMenuIdRev[evt.GetId()]
		self.qualities[quality] = evt.IsChecked()

	def MenuSetMode(self, evt):
		mode = self.modeMenuIdRev[evt.GetId()]
		for modeLoop in self.modes.keys():
			if modeLoop == mode:
				self.modes[modeLoop] = True
			else:
				self.modes[modeLoop] = False

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

	def OnQuit(self, e):
		self.SaveSettings()
		self.Close()

	def OnKeyDown(self, e):
		key = e.GetKeyCode()
        
		if key == wx.WXK_ESCAPE:
			self.OnQuit(e)
		elif key == wx.WXK_SPACE:
			self.pause = not self.pause
			pauseLabel = " (Paused)"
			label = self.chordDisplay.GetLabel()
			if self.pause:
				self.chordDisplayLabelOrig = label
				label += pauseLabel
			else:
				#label = re.sub(r"%s" % pauseLabel, r"", label)
				label = self.chordDisplayLabelOrig
			self.chordDisplay.SetLabel(label)

	def GenerateChord(self):
		checkPitch = False
		checkQuality = False
		for pitch in self.pitches.keys():
			if self.pitches[pitch] is True:
				checkPitch = True
				break
		for quality in self.qualities.keys():
			if self.qualities[quality] is True:
				checkQuality = True
				break
		if checkPitch is False or checkQuality is False:
			self.chord.SetPitch("-")
			self.chord.SetQuality("---")
			return

		chordOld = self.chord.Print()
		while (self.chord.Print() == chordOld):
			pitch = random.choice(self.pitches.keys())
			while (self.pitches[pitch] is not True):
				pitch = random.choice(self.pitches.keys())
			self.chord.SetPitch(pitch)
			
			# Only select a quality for chord mode 
			# (qualities for II-V-I modes are obvious)
			if (self.modes["Chord"]):
				quality = random.choice(self.qualities.keys())
				while (self.qualities[quality] is not True):
					quality = random.choice(self.qualities.keys())
				self.chord.SetQuality(quality)
			else:
				self.chord.SetQuality("---")


def main():
	mw = wx.App()
	ChordTraining(None)
	mw.MainLoop()    


if __name__ == '__main__':
	main()
