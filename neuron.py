import random
from synapse import Synapse
from segment import Segment
from sdr import SDR
rng = random.Random()
rng.seed(1337)
from math import log
from itertools import chain

class DendriteTree(object):
    def __init__(self, neuron = None, type="Binary", levels =9, pattern = "uniform"):
        self.root=Segment(isRoot=True)
        self.levels = levels
        self.segments = []
        self.synapses = []
        self.neuron = neuron
        self.buildTree()

    def buildTree(self):
        frontier = [self.root]
        self.segments.append(self.root)
        nextFrontier = []
        for l in range(self.levels):
            for i in frontier:
                i.leftSegment = Segment(parent=i, level=l, maxLevel=self.levels)
                i.rightSegment = Segment(parent=i,level=l, maxLevel=self.levels)
                nextFrontier.extend([i.leftSegment, i.rightSegment])
            self.segments.extend(nextFrontier)
            frontier = nextFrontier
            nextFrontier = []
    
    def compute(self):
        for j in self.synapses:
            for synapse in j:
                activeBit = bool(synapse.value >= synapse.threshold)
                synapse.segment.activate(activeBit)
                if self.neuron._active:
                    if synapse.segment.indx in synapse.sdr.curSDR:
                        synapse.incPermanance()
                    else:
                        synapse.decPermanance()
                else:
                    if synapse.segment.indx  in synapse.sdr.curSDR:
                        synapse.decPermanance()
                    else:
                        synapse.incPermanance()


                    
    def reset(self):
        for i in self.segments:
            i.reset()

class DistalDendriteTree(DendriteTree):
    def __init__(self, neuron = None):
        super(DistalDendriteTree, self).__init__()
        self.neuron = neuron
        if neuron == None:
            raise Exception

class ProximalDendriteTree(DendriteTree):
    def __init__(self, neuron = None):
        super(ProximalDendriteTree, self).__init__()
        self.neuron = neuron
        if neuron == None:
            raise Exception
        
    def initiateSynapses(self, activeNeurons, lateralSDRS = None):
        sdrs = []
        sdrs.append(activeNeurons)
        sdrs.extend(lateralSDRS if lateralSDRS else []) 
        for sdrindx, sdr in enumerate(sdrs):
            if sdr.size >= len(self.segments):
                indices = list(xrange(sdr.size))
                if isinstance(self, ProximalDendriteTree):
                    if sdrindx == self.neuron.indx:
                        if self.neuron.indx in indices:
                            print(self.neuron.indx)
                            print("preventing self loop")
                            indices.remove(self.neuron.indx)
                    # TODO try Except not necessary
                    try:
                        indices = rng.sample(indices, len(self.segments))
                    except ValueError:
                        indices = rng.sample(indices, len(self.segments)-1)
                else:
                    indices = rng.sample(indices, len(self.segments))
                for i,indx in enumerate(indices):
                    self.segments[i]._indx = indx
            elif sdr.size < len(self.segments):
                indices = list(xrange(len(self.segments)))
                if isinstance(self, ProximalDendriteTree):
                    if sdrindx == self.neuron.indx:
                        if self.neuron.indx in indices:
                            print(self.neuron.indx)
                            print("preventing self loop")
                            indices.remove(self.neuron.indx) 
                    indices = rng.sample(indices, sdr.size)
                self.segments = [self.segments[i] for i in indices]
                for indx, i in enumerate(self.segments):
                    i._indx = indx
            if isinstance(self, ProximalDendriteTree):
                self.synapses.append([Synapse(sdr, segment, inc=0.1, dec=0.2) for segment in self.segments])
            else:
                self.synapses.append([Synapse(sdr, segment) for segment in self.segments])



class BasalDendriteTree(DendriteTree):
    def __init__(self, neuron = None):
        super(BasalDendriteTree, self).__init__()
        self.neuron = neuron
        if neuron == None:
            raise Exception

    def initiateSynapses(self, sdr):
        if sdr.size >= len(self.segments):
            indices = list(xrange(sdr.size))
            indices = rng.sample(indices, len(self.segments))
            for i, indx in enumerate(indices):
                self.segments[i]._indx = indx
        elif sdr.size < len(self.segments):
            indices = list(xrange(len(self.segments)))
            self.segments = [self.segments[i] for i in indices]
            for indx, i in enumerate(self.segments):
                i._indx = indx
        self.synapses.append([Synapse(sdr, segment) for segment in self.segments])
        
