import random

class SDR(object):
    def __init__(self, size, numActiveBits, type = None):
        self.size = size
        self.numActiveBits = numActiveBits
        self.rng = random.Random()
        self.samples = []
        self._curSDR = []
        self.type = type
    
        
    def __len__(self):
        return len(self.curSDR)

    @property
    def curSDR(self):
        return self._curSDR[:self.numActiveBits] if len(self._curSDR) > self.numActiveBits else self._curSDR
    
class SDRGen(SDR):
    def getSampleSDR(self):
        self._curSDR = random.sample(xrange(self.size), self.numActiveBits)
        return self.curSDR

class PeriodicSDR(SDR):
    def __init__(self, size, numActiveBits, n):
        super(PeriodicSDR, self).__init__(size, numActiveBits)
        self.n = n
        self.samples.extend([SDRGen(size, numActiveBits, n).getSampleSDR() for i in range(n)])
        self.gen = self._rotate()
        self._curSDR = []

    @property
    def curSDR(self):
        return self._curSDR
    
    def _rotate(self):
        indx = 0
        while True:
            self._curSDR = self.samples[indx]
            yield self.curSDR
            indx += 1
            if indx == len(self.samples):
                indx=0
        
    def getSampleSDR(self):
        return next(self.gen)
        

