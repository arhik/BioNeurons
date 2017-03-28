import random
from synapse import Synapse
from segment import Segment
from sdr import SDR
rng = random.Random()
rng.seed(1337)
from math import log
from itertools import chain

class DendriteTree(object):
    def __init__(self, type="Binary", levels =7, pattern = "uniform"):
        self.root=Segment(isRoot=True)
        self.levels = levels
        self.segments = []
        self.synapses = []
        self.buildTree()

    def buildTree(self):
        frontier = [self.root]
        self.segments.append(self.root)
        nextFrontier = []
        # self.frontiers = []
        # self.frontiers.append(frontier)
        for l in range(self.levels):
            for i in frontier:
                i.leftSegment = Segment(parent=i, level=l, maxLevel=self.levels)
                i.rightSegment = Segment(parent=i,level=l, maxLevel=self.levels)
                nextFrontier.extend([i.leftSegment, i.rightSegment])
            self.segments.extend(nextFrontier)
            # self.frontiers.append(nextFrontier)
            frontier = nextFrontier
            nextFrontier = []

    def initiateSynapses(self, sdrs):
        for sdr in sdrs:
            if sdr.size >= len(self.segments):
                indices = list(xrange(sdr.size))
                if isinstance(self, ProximalDendriteTree):
                    if self.neuron.indx in indices:
                        print(self.neuron.indx)
                        print("preventing self loop")
                        indices.remove(self.neuron.indx) 
                    indices = rng.sample(indices, len(self.segments))
                else:
                    indices = rng.sample(indices, len(self.segments))
                for i,indx in enumerate(indices):
                    self.segments[i]._indx = indx
            elif sdr.size < len(self.segments):
                indices = list(xrange(len(self.segments)))
                if isinstance(self, ProximalDendriteTree):
                    if self.neuron.indx in indices:
                        print(self.neuron.indx)
                        print("preventing self loop")
                        indices.remove(self.neuron.indx) 
                    indices = rng.sample(indices, sdr.size)
                self.segments = [self.segments[i] for i in indices]
                for indx, i in enumerate(self.segments):
                    i._indx = indx
            if isinstance(self, ProximalDendriteTree):
                self.synapses = [Synapse(sdr, segment, inc=0.001, dec=0.0005) for segment in self.segments]
            else:
                self.synapses = [Synapse(sdr, segment) for segment in self.segments]

    def compute(self):
        for i in self.synapses:
            i.compute()

    def reset(self):
        for i in self.segments:
            i.reset()

class DistalDendriteTree(DendriteTree):
    def __init__(self):
        super(DistalDendriteTree, self).__init__()

class ProximalDendriteTree(DendriteTree):
    def __init__(self, neuron = None):
        super(ProximalDendriteTree, self).__init__()
        self.neuron = neuron
        if self.neuron == None:
            raise Exception
    

class BasalDendriteTree(DendriteTree):
    def __init__(self):
        super(BasalDendriteTree, self).__init__()


class Neuron:
    def __init__(self, inputSDR = None, indx=None, activeNeuronSDR = None, lateralSDRs = []):
        self.inputSDR = inputSDR
        self.threshold = 0.1
        self.history = [[],[],[]]
        self._active = 0
        self.activeNeuronSDR = activeNeuronSDR
        self.indx = indx

        # self.indx = sum([inputSDR.length].extend([lateralSDR.length for i in lateralSDRs]))
        # self.distalDendrites = DistalDendriteTree()
        # self.distalDendrites.levels = 8
        # self.distalDendrites.root.type = self.distalDendrites
        # self.distalDendrites.initiateSynapses(self.inputSDR)

        self.proximalDendrites = ProximalDendriteTree(neuron=self)
        self.proximalDendrites.levels = 5
        self.proximalDendrites.root.type = self.proximalDendrites
        self.proximalDendrites.initiateSynapses([self.activeNeuronSDR])

        self.basalDendrites = BasalDendriteTree()
        self.basalDendrites.root.type = self.basalDendrites
        self.basalDendrites.initiateSynapses([self.inputSDR])

    def compute(self):
        
        self.basalDendrites.compute()
        # threshold = self.threshold*self.basalDendrites.levels
        if self.basalDendrites.root.value >= self.threshold:
            self._active = 1
            self.history[0].append((self._active, self.basalDendrites.root.value ))
            self.fire(self.basalDendrites)            
        else:
            self._active = 0
            self.history[0].append((self._active, self.basalDendrites.root.value ))
        

        self.proximalDendrites.compute()
        # threshold = self.threshold*self.proximalDendrites.levels
        if self.proximalDendrites.root.value >= self.threshold:
            self._active = 1
            self.history[1].append((self._active, self.proximalDendrites.root.value ))
            self.fire(self.proximalDendrites)
        else:
            self._active = 0
            self.history[1].append((self._active, self.proximalDendrites.root.value ))
        
        
        # self.distalDendrites.compute()
        # self.threshold = 0.6*(self.distalDendrites.levels)
        # if self.distalDendrites.root.value > self.threshold:
        #     self._active = 1
        # else:
        #     self._active = 0
        # self.history[2].append((self._active, self.distalDendrites.root.value ))
        # self.fire(self.distalDendrites)

    def fire(self, tree):
        tree.reset()


class MiniColumn:
    def __init__(self, numNeurons, inputSDR = None, indx=None):
        self.numNeurons = numNeurons
        self.inputSDR = inputSDR
        self.neurons = []
        self.indx = indx
        self.threshold  = 10
        self._active = 0
        self.activeNeuronSDR = SDR(self.numNeurons, 8)
        self.activeNeuronSDR.curSDR = []
        for i in range(numNeurons):
            self.neurons.append(Neuron(inputSDR = self.inputSDR, activeNeuronSDR=self.activeNeuronSDR, lateralSDRs=None, indx=i))
    
    def compute(self):
        tmp = set()
        for i in self.neurons:
            i.compute()
            if i._active:
                tmp.add(i.indx)
                self.activeNeuronSDR.curSDR = list(tmp)
        if len(self.activeNeuronSDR) > self.threshold:
            self._active = 1
        else:
            self._active = 0

    def getOutputSDR(self):
        return self.activeNeuronSDR


class Layer23:
    def __init__(self, numMiniColumns, numNeurons, miniColumnSDR = None, inputSDR = None, outputLayerSDR = None):
        self.numMiniColumns = numMiniColumns
        self.inputSDR = inputSDR
        self.miniColumnSDR = SDR(self.numMiniColumns, 10) if miniColumnSDR == None else miniColumnSDR
        self.miniColumns = []
        self.numNeurons = numNeurons
        for i in range(self.numMiniColumns):
            self.miniColumns.append(MiniColumn(self.numNeurons , inputSDR = self.inputSDR, indx = i))

    def compute(self):
        tmp = set()
        for i in self.miniColumns:
            i.compute()
            if i._active:
                tmp.add(i.indx)
                self.miniColumnSDR.curSDR = list(tmp)

    def getOutputSDR(self):
        return self.miniColumn.curSDR