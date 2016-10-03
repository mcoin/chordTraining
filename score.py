from distutils import spawn
from subprocess import call, Popen
import os
import re

class Score:
    def __init__(self, directory):
        self.directory = directory
        self.lilypond = "lilypond"
        
        # Path the lilypond exe needed to generate score images
        try:
            self.lilypond = spawn.find_executable("lilypond")
            # Special cases for windows and mac
            if self.lilypond is None:
                if os.name == 'nt':
                    self.lilypond = os.path.normpath(spawn.find_executable("lilypond", "c:/cygwin/bin"))
                elif os.name == 'posix':
                    import platform
                    if platform.system() == "Darwin":
                        path = os.environ['PATH']
                        path += ":/opt/local/bin/"
                        self.lilypond = os.path.normpath(spawn.find_executable("lilypond", path))
        except:
            self.lilypond = "lilypond"
        
        self.imageToolsAvailable = False
        try:
            from PIL import Image
            self.imageToolsAvailable = True
        except:
            pass
        
    def IsLilypondAvailable(self):
        return os.path.isfile(self.lilypond)
    
    def AreImageToolsAvailable(self):
        return self.imageToolsAvailable
    
    def GenerateImage(self, chord, scoreRes, singleThread, overwrite = False):
        basisHeader = '''
#(set-default-paper-size "a4")

\\version "2.16.2"

\\include "english.ly"

melodicMinor = #`((0 . ,NATURAL) (1 . ,NATURAL) (2 . ,FLAT) (3 . ,NATURAL) (4 . ,NATURAL) (5 . ,NATURAL) (6 . ,NATURAL))
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
        basisContentII_V = '''  
  <IIchordForm1>2
  <IIchordForm2>2 
  <VchordForm1>2
  <VchordForm2>2
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
        lyfile = chord.GetLyName(scoreRes)
        content = basisHeader + \
        basisUpperBeginning + \
        basisUpperContentChord + \
        basisUpperEnd + \
        basisLowerBeginning + \
        basisLowerContentChord + \
        basisLowerEnd + \
        basisFooter
        
        lyfile = os.path.join(self.directory, lyfile)
        
        # Only if the target file does not yet exist
        if not overwrite and os.path.isfile(re.sub(r"\.ly", r".preview.png", lyfile)):
            return
        
        f = open(lyfile, "w")
                
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
        elif chord.GetQuality() == "minMaj7":
            content = re.sub(r"chordForm1", r"ef g b d", content)
            content = re.sub(r"chordForm2", r"b d ef g", content)
            content = re.sub(r"\\key c \\major", r"\\key c \\melodicMinor", content)
        elif chord.GetQuality() == "alt":
            if chord.GetPitch() == 'Db' or \
            chord.GetPitch() == 'Eb' or \
            chord.GetPitch() == 'F' or \
            chord.GetPitch() == 'Ab' or \
            chord.GetPitch() == 'Bb':
                # Avoid very weird key signatures for certain pitches
                content = re.sub(r"chordForm1", r"e gs as ds", content)
                content = re.sub(r"chordForm2", r"as ds e gs", content)
                content = re.sub(r"\\key c \\major", r"\\key cs \\melodicMinor", content)
            else:
                content = re.sub(r"chordForm1", r"ff af bf ef", content)
                content = re.sub(r"chordForm2", r"bf ef ff af", content)
                content = re.sub(r"\\key c \\major", r"\\key df \\melodicMinor", content)
            if chord.GetPitch() == 'G' or \
            chord.GetPitch() == 'Ab' or \
            chord.GetPitch() == 'A' or \
            chord.GetPitch() == 'Bb' or \
            chord.GetPitch() == 'B':
                # Avoid large number of ledger notes for higher pitches
                content = re.sub(r"relative c ", r"relative c, ", content)
                content = re.sub(r"relative c' ", r"relative c ", content)
        elif chord.GetQuality() == "min7b5":
            if chord.GetPitch() == 'Db' or \
            chord.GetPitch() == 'Eb' or \
            chord.GetPitch() == 'Ab':
                # Avoid very weird key signatures for certain pitches
                content = re.sub(r"chordForm1", r"ds fs as css", content)
                content = re.sub(r"chordForm2", r"as css ds fs", content)
                content = re.sub(r"\\key c \\major", r"\\key ds \\melodicMinor", content)
            else:
                content = re.sub(r"chordForm1", r"ef gf bf d", content)
                content = re.sub(r"chordForm2", r"bf d ef gf", content)
                content = re.sub(r"\\key c \\major", r"\\key ef \\melodicMinor", content)
        elif chord.GetQuality() == "dim7":
            content = re.sub(r"chordForm1", r"c ef gf a", content)
            content = re.sub(r"chordForm2", r"c ef gf b", content)
            indexPitch = chord.pitches.index(chord.GetPitch())
            indexPitchCompensated = 12 - indexPitch
            indexPitchCompensated = indexPitchCompensated % len(chord.pitches)
            pitchCompensatedLy = chord.ConvertToLy(chord.pitches[indexPitchCompensated])
            if pitchCompensatedLy == "Fs":
                # Avoid very weird key signatures for F#
                content = re.sub(r"\\key c \\major", r"\\key gf \\major", content)
            else:
                content = re.sub(r"\\key c \\major", r"\\key %s \\major" % (pitchCompensatedLy.lower()), content)
        elif chord.GetQuality() == "7b9":
            content = re.sub(r"chordForm1", r"e a bf df", content)
            content = re.sub(r"chordForm2", r"bf df e a", content)
            indexPitch = chord.pitches.index(chord.GetPitch())
            indexPitchCompensated = 12 - indexPitch
            indexPitchCompensated = indexPitchCompensated % len(chord.pitches)
            pitchCompensatedLy = chord.ConvertToLy(chord.pitches[indexPitchCompensated])
            if pitchCompensatedLy == "Fs":
                # Avoid very weird key signatures for F#
                content = re.sub(r"\\key c \\major", r"\\key gf \\major", content)
            else:
                content = re.sub(r"\\key c \\major", r"\\key %s \\major" % (pitchCompensatedLy.lower()), content)
        else:
            # TODO: Other qualities not yet implemented...
            content = re.sub(r"chordForm1", r"c e g", content)
            content = re.sub(r"chordForm2", r"c e g", content)
            scalePitch = 'C'
        
        # Transpose if needed
        if chord.GetPitch() != 'C':
            content = re.sub(r"transpose c c", r"transpose c %s" % chord.GetLyPitch().lower(), content)
        f.write(content)
        f.close()

        self.CallLilypond(lyfile, scoreRes, singleThread)
        
    def GenerateScaleImage(self, chord, scoreRes, singleThread, overwrite = False):
        basisHeader = '''
#(set-default-paper-size "a4")

\\version "2.16.2"

\\include "english.ly"
\\include "../noteswithkeyboard.ly" 
'''
        basisUpperBeginning = '''
notes = \\relative c' {
  scaleDefinition 
}

upper = \\NotesWithKeyboard \\relative c' {
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
        if chord.GetScaleKind() == 'Major' or \
        chord.GetScaleKind() == 'Minor' or \
        chord.GetScaleKind() == 'Diminished':
            lyfile = chord.GetLyScaleName(scoreRes)
            content = basisHeader + \
            basisUpperBeginning + \
            basisUpperContentMajorScale + \
            basisUpperEnd + \
            basisFooter
            if chord.GetScaleKind() == 'Major':
                content = re.sub(r"scaleDefinition", r"c d e f g a b c", content)
            elif chord.GetScaleKind() == 'Minor':
                content = re.sub(r"scaleDefinition", r"c d ef f g a b c", content)
            elif chord.GetScaleKind() == 'Diminished':
                content = re.sub(r"scaleDefinition", r"c d ef f gf af a b c", content)
        else:
            # Unsupported mode
            raise
        
        lyfile = os.path.join(self.directory, lyfile)

        # Only if the target file does not yet exist
        if not overwrite and os.path.isfile(re.sub(r"\.ly", r".preview.png", lyfile)):
            return        

        f = open(lyfile, "w")
        
        # Transpose if needed
        if chord.GetScalePitch() != 'C':
            content = re.sub(r"transpose c c", r"transpose c %s" % chord.GetLyScalePitch().lower(), content)
        f.write(content)
        f.close()

        # Create include file for keyboard visualization of scales
        self.WriteNotesWithKeyboardInclude()
        
        self.CallLilypond(lyfile, scoreRes, singleThread)

    def WriteNotesWithKeyboardInclude(self):
        lyfile = "noteswithkeyboard.ly"
        content = '''
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% LSR workaround:
#(set! paper-alist (cons '("snippet" . (cons (* 190 mm) (* 155 mm))) paper-alist))
\\paper {
  #(set-paper-size "snippet")
  tagline = ##f
  indent = 0
}
\\markup\\vspace #1
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%\\language "deutsch"

