from sdr import SDR
from segment import Segment
import random


class Synapse:
    def __init__(self, sdr, segment = None , inc = 0.01, dec = 0.01, threshold = 0.5, defaultPermanance = 0.6, verbose = False):
        self.inc = inc
        self.dec = dec
        self.threshold = threshold
        self.default = defaultPermanance
        self._value = self.default
        self.segment = segment
        self.sdr = sdr # I may not need this
        self.verbose = verbose
    
    def register(self, obj):
        if isinstance(obj, Segment):
            self.segment = obj
        if isinstance(obj, SDR):
            self.sdr = obj
    
    @property
    def value(self):
        return self._value
    

    def incPermanance(self):
        netValue = self.value + self.inc
        self._value = netValue if netValue <= 1.0 else 1.0
        
    
    def decPermanance(self):
        tmpValue = self.value - self.dec
        self._value = tmpValue if tmpValue > 0.0 else 0.0
    
    def compute(self):
        if self.segment.indx in self.sdr:
            if self.verbose:
                print("I am incrementing ")
            self.incPermanance()
        else:
            if self.verbose:
                print("I am decrementing")
            self.decPermanance()
        activeBit = bool(self.value >= self.threshold)
        self.segment.activate(activeBit)

            