class Neuron:
    def __init__(self, inputSDR = None, indx=None, activeNeuronsSDR):
        self.inputSDR = inputSDR
        self.history = [[],[],[]]
        self._active = 0
        self.indx = indx
        self.activeNeuronsSDR = activeNeuronsSDR
        # self.indx = sum([inputSDR.length].extend([lateralSDR.length for i in lateralSDRs]))
        # self.distalDendrites = DistalDendriteTree()
        # self.distalDendrites.levels = 8
        # self.distalDendrites.root.type = self.distalDendrites
        # self.distalDendrites.initiateSynapses(self.inputSDR)

        # self.proximalDendrites = ProximalDendriteTree(neuron=self)
        # self.proximalDendrites.levels = 5
        # self.proximalDendrites.root.type = self.proximalDendrites
        # self.proximalDendrites.initiateSynapses(self.activeNeuronSDR, self.lateralSDRs)

        self.basalDendrites = BasalDendriteTree(neuron = self)
        self.basalDendrites.root.type = self.basalDendrites
        self.basalDendrites.initiateSynapses(self.inputSDR)
    
    @property
    def threshold(self):
        return 1.0

    @property
    def bias(self):
        try:
            bias = 0#0.25*(log(self.proximalDendrites.root.value,2)/2)/self.proximalDendrites.levels
        except ValueError as e:
            bias = 0
        return bias

    @property
    def response(self):
        try:
            response = 0.75*(log(self.basalDendrites.root.value, 2))/self.basalDendrites.levels # double check this
        except ValueError as e:
            response = 0
        return response

    @property
    def activation(self):
        return self.bias + self.response if self.bias!=None else self.response

    def compute(self):
        self.basalDendrites.compute()
        if self.activation >= self.threshold:
            self._active = 1
            self.activeNeuronsSDR.append(self.indx)
            self.history[0].append((self._active, self.basalDendrites.root.value ))
            self.fire()
        else:
            self._active = 0
            self.history[0].append((self._active, self.basalDendrites.root.value ))
        yield self._active
        # self.proximalDendrites.compute()
    
        # #proximal only provide bias but investigate if they play role in spiking
        # # if self.bias >= self.threshold:
        #     # self._active = 1
        #     # self.history[1].append((self._active, self.proximalDendrites.root.value ))
        #     # self.fire()
        # # else:
        #     # self._active = 0
        # self.history[1].append((self._active, self.proximalDendrites.root.value ))

        # yield None
        


        
        
        # self.distalDendrites.compute()
        # self.threshold = 0.6*(self.distalDendrites.levels)
        # if self.distalDendrites.root.value > self.threshold:
        #     self._active = 1
        # else:
        #     self._active = 0
        # self.history[2].append((self._active, self.distalDendrites.root.value ))
        # self.fire(self.distalDendrites)

    def fire(self): #depolarize
        self.proximalDendrites.reset()
        self.basalDendrites.reset()
        


class MiniColumn:
    def __init__(self, numNeurons, inputSDR = None, indx=None, activeNeuronSDRs = None):
        self.numNeurons = numNeurons
        self.inputSDR = inputSDR
        self.neurons = []
        self.indx = indx
        self._active = 0
        self.activeNeuronSDRs = activeNeuronSDRs.remove(self.activeNeuronSDR)
        for i in range(numNeurons):
            self.neurons.append(Neuron(inputSDR = self.inputSDR, activeNeuronSDR = self.activeNeuronSDRs[i], \
                        lateralSDRs = activeNeuronSDRs[0:i] + activeNeuronSDRs[i+1:], indx=i))
    
    def compute(self):
        tmp = []
        computegens = []
        activity = []
        for neuron in self.neurons:
            computegens.append(neuron.compute())
        for i, neuron in enumerate(self.neurons):
            _active = next(computegens[i])
            activity.append(_active)
        for i, neuron in enumerate(self.neurons):
            if activity[i]:
                tmp.append(neuron.indx)
                tmp.sort(key=lambda x: neuron.response , reverse=True)
                self.activeNeuronSDRs[i]._curSDR = tmp
                if neuron.indx in self.activeNeuronSDRs[i].curSDR:
                    self._active = 1
                else: 
                    self._active = 0
        # for i, neuron in enumerate(self.neurons):
        #     next(computegens[i])                    
    def getOutputSDR(self):
        return self.activeNeuronSDRs


class Layer23:
    def __init__(self, numMiniColumns, numNeurons, miniColumnSDR = None, inputSDR = None, outputLayerSDR = None):
        self.numMiniColumns = numMiniColumns
        self.inputSDR = inputSDR
        self.miniColumnSDR = SDR(self.numMiniColumns, 10, type = "miniColumn") if miniColumnSDR == None else miniColumnSDR
        self.miniColumns = []
        self.numNeurons = numNeurons
        self.activeNeuronSDRs = [SDR(self.numNeurons, 8, type="activeNeuronSDR") for i in range(numNeurons)]
        for i in range(self.numMiniColumns):
            self.miniColumns.append(MiniColumn(self.numNeurons ,inputSDR = self.inputSDR, indx = i, activeNeuronSDRs = self.activeNeuronSDRs))

    def compute(self):
        tmp = set()
        activity = []
        for i in self.miniColumns:
            i.compute()
        for i in self.miniColumns:
            if i._active:
                tmp.add(i.indx)
                self.miniColumnSDR._curSDR = list(tmp)

    def getOutputSDR(self):
        return self.miniColumn.curSDR
