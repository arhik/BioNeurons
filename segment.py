from math import log

class Segment:
    def __init__(self, root=None,  isRoot=False, tree=None, level = 0, parent = None, maxLevel = 5):
        self.isRoot = isRoot
        self.parent = None if isRoot == True else parent
        self.leftSegment = None
        self.rightSegment = None
        self.level = 0
        self.leaf = False
        self.maxLevel = maxLevel
        self._active = 0
        self._indx = None
        self._value = 0
        self.type = None
        self.tree = tree
        self._activity = 0.
        # self._criticalValue = 2**self.maxLevel if self.isRoot else None

    def setIndx(self, indx):
        self._indx = indx

    @property
    def indx(self):
        return self._indx

    @property
    def value(self):
        return self._value

    @property
    def active(self):
        return self._active
    
    @property
    def activity(self):
        return self._activity

    def activate(self, activeBit):
        self._value = self.value + int(activeBit)
        self._active = 1 if self.value > 0 else 0
        self._activity = (self._activity + self.active)/2
        if self.parent != None:
            self.parent.activate(activeBit)
        
        
    def reset(self):
        self._value = 0
        self._active = 0