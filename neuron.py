import random
from synapse import Synapse
from segment import Segment
from sdr import SDR
rng = random.Random()
rng.seed(1337)

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

    def initiateSynapses(self, sdr):
        sdrlength = sdr.length if isinstance(sdr, SDR) else sdr[1]
        if sdrlength >= len(self.segments):
            indices = list(xrange(sdrlength))
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
        elif sdrlength < len(self.segments):
            indices = list(xrange(len(self.segments)))
            if isinstance(self, ProximalDendriteTree):
                if self.neuron.indx in indices:
                    print(self.neuron.indx)
                    print("preventing self loop")
                    indices.remove(self.neuron.indx) 
                indices = rng.sample(indices, sdrlength)
            self.segments = [self.segments[i] for i in indices]
            for indx, i in enumerate(self.segments):
                i._indx = indx
        if isinstance(self, ProximalDendriteTree):
            self.synapses = [Synapse(sdr[0], segment, inc=0.001, dec=0.005) for segment in self.segments]
        else:
            self.synapses = [Synapse(sdr[0], segment) for segment in self.segments]

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
    def __init__(self, inputSDR = None, indx=None, lateralSDRs = [], outputSDR = None):
        self.inputSDR = inputSDR
        self.threshold = 35
        self.history = [[],[],[]]
        self._active = 0
        self.outputSDR = outputSDR if outputSDR!=None else [[],1024]
        self.indx = indx

        # self.indx = sum([inputSDR.length].extend([lateralSDR.length for i in lateralSDRs]))

        # self.distalDendrites = DistalDendriteTree()
        # self.distalDendrites.levels = 8
        # self.distalDendrites.root.type = self.distalDendrites
        # self.distalDendrites.initiateSynapses(self.inputSDR)

        self.proximalDendrites = ProximalDendriteTree(neuron=self)
        self.proximalDendrites.levels = 5
        self.proximalDendrites.root.type = self.proximalDendrites
        self.proximalDendrites.initiateSynapses(self.outputSDR)

        self.basalDendrites = BasalDendriteTree()
        self.basalDendrites.root.type = self.basalDendrites
        self.basalDendrites.initiateSynapses(inputSDR)

    def compute(self):
        self.basalDendrites.compute()
        if self.basalDendrites.root.value >= self.threshold:
            self._active = 1
            self.fire(self.basalDendrites)            
        else:
            self._active = 0
        self.history[0].append((self._active, self.basalDendrites.root.value ))

        self.proximalDendrites.compute()
        if (self.basalDendrites.root.value + self.proximalDendrites.root.value) >= self.threshold:
            self._active = 1
            self.fire(self.proximalDendrites)
        else:
            self._active = 0
        self.history[1].append((self._active, self.proximalDendrites.root.value ))
        

        # self.distalDendrites.compute()
        # if self.distalDendrites.root.value > self.threshold:
        #     self._active = 1
        # else:
        #     self._active = 0
        # self.history[2].append((self._active, self.distalDendrites.root.value ))
        # self.fire(self.distalDendrites)

    def fire(self, tree):
        tree.reset()


class MiniColumn:
    def __init__(self, numNeurons, inputSDR = None, outputSDR = None, indx=None):
        self.numNeurons = numNeurons
        self.inputSDR = inputSDR
        self.neurons = []
        self.indx = indx
        self.threshold  = 10
        self._active = 0
        self.outputSDR = outputSDR if outputSDR!=None else [[],1024]
        self.miniColumnSDR = None
        for i in range(numNeurons):
            self.neurons.append(Neuron(inputSDR = self.inputSDR, outputSDR = self.outputSDR, lateralSDRs=None, indx=i))
    
    def compute(self):
        tmp = set()
        for i in self.neurons:
            i.compute()
            if i._active:
                tmp.add(i.indx)
                self.miniColumnSDR = list(tmp)
        if len(self.miniColumnSDR) > self.threshold:
            self._active = 1
        else:
            self._active = 0
        print(self.miniColumnSDR)

    def getOutputSDR(self):
        return self.miniColumnSDR

class Layer23:
    def __init__(self, numMiniColumns, numNeurons, inputSDR = None, outputSDR = None):
        self.numMiniColumns = numMiniColumns
        self.inputSDR = inputSDR
        self.outputSDR = outputSDR if outputSDR!=None else [[], self.numMiniColumns]
        self.miniColumns = []
        self.numNeurons = numNeurons
        for i in range(self.numMiniColumns):
            self.miniColumns.append(MiniColumn( self.numNeurons ,inputSDR = self.inputSDR, outputSDR = self.outputSDR, indx = i))
        
    def compute(self):
        tmp = set()
        self.outputSDR[0] = []
        for i in self.miniColumns:
            i.compute()
            if i._active:
                tmp.add(i.indx)
                self.outputSDR[0] = list(tmp)

    def getOutputSDR(self):
        return self.outputSDR
            
