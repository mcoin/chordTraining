import os

class StayOn:
    def __init__(self):
        self.pyMouseEnabled = False
        # Disable import of pymouse for debug purposes 
        # (makes startup extremely slow)
        if "DISABLE_STAYON" in os.environ:
            return
     
        # Use the PyMouse framework to move the mouse periodically
        try:
            from pymouse import PyMouse
            self.pyMouseEnabled = True
        except:
            # Give up in case the PyMouse framework cannot be found
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
        