%% often people think that the black keys are centered to the white keys
%% even in piano teaching books keyboards are drawn this way
%% this is not the case, black keys are positioned surprisingly excentric
%% http://lsr.di.unimi.it/LSR/Item?id=791 inspired me
%% to draw a keyboard with following features:
%% - scalable
%% - correct positioning of the black keys
%% - entering of notes which are represented by dots

%% created by Manuela
%% feel free to modify and distribute

%% all values are measured by myself on my piano

#(define white-key-width 23.5) %% the width of a white piano key
#(define white-key-height 150) %% the height of a white piano key
#(define black-key-width 15)   %% the width of a black piano key
#(define black-key-height 95)  %% the height of a black piano key
#(define black-key-y-start (- white-key-height black-key-height)) %% the y-coordinate of black keys

%% left coordinate of black keys cis/des fis/ges
%% n=0 oder n=3 (index number of global default scale)

#(define black-key-cis-start 13)
%% left coordinate of centered black keys gis/as
%% n=4 (index number of global default scale)
#(define black-key-gis-start 16)
%% left coordinate of right black keys dis/es ais/b
%% n=1 oder n=5 (index number of global default scale)

#(define black-key-dis-start 19)
#(define octav-distance (* 7 white-key-width))
%% define circle diameter for the dots
%% just try what looks fine
#(define kreis-dm (* black-key-width 0.5)) %% circle diameter

