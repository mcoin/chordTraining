import re

class Settings():
    def __init__(self, chordTraining):
        self.chordTraining = chordTraining

    def SaveSettings(self, event = None, savefile = None):
        # Use the default (autosave) file if none explicitly given
        if (savefile is None):
            savefile = self.chordTraining.savefile
        
        f = open(savefile, "w")
        
        f.write("#Chord Training settings\n")
        f.write("Tones:\n")
        for tone in self.chordTraining.pitches.keys():
            f.write("\t%s\t%s\n" % (tone, self.chordTraining.pitches[tone]))
        f.write("Qualities:\n")
        for quality in self.chordTraining.qualities.keys():
            f.write("\t%s\t%s\n" % (quality, self.chordTraining.qualities[quality]))
        f.write("Mode:\n")
        for mode in self.chordTraining.modes.keys():
            if self.chordTraining.modes[mode]:
                f.write("\t%s\n" % mode)
        f.write("Duration:\n")
        f.write("%d\n" % self.chordTraining.duration)
        f.write("WindowSize:\n")
        size = self.chordTraining.GetSize()
        f.write("\t%d\t%d\n" % (size.x, size.y))
        f.write("FontSize:\n")
        f.write("\t%d\n" % self.chordTraining.fontSize)
        f.write("ScoreResolution:\n")
        f.write("\t%d\n" % self.chordTraining.scoreRes)
        f.write("SingleThread:\n")
        f.write("\t%r\n" % self.chordTraining.singleThread)
        f.write("DisplayScore:\n")
        f.write("\t%s\n" % self.chordTraining.displayScore)
        f.write("DisplayScale:\n")
        f.write("\t%s\n" % self.chordTraining.displayScale)
        f.write("StayOn:\n")
        f.write("\t%s\n" % self.chordTraining.moveMouse)
                                
        f.close()


    def LoadSettings(self, event = None, savefile = None):
        try:
            context = None
            # Use the default (autosave) file if none explicitly given
            if (savefile is None):
                savefile = self.chordTraining.savefile
            
            with open(savefile) as f:
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
                        if tone in self.chordTraining.pitches.keys():
                            self.chordTraining.pitches[tone] = state
                    elif context == "Qualities":
                        quality = items[0]
                        try:
                            state = items[1].lower() == 'true'
                        except:
                            state = False
                        if quality in self.chordTraining.qualities.keys():
                            self.chordTraining.qualities[quality] = state              
                    elif context == "Mode":
                        mode = items[0]
                        for modeTest in self.chordTraining.modes.keys():
                            if mode == modeTest:
                                self.chordTraining.modes[modeTest] = True
                            else:
                                self.chordTraining.modes[modeTest] = False
                    elif context == "Duration":
                        duration = int(items[0])
                        self.chordTraining.duration = duration
                    elif context == "WindowSize":
                        self.chordTraining.windowSizeX = int(items[0])
                        self.chordTraining.windowSizeY = int(items[1])
                    elif context == "FontSize":
                        self.chordTraining.fontSize = int(items[0])
                        for fontSize in self.chordTraining.fontSizes.keys():
                            if int(fontSize) == self.chordTraining.fontSize:
                                self.chordTraining.fontSizes[fontSize] = True
                            else:
                                self.chordTraining.fontSizes[fontSize] = False
                    elif context == "ScoreResolution":
                        self.chordTraining.scoreRes = int(items[0])
                        for scoreRes in self.chordTraining.scoreRess.keys():
                            if int(scoreRes) == self.chordTraining.scoreRes:
                                self.chordTraining.scoreRess[scoreRes] = True
                            else:
                                self.chordTraining.scoreRess[scoreRes] = False
                    elif context == "SingleThread":
                        if items[0].lower() == 'false':
                            self.chordTraining.singleThread = False
                        else:
                            self.chordTraining.singleThread = True
                    elif context == "DisplayScore":
                        if items[0].lower() == 'false':
                            self.chordTraining.displayScore = False
                        else:
                            self.chordTraining.displayScore = True
                    elif context == "DisplayScale":
                        if items[0].lower() == 'false':
                            self.chordTraining.displayScale = False
                        else:
                            self.chordTraining.displayScale = True
                    elif context == "StayOn":
                        if items[0].lower() == 'false':
                            self.chordTraining.moveMouse = False
                        else:
                            self.chordTraining.moveMouse = True                                
        except:
            pass

        # Check that the data read makes sense
        # There should be only one mode selected
        nbModes = 0
        for mode in self.chordTraining.modes.keys():
            if self.chordTraining.modes[mode]:
                nbModes += 1
        if nbModes != 1:
            first = True
            for mode in self.chordTraining.modes:
                if first:
                    self.chordTraining.modes[mode] = True
                else:
                    self.chordTraining.modes[mode] = False
                first = False
                
        # The duration should be an integer value between durationMin and durationMax
        if (self.chordTraining.duration < self.chordTraining.durationMin or self.chordTraining.duration > self.chordTraining.durationMax):
            self.chordTraining.duration = int((self.chordTraining.durationMax - self.chordTraining.durationMin) / 2 + 1)
            
        # Check that the given font size is legal
        nbFontSizes = 0
        for fontSize in self.chordTraining.fontSizes.keys():
            if self.chordTraining.fontSizes[fontSize]:
                nbFontSizes += 1
        if nbFontSizes != 1:
            first = True
            for fontSize in self.chordTraining.fontSizes.keys():
                if first:
                    self.chordTraining.fontSizes[fontSize] = True
                    self.chordTraining.fontSize = int(fontSize)
                    first = False
                else:
                    self.chordTraining.fontSizes[fontSize] = False

        # Check that the given score resolution is legal
        nbScoreRess = 0
        for scoreRes in self.chordTraining.scoreRess.keys():
            if self.chordTraining.scoreRess[scoreRes]:
                nbScoreRess += 1
        if nbScoreRess != 1:
            first = True
            for scoreRes in self.chordTraining.scoreRess.keys():
                if first:
                    self.chordTraining.scoreRess[scoreRes] = True
                    self.chordTraining.scoreRes = int(scoreRes)
                    first = False
                else:
                    self.chordTraining.scoreRess[scoreRes] = False
                    
        # Synchronize the menus to the data we just read
        for tone in self.chordTraining.pitches.keys():
            self.chordTraining.tonesMenu.Check(self.chordTraining.tonesMenuId[tone], self.chordTraining.pitches[tone])

        for mode in self.chordTraining.modes.keys():
            self.chordTraining.modeMenu.Check(self.chordTraining.modeMenuId[mode], self.chordTraining.modes[mode])
            
        for quality in self.chordTraining.qualities.keys():
            self.chordTraining.qualitiesMenu.Check(self.chordTraining.qualitiesMenuId[quality], self.chordTraining.qualities[quality])

        try:
            self.chordTraining.durationMenu.Check(self.chordTraining.durationMenuId[self.chordTraining.duration], True)
        except:
            pass
                
        try:
            self.chordTraining.fontSizeMenu.Check(self.chordTraining.fontSizeMenuId[str(self.chordTraining.fontSize)], True)
        except:
            pass

        try:
            self.chordTraining.scoreResMenu.Check(self.chordTraining.scoreResMenuId[str(self.chordTraining.scoreRes)], True)
        except:
            pass
        
        self.chordTraining.settingsMenu.Check(self.chordTraining.singleThreadId, self.chordTraining.singleThread)
        self.chordTraining.settingsMenu.Check(self.chordTraining.displayScoreId, self.chordTraining.displayScore)
        self.chordTraining.settingsMenu.Check(self.chordTraining.displayScaleId, self.chordTraining.displayScale)
        self.chordTraining.settingsMenu.Check(self.chordTraining.stayOnId, self.chordTraining.moveMouse)