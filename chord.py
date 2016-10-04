import re
import random
import os

class Conversion:
    def __init__(self):
        # Quality names for output in the GUI
        self.qualityNames = {}
        self.qualityNames['min7'] = "-7"
        self.qualityNames['7'] = "7"
        self.qualityNames['Maj7'] = u'\u25B3'
        self.qualityNames['minMaj7'] = u'-\u25B3'
        self.qualityNames['alt'] = "alt"
        self.qualityNames['min7b5'] = u'\u2300' #u'\u00F8'
        self.qualityNames['dim7'] = "dim"
        self.qualityNames['7b9'] = u'7\u266D9'

        # Pitch names for output in the GUI
        self.pitchNames = {}
        self.pitchNames['C'] = "C "
        self.pitchNames['F'] = "F "
        self.pitchNames['Bb'] = u'B\u266D' 
        self.pitchNames['Eb'] = u'E\u266D' 
        self.pitchNames['Ab'] = u'A\u266D' 
        self.pitchNames['Db'] = u'D\u266D' 
        self.pitchNames['F#'] = u'F\u266F' 
        self.pitchNames['B'] = "B "
        self.pitchNames['E'] = "E "
        self.pitchNames['A'] = "A "
        self.pitchNames['D'] = "D "
        self.pitchNames['G'] = "G "

    def GetQualityName(self, quality):
        if quality not in self.qualityNames:
            return quality
        
        return self.qualityNames[quality]

    def GetPitchName(self, pitch):
        if pitch not in self.pitchNames:
            return pitch
        
        return self.pitchNames[pitch]

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
        
        self.conv = Conversion()
        
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
    
    def GetPreviousPitchAlongCircleOfFifths(self):
        index = self.pitches.index(self.pitch)
        prevIndex = index - 1
        
        return self.pitches[prevIndex]
        
    def GetNextPitchAlongCircleOfFifths(self):
        index = self.pitches.index(self.pitch)
        nextIndex = (index + 1) % len(self.pitches)
        
        return self.pitches[nextIndex]
        
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
    
    def GenerateRandom(self, listPitches, listQualities, currentMode, chordToAvoid=None):
        self.SetMode(currentMode)
        
        if len(listPitches) == 0 or len(listQualities) == 0:
            self.SetPitch("-")
            self.SetQuality("-")
            return

        suitableChord = False
        while not suitableChord:
            pitch = random.choice(listPitches)
            self.SetPitch(pitch)
            
            quality = random.choice(listQualities)
            self.SetQuality(quality)
            
            if len(listPitches) * len(listQualities) < 2 or \
            self.GetName() != chordToAvoid:
                suitableChord = True            
            
        self.updateScale = True

    def GetName(self):
        self.name = self.conv.GetPitchName(self.pitch) + self.conv.GetQualityName(self.quality)
            
        return self.name

    def DetermineScale(self):
        if not self.updateScale:
            return
        self.updateScale = False
        
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
        elif self.quality == 'minMaj7' or self.quality == 'alt' or self.quality == 'min7b5':
            if self.quality == 'minMaj7':
                self.scalePitch = self.pitch
                self.scaleKind = "Minor"
            elif self.quality == 'alt':
                indexVpitch = self.pitches.index(self.pitch)
                indexPitch = indexVpitch + 5 
                if indexPitch >= len(self.pitches): 
                    indexPitch -= len(self.pitches)
                self.scalePitch = self.pitches[indexPitch]
                self.scaleKind = "Minor"
            elif self.quality == 'min7b5':
                indexIIpitch = self.pitches.index(self.pitch)
                indexPitch = indexIIpitch + 3
                if indexPitch >= len(self.pitches): 
                    indexPitch -= len(self.pitches)
                self.scalePitch = self.pitches[indexPitch]
                self.scaleKind = "Minor"
        elif (self.quality == 'dim7'):
            index = self.pitches.index(self.pitch) % 3
            self.scalePitch = self.pitches[index]
            self.scaleKind = "Diminished"
        elif (self.quality == '7b9'):
            indexPitch = self.pitches.index(self.pitch) + 2
            if indexPitch >= len(self.pitches): 
                indexPitch -= len(self.pitches)
            indexPitch = indexPitch % 3
            self.scalePitch = self.pitches[indexPitch]
            self.scaleKind = "Diminished"
        else:
            self.scaleKind = "-"
            self.scalePitch = self.pitch if self.pitch is not None else "-"

        if self.scalePitch is None or self.scaleKind is None:
            self.scale = "-"
        else:
            self.scale = self.scalePitch + " " + self.scaleKind
            
    def GetScale(self):
        self.DetermineScale()            
        return self.conv.GetPitchName(self.scalePitch) + " " + self.scaleKind

    def GetBaseFileName(self):
        self.fileName = os.path.join("res%s", "chord_" + self.GetLyPitch() + "_" + self.GetQuality() + "%s")
        
        return self.fileName

    def GetImgName(self, res):
        return self.GetBaseFileName() % (str(res), '.preview.png')
    
    def GetLyName(self, res):
        return self.GetBaseFileName() % (str(res), '.ly')

    def GetBaseScaleFileName(self):
        self.DetermineScale()
        self.scaleFileName = os.path.join("res%s", "scale_" + self.GetLyScalePitch() + "_" + self.GetScaleKind() + "%s")
        
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
        # List of Chord objects
        self.elements = []
        # Dummy Chord object to return when at end of stack
        self.dummy = Chord()
        
    def LookForChordToAvoid(self, indices, convertVtoI=False):
        """ Check whether the same chord has been generated twice in a row already """
        if len(indices) != 2:
            return None
        
        maxIndex = 0
        for index in indices:
            maxIndex = max(maxIndex, abs(index))
            
        if len(self.elements) >= maxIndex:
            prevChord = self.elements[indices[0]].GetName()
            if self.elements[indices[1]].GetName() == prevChord:
                if convertVtoI:
                    # Return the corresponding major chord instead
                    Vchord = self.elements[indices[0]]
                    pitch = self.elements[indices[0]].GetNextPitchAlongCircleOfFifths()
                    IchordName = Vchord.conv.GetPitchName(pitch) + Vchord.conv.GetQualityName("Maj7")
                    return IchordName
                else:
                    return prevChord
            
        return None
        
    def AddElement(self, listPitches, listQualities, currentMode):
        """ Add one or more items to the stack """
        if currentMode == 'Chord':
            chordToAvoid = self.LookForChordToAvoid([-1, -2])
            
            self.elements.append(Chord())
            self.elements[-1].GenerateRandom(listPitches, listQualities, currentMode, chordToAvoid)
            
        elif currentMode == 'II-V-I':
            chordToAvoid = self.LookForChordToAvoid([-3, -6])

            self.elements.append(Chord())
            self.elements.append(Chord())
            self.elements.append(Chord())
            
            self.elements[-1].GenerateRandom(listPitches, ['Maj7'], currentMode, chordToAvoid)
            
            pitchV = self.elements[-1].GetPreviousPitchAlongCircleOfFifths()            
            self.elements[-2].SetPitch(pitchV)
            self.elements[-2].SetQuality('7')
            self.elements[-2].SetMode(currentMode)
            
            pitchII = self.elements[-2].GetPreviousPitchAlongCircleOfFifths()
            self.elements[-3].SetPitch(pitchII)
            self.elements[-3].SetQuality('min7')
            self.elements[-3].SetMode(currentMode)

        elif currentMode == 'II-V':
            chordToAvoid = self.LookForChordToAvoid([-1, -3], convertVtoI=True)

            self.elements.append(Chord())
            self.elements.append(Chord())
           
            self.elements[-1].GenerateRandom(listPitches, ['Maj7'], currentMode, chordToAvoid)
            
            pitchV = self.elements[-1].GetPreviousPitchAlongCircleOfFifths()
            self.elements[-1].SetPitch(pitchV)
            self.elements[-1].SetQuality('7')
            self.elements[-1].SetMode(currentMode)
            
            pitchII = self.elements[-1].GetPreviousPitchAlongCircleOfFifths()
            self.elements[-2].SetPitch(pitchII)
            self.elements[-2].SetQuality('min7')
            self.elements[-2].SetMode(currentMode)
 
        elif currentMode == 'V-I':
            chordToAvoid = self.LookForChordToAvoid([-1, -3])

            self.elements.append(Chord())
            self.elements.append(Chord())
           
            self.elements[-1].GenerateRandom(listPitches, ['Maj7'], currentMode, chordToAvoid)
            
            pitchV = self.elements[-1].GetPreviousPitchAlongCircleOfFifths()
            self.elements[-2].SetPitch(pitchV)
            self.elements[-2].SetQuality('7')
            self.elements[-2].SetMode(currentMode)

    def Initialize(self, listPitches, listQualities, currentMode):
        """ Allocate items according to the current definitions """
        while len(self.elements) < self.nbElements:
            self.AddElement(listPitches, listQualities, currentMode)
        
    def Next(self):
        """ Shift indices to display the next item """
        if self.curr < len(self.elements) - 1:
            self.curr += 1
            return True
        
        return False
        
    def Prev(self):
        """ Shift indices to display the previous item """
        if self.curr > 0:
            self.curr -= 1
            return True
        
        return False
            
    def UpdateStack(self, listPitches, listQualities, currentMode, recreating=False):
        """ Move up the stack on updates """
        if self.curr < self.nbElements/2 and \
        not recreating:
            # Just move upwards until we have reached the middle of the stack
            self.Next()
        else:
            # In case we are at the middle of the stack or further up,
            # add new chords to the stack (so that there are nbFurtherItems
            # chords upwards) and trim the older chords at the bottom of the
            # stack to retain nbElements in total 
            firstAddition = True
            while firstAddition or len(self.elements) - self.curr < self.nbFurtherItems:
                # Ensure creation of at least one new chord in the stack
                firstAddition = False
                self.AddElement(listPitches, listQualities, currentMode)
                
            # Prune the chord list (keep the last nbElements)
            nbElementsOld = len(self.elements)
            self.elements = self.elements[-self.nbElements:]
            nbElementsNew = len(self.elements)
            
            # Adjust the index of the current chord
            self.curr -= nbElementsOld - nbElementsNew - 1
            
    def RecreateNext(self, listPitches, listQualities, currentMode):
        """ Redefine elements up the list in case of a change in properties """
        # Remove the last elements in the list up to the next chord
        del self.elements[self.curr + 1:]
        # Add new elements conforming to the new prescriptions
        self.UpdateStack(listPitches, listQualities, currentMode, recreating=True)

    def GetCurrent(self):
        """ Return the current chord object """
        if self.curr < len(self.elements):
            return self.elements[self.curr]
        else:
            return self.dummy
    
    def GetPrev(self):
        """ Return the previous chord object """
        if self.curr > 0:
            return self.elements[self.curr - 1]
        else:
            return self.dummy
        
    def GetNext(self):
        """ Return the next chord object """
        if self.curr < len(self.elements) - 1:
            return self.elements[self.curr + 1]
        else:
            return self.dummy