%% routine to move and scale a markup
#(define-markup-command (move-and-scale layout props mymark faktor x-offset)
   (markup? number? number?)
   (ly:stencil-translate-axis
     (ly:stencil-scale
       (interpret-markup layout props mymark)
       faktor faktor)
       x-offset X))

%% single white key
wh-taste =
#(make-connected-path-stencil
  ;; creates a square which is transformed
  ;; according to width and height of a white key
  '((0 0) (1 0) (1 1) (0 1))
  0.1 ;; thickness
  white-key-width
  white-key-height
  #t  ;; close path
  #f  ;; do not fill path
  )

w-tasten=
#(apply
   ly:stencil-add
   wh-taste
   (map
     (lambda (i) (ly:stencil-translate-axis wh-taste (* i white-key-width) X))
     (iota 6 1 1)))

%% combining two octaves
dos-w-octavas=
#(ly:stencil-add
   w-tasten
   (ly:stencil-translate-axis w-tasten octav-distance X))

%% defining single black key
bl-taste=
#(make-connected-path-stencil
  '((0 0) (1 0) (1 1) (0 1) )
  0.1
  black-key-width
  black-key-height
  #t  ;; close path
  #t  ;; fill path
  )

%% combining 5 black keys for one octave
b-tasten =
#(ly:stencil-add
  (ly:stencil-translate
   bl-taste
   (cons black-key-cis-start black-key-y-start))
  (ly:stencil-translate
   bl-taste
   (cons (+ black-key-dis-start white-key-width ) black-key-y-start))
  (ly:stencil-translate
   bl-taste
   (cons (+ black-key-cis-start (* white-key-width 3) ) black-key-y-start))
  (ly:stencil-translate
   bl-taste
   (cons (+ black-key-gis-start (* white-key-width 4) ) black-key-y-start))
  (ly:stencil-translate
   bl-taste
   (cons (+ black-key-dis-start (* white-key-width 5) ) black-key-y-start)))

