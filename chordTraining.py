#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Random chord generator to train with jazz voicings
TV 2013-07-28
'''

import wx
import collections
import os

from stayon import StayOn
from score import Score
from settings import Settings
from chord import Chord, ChordStack, Conversion

# Exception thrown when no image may be determined for the score of a chord/progression
class NoImage(Exception):
	def __init__(self):
	    pass

class ChordTraining(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(ChordTraining, self).__init__(*args, **kwargs) 

		# Default settings (overridden by settings from file ~/.chord_training/settings, if it exists)
		self.pitches = collections.OrderedDict()
		self.pitches['C'] = True
		self.pitches['F'] = True
		self.pitches['Bb'] = True
		self.pitches['Eb'] = True
		self.pitches['Ab'] = True
		self.pitches['Db'] = True
		self.pitches['F#'] = True
		self.pitches['B'] = True
		self.pitches['E'] = True
		self.pitches['A'] = True
		self.pitches['D'] = True
		self.pitches['G'] = True
		
		self.qualities = collections.OrderedDict()
		self.qualities['min7'] = True
		self.qualities['7'] = True
		self.qualities['Maj7'] = True
		self.qualities['minMaj7'] = False
		self.qualities['alt'] = False
		self.qualities['min7b5'] = False
		self.qualities['dim7'] = False
		self.qualities['7b9'] = False
		#self.qualities['min'] = False
		#self.qualities['Maj'] = False
		#self.qualities['7sus4'] = False
		#self.qualities['aug'] = False
		
		self.modes = collections.OrderedDict()
		self.modes['Chord'] = True
		self.modes['II-V-I'] = False
		self.modes['II-V'] = False
		self.modes['V-I'] = False

		self.conv = Conversion()
		
		self.durationMin = 1  # s
		self.durationMax = 10  # s
		self.duration = 5  # s
		self.elapsedTime = 0  # ms
		self.refreshPeriod = 50  # ms
		# Indicator for manual manipulation of the chord stack
		self.manualChange = False 
		
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

		# Path to file where the settings are saved		
		home = os.path.expanduser("~")
		self.directory = os.path.join(home, ".chord_training")
		# Create directory in case it doesn't exist
		if not os.path.isdir(self.directory):
			os.makedirs(self.directory)
		self.savefile = os.path.join(self.directory, "settings")	
		self.settings = Settings(self)

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

		# Make sure the subdirectory exists
		for scoreRes in self.scoreRess.keys():
			targetDir = os.path.join(self.directory, "res" + scoreRes)
			if not os.path.isdir(targetDir):
				os.mkdir(targetDir)	
		
		# Framework creating the needed score images for chord voicings and corresponding scales
		self.score = Score(self.directory)
		
		# Trick the system to disable screen savers during training
		self.moveMouse = True
		
		# Prevent the screensaver from starting
		self.stayOn = StayOn()
		
		# Set pause to off
		self.pause = False  
		
		# Override setting in case the feature is unavailable
		if not self.stayOn.isEnabled():
			self.moveMouse = False
		
		# Set up the menus
		self.InitMenus()
		
		# Attempt to read other settings from the savefile, in case it exists
		self.settings.LoadSettings()
		
		self.SetChord()

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

	def SaveFile(self, event):
		saveFileDialog = wx.FileDialog(self, "Save As", self.directory, self.savefile, "*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		saveFileDialog.ShowModal()
		savefile = saveFileDialog.GetPath()
		
		self.settings.SaveSettings(event, savefile)
		
		saveFileDialog.Destroy()
		
	def LoadFile(self, event):
		openFileDialog = wx.FileDialog(self, "Open", self.directory, self.savefile, "*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		openFileDialog.ShowModal()
		savefile = openFileDialog.GetPath()
		
		self.settings.LoadSettings(event, savefile)

		# Mark the current parameters as new, so as to renew the chord stack 
		self.changedParameters = True
		
		openFileDialog.Destroy()

	def PickLilypond(self, event):		
		lilypondDir = os.path.dirname(self.score.lilypond) 
		lilypondProg = self.score.lilypond
		openFileDialog = wx.FileDialog(self, "Select the location of the lilypond program", \
									lilypondDir, lilypondProg, "*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		openFileDialog.ShowModal()
		self.score.lilypond = openFileDialog.GetPath()

		# Reset the path in the menu
		self.lilypondPathMenu.SetLabel(self.lilypondPathId, self.score.lilypond)
		
		# Update the availability of the option to generate the score images in the menu
		generateScoreIsPossible = self.score.IsLilypondAvailable() and self.score.AreImageToolsAvailable()
 		self.settingsMenu.Enable(self.generateScoresId, generateScoreIsPossible)
		
		openFileDialog.Destroy()

	def resizeImgCanvas(self, imgFile, canvasWidth, canvasHeight):
		from PIL import Image
		from math import floor
		
		imgOrig = Image.open(imgFile)
		imgWidth, imgHeight = imgOrig.size
	
		# Center the image
		x1 = int(floor((canvasWidth - imgWidth) / 2))
		y1 = int(floor((canvasHeight - imgHeight) / 2))
	
		mode = imgOrig.mode
		if len(mode) == 1:  # L, 1
			bckgrnd = (255)
		elif len(mode) == 3:  # RGB
			bckgrnd = (255, 255, 255)
		elif len(mode) == 4:  # RGBA, CMYK
			bckgrnd = (255, 255, 255, 255)
	
		imgNew = Image.new(mode, (canvasWidth, canvasHeight), bckgrnd)
		imgNew.paste(imgOrig, (x1, y1, x1 + imgWidth, y1 + imgHeight))
		imgNew.save(imgFile)
		
	def GenerateScores(self, event):
		# Generate images for all possible chords and scales in all available resolutions
		from PIL import Image
		
		for scoreRes in self.scoreRess:
			# Scores
			maxWidth = 0
			maxHeight = 0
			imgList = []
			for pitch in self.pitches:
				for quality in self.qualities:
					chord = Chord(pitch, quality, "Chord")
					self.score.GenerateImage(chord, scoreRes, True, False)
					imgFile = chord.GetImgName(scoreRes)
					imgFile = os.path.join(self.directory, imgFile)
 					
					imgList.append(imgFile)
					img = Image.open(imgFile)
					width, height = img.size
					maxWidth = max(maxWidth, width)
					maxHeight = max(maxHeight, height)
 					
			for imgFile in imgList:
				self.resizeImgCanvas(imgFile, maxWidth, maxHeight)
			
			# Scales
			maxWidth = 0
			maxHeight = 0
			imgList = []
			# Qualities leading to the generation of all possible scales (Major, Minor, Diminished)
			qualities = ["Maj7", "minMaj7", "dim7"] 
			for pitch in self.pitches:
				for quality in qualities:
					# For the diminished scale, only a subset of all possibilities is needed
					if quality == "dim7" and self.pitches.keys().index(pitch) != self.pitches.keys().index(pitch) % 3:
						continue
					chord = Chord(pitch, quality, "Chord")
					self.score.GenerateScaleImage(chord, scoreRes, True, False)
					imgFile = chord.GetScaleImgName(scoreRes)
					imgFile = os.path.join(self.directory, imgFile)
					
					imgList.append(imgFile)
					img = Image.open(imgFile)
					width, height = img.size
					maxWidth = max(maxWidth, width)
					maxHeight = max(maxHeight, height)
					
			for imgFile in imgList:
				self.resizeImgCanvas(imgFile, maxWidth, maxHeight)
					
			
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
				self.score.GenerateImage(currChord, self.scoreRes, self.singleThread)
			elif imageMode == "Scale" and currChord.GetPitch() != "-" and self.displayScale:
				self.score.GenerateScaleImage(currChord, self.scoreRes, self.singleThread)
				
		if imageMode == "Chord":		
			self.chordImage.SetBitmap(png)
		elif imageMode == "Scale":		
			self.scaleImage.SetBitmap(png)
					
	def RefreshChord(self):
		# Renew upcoming chords in the stack upon changes in the parameters
		if self.changedParameters:
			self.chordStack.RecreateNext(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
			self.changedParameters = False
			# Avoid skipping the next chord
			self.chordStack.Prev()

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
		
		# Explicitly switch to the next chord in the stack in case we have 
		# manually changed the current chord
		if self.manualChange:
			self.manualChange = False
			self.chordStack.Next()

		self.RefreshChord()

 		# Append a new chord to the stack		
 		self.chordStack.UpdateStack(self.AvailablePitches(), self.AvailableQualities(), self.CurrentMode())
		
	def getSmallerFontsize(self, fontsize):
		return fontsize/2
	
	def InitMenus(self):
		# Menus
		menubar = wx.MenuBar()

		# Menu: FILE
		fileMenu = wx.Menu()

		wx.ID_PAUSE = wx.NewId()
		fileMenu.Append(wx.ID_PAUSE, '&Pause')
		wx.ID_REDRAW = wx.NewId()
		fileMenu.Append(wx.ID_REDRAW, '&Redraw layout')
		fileMenu.Append(wx.ID_OPEN, '&Open')
		fileMenu.Append(wx.ID_SAVE, '&Save')
		fileMenu.Append(wx.ID_SAVEAS, 'Save &as...')
			
		self.Bind(wx.EVT_MENU, self.TogglePause, id=wx.ID_PAUSE)
		self.Bind(wx.EVT_MENU, self.FlagLayoutRedraw, id=wx.ID_REDRAW)
		self.Bind(wx.EVT_MENU, self.LoadFile, id=wx.ID_OPEN)
		self.Bind(wx.EVT_MENU, self.settings.SaveSettings, id=wx.ID_SAVE)
		self.Bind(wx.EVT_MENU, self.SaveFile, id=wx.ID_SAVEAS)

# 		fileMenu.Append(wx.ID_EXIT, '&Quit')
# 		self.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)

		qmi = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit\tCtrl+W')
		fileMenu.AppendItem(qmi)

		self.Bind(wx.EVT_MENU, self.OnQuit, qmi)

		menubar.Append(fileMenu, '&File')

		# Menu: MODE
		self.modeMenu = wx.Menu()
		self.modeMenuId = {}
		self.modeMenuIdRev = {}
		for mode in self.modes.keys():
			self.modeMenuId[mode] = wx.NewId()
			self.modeMenuIdRev[self.modeMenuId[mode]] = mode
			self.modeMenu.Append(self.modeMenuId[mode], mode, "", wx.ITEM_RADIO)
			self.modeMenu.Check(self.modeMenuId[mode], self.modes[mode])
			self.Bind(wx.EVT_MENU, self.MenuSetMode, id=self.modeMenuId[mode])
		menubar.Append(self.modeMenu, '&Mode')

		# Menu: TONES
		self.tonesMenu = wx.Menu()
		self.tonesMenuId = {}
		self.tonesMenuIdRev = {}

		self.tonesFuncId = {\
						"all" : wx.NewId(),\
						"none" : wx.NewId(),\
						"invert" : wx.NewId(),\
						"1-3" : wx.NewId(),\
						"4-6" : wx.NewId(),\
						"7-9" : wx.NewId(),\
						"10-12" : wx.NewId(),\
						"1-4" : wx.NewId(),\
						"5-8" : wx.NewId(),\
						"9-12" : wx.NewId(),\
						"1-6" : wx.NewId(),\
						"7-12" : wx.NewId()\
						}

		self.tonesMenu.Append(self.tonesFuncId["all"], "All")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["all"])
		self.tonesMenu.Append(self.tonesFuncId["none"], "None")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["none"])
		self.tonesMenu.Append(self.tonesFuncId["invert"], "Invert")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["invert"])
					
		self.toneGroupsMenu = wx.Menu()

		self.tonesMenu.AppendMenu(wx.ID_ANY, '&Groups', self.toneGroupsMenu)

		self.tonesMenu.AppendSeparator()
		
		for tone in self.pitches.keys():
			self.tonesMenuId[tone] = wx.NewId()
			self.tonesMenuIdRev[self.tonesMenuId[tone]] = tone
			self.tonesMenu.Append(self.tonesMenuId[tone], self.conv.GetPitchName(tone), "", wx.ITEM_CHECK)
			self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
			self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesMenuId[tone])
			
		self.toneGroupsMenu.Append(self.tonesFuncId["1-3"], "1-3")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["1-3"])
		self.toneGroupsMenu.Append(self.tonesFuncId["4-6"], "4-6")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["4-6"])
		self.toneGroupsMenu.Append(self.tonesFuncId["7-9"], "7-9")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["7-9"])
		self.toneGroupsMenu.Append(self.tonesFuncId["10-12"], "10-12")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["10-12"])
					
		self.toneGroupsMenu.AppendSeparator()

		self.toneGroupsMenu.Append(self.tonesFuncId["1-4"], "1-4")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["1-4"])
		self.toneGroupsMenu.Append(self.tonesFuncId["5-8"], "5-8")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["5-8"])
		self.toneGroupsMenu.Append(self.tonesFuncId["9-12"], "9-12")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["9-12"])

		self.toneGroupsMenu.AppendSeparator()

		self.toneGroupsMenu.Append(self.tonesFuncId["1-6"], "1-6")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["1-6"])
		self.toneGroupsMenu.Append(self.tonesFuncId["7-12"], "7-12")
		self.Bind(wx.EVT_MENU, self.MenuSetTones, id=self.tonesFuncId["7-12"])

		menubar.Append(self.tonesMenu, '&Tones')

		# Menu: QUALITIES
		self.qualitiesMenu = wx.Menu()
		self.qualitiesMenuId = {}
		self.qualitiesMenuIdRev = {}

		self.qualitiesFuncId = {\
						"maj" : wx.NewId(),\
						"min" : wx.NewId(),\
						"dim" : wx.NewId(),\
						"all" : wx.NewId(),\
						"none" : wx.NewId()\
						}

		self.qualitiesMenu.Append(self.qualitiesFuncId["all"], "All")
		self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesFuncId["all"])
		self.qualitiesMenu.Append(self.qualitiesFuncId["none"], "None")
		self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesFuncId["none"])

		self.qualitiesMenu.AppendSeparator()

		self.qualitiesMenu.Append(self.qualitiesFuncId["maj"], "Major")
		self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesFuncId["maj"])
		self.qualitiesMenu.Append(self.qualitiesFuncId["min"], "Minor")
		self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesFuncId["min"])
		self.qualitiesMenu.Append(self.qualitiesFuncId["dim"], "Diminished")
		self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesFuncId["dim"])
					
		self.qualitiesMenu.AppendSeparator()

		for quality in self.qualities.keys():
			self.qualitiesMenuId[quality] = wx.NewId()
			self.qualitiesMenuIdRev[self.qualitiesMenuId[quality]] = quality
			self.qualitiesMenu.Append(self.qualitiesMenuId[quality], self.conv.GetQualityName(quality), "", wx.ITEM_CHECK)
			self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
			self.Bind(wx.EVT_MENU, self.MenuSetQualities, id=self.qualitiesMenuId[quality])
			self.qualitiesMenu.Enable(self.qualitiesMenuId[quality], self.modes['Chord'])
				
		
		menubar.Append(self.qualitiesMenu, '&Qualities')
			
		# Menu: DURATION
		self.durationMenu = wx.Menu()
		self.durationMenuId = {}
		self.durationMenuIdRev = {}
		self.duration = int(self.duration)
		if self.duration < self.durationMin or self.duration > self.durationMax:
			self.duration = int(0.5 * (self.durationMax - self.durationMin + 1))
		for duration in range(self.durationMin, self.durationMax + 1):
			self.durationMenuId[duration] = wx.NewId()
			self.durationMenuIdRev[self.durationMenuId[duration]] = duration
			self.durationMenu.Append(self.durationMenuId[duration], "%d" % duration, "", wx.ITEM_RADIO)
			if duration == self.duration:
				self.durationMenu.Check(self.durationMenuId[duration], True)
			self.Bind(wx.EVT_MENU, self.MenuSetDuration, id=self.durationMenuId[duration])

		menubar.Append(self.durationMenu, '&Duration')

		# Menu: SETTINGS
		self.settingsMenu = wx.Menu()
		self.fontSizeMenu = wx.Menu()
		self.fontSizeMenuId = {}
		self.fontSizeMenuIdRev = {}
		for fontSize in self.fontSizes.keys():
			self.fontSizeMenuId[fontSize] = wx.NewId()
			self.fontSizeMenuIdRev[self.fontSizeMenuId[fontSize]] = fontSize
			self.fontSizeMenu.Append(self.fontSizeMenuId[fontSize], "%s" % fontSize, "", wx.ITEM_RADIO)
			if int(fontSize) == self.fontSize:
				self.fontSizeMenu.Check(self.fontSizeMenuId[fontSize], True)
			self.Bind(wx.EVT_MENU, self.MenuSetFontSize, id=self.fontSizeMenuId[fontSize])

		self.scoreResMenu = wx.Menu()
		self.scoreResMenuId = {}
		self.scoreResMenuIdRev = {}
		for scoreRes in self.scoreRess.keys():
			self.scoreResMenuId[scoreRes] = wx.NewId()
			self.scoreResMenuIdRev[self.scoreResMenuId[scoreRes]] = scoreRes
			self.scoreResMenu.Append(self.scoreResMenuId[scoreRes], "%s" % scoreRes, "", wx.ITEM_RADIO)
			if int(scoreRes) == self.scoreRes:
				self.scoreResMenu.Check(self.scoreResMenuId[scoreRes], True)
			self.Bind(wx.EVT_MENU, self.MenuSetScoreRes, id=self.scoreResMenuId[scoreRes])

		self.singleThreadId = wx.NewId()
		self.settingsMenu.Append(self.singleThreadId, "Single &thread", "", wx.ITEM_CHECK)
		self.settingsMenu.Check(self.singleThreadId, self.singleThread)
		self.Bind(wx.EVT_MENU, self.MenuSetSingleThread, id=self.singleThreadId)

		self.displayScoreId = wx.NewId()
		self.settingsMenu.Append(self.displayScoreId, "&Display score", "", wx.ITEM_CHECK)
		self.settingsMenu.Check(self.displayScoreId, self.displayScore)
		self.Bind(wx.EVT_MENU, self.MenuSetDisplayScore, id=self.displayScoreId)

		self.displayScaleId = wx.NewId()
		self.settingsMenu.Append(self.displayScaleId, "D&isplay scale", "", wx.ITEM_CHECK)
		self.settingsMenu.Check(self.displayScaleId, self.displayScale)
		self.Bind(wx.EVT_MENU, self.MenuSetDisplayScale, id=self.displayScaleId)

		self.stayOnId = wx.NewId()
		self.settingsMenu.Append(self.stayOnId, "Disable &Screensaver", "", wx.ITEM_CHECK)
		self.settingsMenu.Check(self.stayOnId, self.moveMouse)
		self.Bind(wx.EVT_MENU, self.MenuSetStayOn, id=self.stayOnId)
		self.settingsMenu.Enable(self.stayOnId, self.stayOn.isEnabled())

		self.settingsMenu.AppendSeparator()

		self.settingsMenu.AppendMenu(wx.ID_ANY, '&Font size', self.fontSizeMenu)

		self.settingsMenu.AppendMenu(wx.ID_ANY, '&Score resolution', self.scoreResMenu)

		self.lilypondPathMenu = wx.Menu()
		self.lilypondPathId = wx.NewId()
		pathToLilypond = self.score.lilypond
		self.lilypondPathMenu.Append(self.lilypondPathId, "%s" % pathToLilypond)
		self.lilypondPathMenu.Enable(self.lilypondPathId, False)
		self.lilypondPathMenu.AppendSeparator()
		editLilypondPathId = wx.NewId()
		self.lilypondPathMenu.Append(editLilypondPathId, "&Select...")
		
		self.Bind(wx.EVT_MENU, self.PickLilypond, id=editLilypondPathId)

		self.settingsMenu.AppendMenu(wx.ID_ANY, '&Path to Lilypond', self.lilypondPathMenu)

		self.settingsMenu.AppendSeparator()
		self.generateScoresId = wx.NewId()
		self.settingsMenu.Append(self.generateScoresId, "&Generate Score images")
		generateScoreIsPossible =  self.score.AreImageToolsAvailable() and self.score.IsLilypondAvailable()
 		self.settingsMenu.Enable(self.generateScoresId, generateScoreIsPossible)

		self.Bind(wx.EVT_MENU, self.GenerateScores, id=self.generateScoresId)
		
		menubar.Append(self.settingsMenu, '&Settings')

		self.SetMenuBar(menubar)

	def SetChord(self):
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
		elif evt.GetId() == self.tonesFuncId["1-3"]:
			index = 0
			for tone in self.pitches.keys():
				if index < 3:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["4-6"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 3 and index < 6:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["7-9"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 6 and index < 9:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["10-12"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 9:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["1-4"]:
			index = 0
			for tone in self.pitches.keys():
				if index < 4:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["5-8"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 4 and index < 8:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["9-12"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 8:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["1-6"]:
			index = 0
			for tone in self.pitches.keys():
				if index < 6:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		elif evt.GetId() == self.tonesFuncId["7-12"]:
			index = 0
			for tone in self.pitches.keys():
				if index >= 6:
					self.pitches[tone] = True
				else:
					self.pitches[tone] = False
				self.tonesMenu.Check(self.tonesMenuId[tone], self.pitches[tone])
				index += 1
		else:
			tone = self.tonesMenuIdRev[evt.GetId()]
			self.pitches[tone] = evt.IsChecked()
		# Mark the current parameters as new, so as to renew the chord stack 
		self.changedParameters = True

	def MenuSetQualities(self, evt):
		if evt.GetId() == self.qualitiesFuncId["maj"]:
			for quality in self.qualities.keys():
				if quality == "Maj7" or \
				quality == "7" or \
				quality == "min7":
					self.qualities[quality] = True
				else:
					self.qualities[quality] = False
				self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
		elif evt.GetId() == self.qualitiesFuncId["min"]:
			for quality in self.qualities.keys():
				if quality == "minMaj7" or \
				quality == "alt" or \
				quality == "min7b5":
					self.qualities[quality] = True
				else:
					self.qualities[quality] = False
				self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
		elif evt.GetId() == self.qualitiesFuncId["dim"]:
			for quality in self.qualities.keys():
				if quality == "dim7" or \
				quality == "7b9":
					self.qualities[quality] = True
				else:
					self.qualities[quality] = False
				self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
		elif evt.GetId() == self.qualitiesFuncId["all"]:
			for quality in self.qualities.keys():
				self.qualities[quality] = True
				self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
		elif evt.GetId() == self.qualitiesFuncId["none"]:
			for quality in self.qualities.keys():
				self.qualities[quality] = False
				self.qualitiesMenu.Check(self.qualitiesMenuId[quality], self.qualities[quality])
		else:
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
		
		# Mark the current parameters as new, so as to renew the chord stack 
		self.changedParameters = True		
		
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
		self.settings.SaveSettings()
		self.Close()

	def TogglePause(self, e):
		self.pause = not self.pause
		pauseLabel = "(Paused)"
		if self.pause:
			self.timer.Stop()
			label = pauseLabel
		else:
			self.timer.Start(self.refreshPeriod)  # milliseconds
			label = ""
		self.status.SetLabel(label)

	def FlagLayoutRedraw(self, e):
		self.changedLayout = True

	def NextChord(self, e):
		# Do not explicitly call the function the first time
		if not self.manualChange:
			nextChordExists = True
		else:
			nextChordExists = self.chordStack.Next()
		
		if nextChordExists:
			self.RefreshChord()
		self.manualChange = True
		
	def PrevChord(self, e):
		# Call the function twice the first time
		if not self.manualChange:
			self.chordStack.Prev()
			self.chordStack.Prev()
			prevChordExists = True
		else:
			prevChordExists = self.chordStack.Prev()

		if prevChordExists:
			self.RefreshChord()
		self.manualChange = True

	def OnKeyDown(self, e):
		key = e.GetKeyCode()

		if key == wx.WXK_ESCAPE:
			self.OnQuit(e)
		elif key == wx.WXK_SPACE:
			self.TogglePause(e)
		elif key == wx.WXK_LEFT:
			self.PrevChord(e)
		elif key == wx.WXK_RIGHT:
			self.NextChord(e)
		elif key == wx.WXK_F5:
			self.FlagLayoutRedraw(e)
	
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
