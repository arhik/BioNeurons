import random
class SDR:
    def __init__(self, length, numActiveBits):
        self.length = length
        self.numActiveBits = numActiveBits
        self.rng = random.Random()
        self.samples = []
    
    def generateSamples(self, n):
        for i in range(n):
            self.samples.append(self.rng.sample(xrange(self.length), self.numActiveBits))
    
    def getSampleSDR(self):
        yield self.rng.choice(self.samples), self.length

class PeriodicSDR(SDR):
    def getSampleSDR(self):
        indx = 0
        while True:
            yield self.samples[indx], self.length
            indx += 1
            if indx == len(self.samples):
                indx=0