%% combining to octaves black keys
dos-b-octavas=
#(ly:stencil-add
   b-tasten
   (ly:stencil-translate-axis b-tasten octav-distance X))

complete-keyboard-two-octaves=
#(ly:stencil-add
  dos-w-octavas
  dos-b-octavas)

#(define (music-name x)
   (if (not (ly:music? x))
       #f
       (ly:music-property x 'name)))

#(define (naturalize-pitch p)
   (let ((o (ly:pitch-octave p))
         (a (* 4 (ly:pitch-alteration p)))
         ;; alteration, a, in quarter tone steps,
         ;; for historical reasons
         (n (ly:pitch-notename p)))
     (cond
      ((and (> a 1) (or (eq? n 6) (eq? n 2)))
       (set! a (- a 2))
       (set! n (+ n 1)))
      ((and (< a -1) (or (eq? n 0) (eq? n 3)))
       (set! a (+ a 2))
       (set! n (- n 1))))
     (cond
      ((> a 2) (set! a (- a 4)) (set! n (+ n 1)))
      ((< a -2) (set! a (+ a 4)) (set! n (- n 1))))
     (if (< n 0) (begin (set! o (- o 1)) (set! n (+ n 7))))
     (if (> n 6) (begin (set! o (+ o 1)) (set! n (- n 7))))
     (ly:make-pitch o n (/ a 4))))

#(define (white-key? p)
   (let
    ((a (ly:pitch-alteration (naturalize-pitch p))))
    (if (= a 0)
        #t
        #f)))

#(define (start-point-key p)
   ;; calculation the starting point of a key
   ;; depending on the pitch p
   ;; result (x . y)
   (let*
    ((m (naturalize-pitch p))
     (o (ly:pitch-octave m))
     (a (ly:pitch-alteration m))
     ;; we must naturalize pitch otherwise wrong result for eis e.g.
     ;; we subtract the alteration from the notename and add a half
     ;; so we end up at the same note despite flat oder sharp
     ;; cis is drawn the same as des e.g.
     (n  (ly:pitch-notename m))
     (n1 (+ n a -0.5))
     (x-shift (* o 7 white-key-width))
     )
    (cond
     ((eq? a 0)
      ;; alteration eq 0
      ;; no alteration ==> white key
      (cons (+ (* n white-key-width) x-shift) 0 ))
     ((or (= n1 0) (= n1 3))
      ;; "left" black keys cis/des and fis/ges
      ;; notename=0 or 3 and alteration
      ;; n=0 oder n=3
      (cons (+ (* n1 white-key-width) black-key-cis-start x-shift ) black-key-y-start ))
     ((or (= n1 1) (= n1 5))
      ;; "right" black keys dis/es and ais/b
      ;; notename=0 or 3 and alteration
      ;, n=1 oder n=5
      (cons (+ (* n1 white-key-width) black-key-dis-start x-shift ) black-key-y-start ))
     (else
      ;; only one left, the centered black key gis/as
      (cons (+ (* n1 white-key-width) black-key-gis-start x-shift) black-key-y-start )))))

#(define (make-dot p)
   (let* ((start-p (start-point-key p)))
     (if (white-key? p)
         (ly:stencil-in-color
           (ly:stencil-translate
             (make-circle-stencil kreis-dm 0 #t)
             (cons
               (+ (car start-p) (/ white-key-width 2 ))
               (+ (cdr start-p) (/ (- white-key-height black-key-height) 1.5))))
           1.0 0.0 0.0) ;; color (on white keys)
         (ly:stencil-in-color
           (ly:stencil-translate
             (make-circle-stencil kreis-dm 0 #t)
             (cons
               (+ (car start-p) (/ black-key-width 2 ))
               (+ (cdr start-p) (/ black-key-height 5))))
           1.0 0.0 0.0) ;; color (on black keys)
         )))

%% creating a single stencil of multiple dots for a list of pitches
#(define (make-dot-list l1)
  (if (every ly:pitch? l1)
      (apply ly:stencil-add (map make-dot l1))
      empty-stencil))

#(define-markup-command (complete layout props the-chord)
  (ly:music?)
  (ly:stencil-scale
   (ly:stencil-add
    dos-w-octavas
    dos-b-octavas
    (make-dot-list 
      (map
        (lambda (m) (ly:music-property m 'pitch))
        (extract-named-music the-chord 'NoteEvent)))) 
    0.070 0.070))

NotesWithKeyboard=
#(define-music-function (parser location the-chord)
  (ly:music?)
  #{ <>^\\markup \\complete #the-chord $the-chord #})


%notes = \\relative { c' d e f g a b c}
%
%notess = \\transpose c f \\notes
%
%\\score {
%  <<
%%    \\new Staff \\NotesWithKeyboard \\chordmode { b:7sus4 }
%%    \\new Staff \\NotesWithKeyboard \\relative { c' d e f g a b c}
%    \\new Staff \\NotesWithKeyboard \\notess
%%    \\new ChordNames \\chordmode { b:sus4 }
%  >>
%}        
        '''
        
        lyfile = os.path.join(self.directory, lyfile)

        # Only if the target file does not yet exist
        if os.path.isfile(lyfile):
            return        

        f = open(lyfile, "w")
        f.write(content)
        f.close()
        
                
    def CallLilypond(self, lyfile, scoreRes, singleThread = False):
        dbg = False
        try:
            if dbg:
                catOutputFile = os.path.join(self.directory, "cat_outputFile")
                f = open(catOutputFile, "w")
        
                rc = call(["cat", lyfile], stdout=f)
                f.close()
            
                print "rc = %s" % rc
            
            # The lilypond call apparently won't work properly without an explicit stdout redirection...
            lilypondOutputFile = os.path.join(self.directory, "lilypond_outputFile")
            f = open(lilypondOutputFile, "w")
            wdir = os.path.join(self.directory, "res" + str(scoreRes))
            proc = Popen([self.lilypond, "--png", "-dresolution=" + str(scoreRes), "-dpreview", "-dno-print-pages", lyfile], \
                         stdout=f, cwd=wdir)
            # Do not continue after starting the lilypond process
            # (useful on slower machines, e.g. raspberryPi)
            if singleThread:
                proc.wait()
                
            f.close()
            
            if dbg:
                print "rc = %s" % rc

#             # Remove the normal .png file (only the .preview.png file is needed)
#             pngFile = re.sub(r".ly", r".png", lyfile)
#             try:
#                 if dbg:
#                     print "Trying to remove file '%s'" % pngFile
#                 os.remove(pngFile)
#             except:
#                 if dbg:
#                     print "Removing png file failed"
#                 pass

            # Remove the .preview.eps file (only the .preview.png file is needed)
            epsFile = re.sub(r".ly", r".preview.eps", lyfile)
            try:
                if dbg:
                    print "Trying to remove file '%s'" % epsFile
                os.remove(epsFile)
            except:
                if dbg:
                    print "Removing eps file failed"
                pass
        except:
            print "Call to lilypond failed."