import random
from synapse import Synapse
from segment import Segment
from sdr import SDR
rng = random.Random()
rng.seed(1337)
from math import log
from itertools import chain


class DendriteTree(object):
    def __init__(self, neuron = None, type="Binary", levels = 7, pattern = "uniform"):
        self.root=Segment(isRoot=True)
        self.levels = levels
        self.segments = []
        self.synapses = []
        self.neuron = neuron
        self.buildTree()
        self.computeGen = None

    def buildTree(self):
        frontier = [self.root]
        self.segments.append(self.root)
        nextFrontier = []
        for l in range(self.levels):
            for i in frontier:
                i.leftSegment = Segment(root=self.root,  parent=i, level=l, maxLevel=self.levels)
                i.rightSegment = Segment(root=self.root, parent=i,level=l, maxLevel=self.levels)
                nextFrontier.extend([i.leftSegment, i.rightSegment])
            self.segments.extend(nextFrontier)
            frontier = nextFrontier
            nextFrontier = []
    
    def compute(self):
        for synapse in self.synapses:
            activeBit = bool(synapse.value >= synapse.threshold)
            synapse.segment.activate(activeBit)
        yield None

        if self.neuron._active:
            for synapse in self.synapses:
                if synapse.segment.indx in synapse.sdr.curSDR:
                    synapse.incPermanance()
                else:
                    synapse.decPermanance()
        
        # if self.neuron.iteration > 10:
        if len(self.synapses) > 2**self.levels:
            orderedActiveSynapses = sorted(self.synapses, key=lambda x: x.segment.activity)
            if len(orderedActiveSynapses) > 40:
                leastActiveSynapses = orderedActiveSynapses[:40]
                for synapse in leastActiveSynapses:
                    synapse.segment._indx = None
                    synapse.segment._value = 0
                    synapse.segment._activity = 0
                    synapse.segment._active = 0
                    self.synapses.remove(synapse)

        elif len(self.synapses) < 20:
            for i in range(2**self.levels - len(self.synapses)):
                segments = [i for i in self.segments if i.indx == None]
                if len(segments) !=0:
                    segment = rng.choice(segments)
                    segment._indx = rng.choice(synapse.sdr.curSDR)
                    self.synapses.append(Synapse(synapse.sdr, segment))
                else:
                    segments = []
        
        yield None
                        #TODO 

                        # create segments onto top segments
                # if self.neuron.activity >= 0.9:
                #     if synapse.segment.activity < 0.01 and len(self.synapses) < 40:
                #         segments = [i for i in self.segments if i.indx == None]
                #         if len(segments)!=0:
                #             segment = rng.choice(segments)
                #             segment._indx = rng.choice(synapse.sdr.curSDR)
                #             self.synapses.append(Synapse(synapse.sdr, segment))
                #             print("growing synapse")
                #     if synapse.segment.activity >= 0.99 and len(self.synapses) > 40:
                #         synapse.segment._indx = None
                #         synapse.segment._value = 0
                #         synapse.segment._activity = 0
                #         synapse.segment._active = 0
                #         self.synapses.remove(synapse)
                #         print("pruning synapse")
                # elif self.neuron.activity < 0.1:
                #     if synapse.segment.activity > 0.99 and len(self.synapses) < 2**self.levels:
                #         segments = [i for i in self.segments if i.indx == None]
                #         if len(segments)!=0:
                #             segment = rng.choice(segments)
                #             segment._indx = rng.choice(synapse.sdr.curSDR)
                #             self.synapses.append(Synapse(synapse.sdr, segment))
                #             # print("growing synapse")


    def reset(self):
        for i in self.synapses:
            i.segment.reset()


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
        
    def initiateSynapses(self, activeNeuronsSDR, lateralSDRS = None):
        if activeNeuronsSDR.size >= len(self.segments):
            indices = list(xrange(activeNeuronsSDR.size))
            if self.neuron.indx in indices:
                indices.remove(self.neuron.indx)
            indices = rng.sample(indices, len(self.segments))
            for i,indx in enumerate(indices):
                self.segments[i]._indx = indx
        elif activeNeuronsSDR.size < len(self.segments):
            indices = list(xrange(len(self.segments)))
            if self.neuron.indx in indices:
                indices.remove(self.neuron.indx) 
            indices = rng.sample(indices, activeNeuronsSDR.size)
            self.segments = [self.segments[i] for i in indices]
            for indx, i in enumerate(self.segments):
                i._indx = indx
        self.synapses.extend([Synapse(activeNeuronsSDR, segment, inc=0.01, dec=0.05) for segment in self.segments])


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
        self.synapses.extend([Synapse(sdr, segment) for segment in self.segments])


class Neuron:
    def __init__(self, inputSDR = None, activeNeuronsSDR = None, indx=None):
        self.inputSDR = inputSDR
        self.history = [[],[],[]]
        self._active = 0
        self.indx = indx
        self._iteration = 0
        self._activity = 0
        
        # self.indx = sum([inputSDR.length].extend([lateralSDR.length for i in lateralSDRs]))
        # self.distalDendrites = DistalDendriteTree()
        # self.distalDendrites.levels = 8
        # self.distalDendrites.root.type = self.distalDendrites
        # self.distalDendrites.initiateSynapses(self.inputSDR)

        self.proximalDendrites = ProximalDendriteTree(neuron=self)
        self.proximalDendrites.levels = 3
        self.proximalDendrites.root.type = self.proximalDendrites
        self.activeNeuronsSDR = activeNeuronsSDR
        
        if self.proximalDendrites !=None:
            if self.activeNeuronsSDR == None:
                raise Exception("No activeNeuronsSDR for proximal computation.")
        self.proximalDendrites.initiateSynapses(self.activeNeuronsSDR)

        self.basalDendrites = BasalDendriteTree(neuron = self)
        self.basalDendrites.root.type = self.basalDendrites
        self.basalDendrites.initiateSynapses(self.inputSDR)

    @property
    def active(self):
        return self._active

    @property
    def iteration(self):
        return self._iteration

    @property
    def activity(self):
        return self._activity

    @property
    def threshold(self):
        return 1.0

    @property
    def bias(self):
        try:
            bias = .2*(log(self.proximalDendrites.root.value,2)/2)/log(len(self.proximalDendrites.synapses*2),2)
            # bias = float(self.proximalDendrites.root.value)/self.proximalDendrites.root._criticalValue
            # bias = float(self.proximalDendrites.root.value)
        except ValueError as e:
            bias = 0
        return bias

    @property
    def response(self):
        try:
            response = .8*(log(self.basalDendrites.root.value, 2))/log(len(self.basalDendrites.synapses), 2) # double check this
            # response = float(self.basalDendrites.root.value)/self.basalDendrites.root._criticalValue
            # response = float(self.basalDendrites.root.value)
        except ValueError as e:
            response = 0
        return response

    @property
    def activation(self):
        return self.bias + self.response #if self.bias!=None else self.response

    def compute(self):
        self._iteration += 1
        if self.proximalDendrites.computeGen == None:
            self.proximalDendrites.computeGen = self.proximalDendrites.compute()

        next(self.proximalDendrites.computeGen)
        next(self.proximalDendrites.computeGen)
        self.basalDendrites.computeGen = self.basalDendrites.compute()
        next(self.basalDendrites.computeGen)
        if self.activation >= self.threshold:
            self._active = 1
            self.history[0].append((self._active, self.basalDendrites.root.value ))
        else:
            self._active = 0
            self.history[0].append((self._active, self.basalDendrites.root.value ))
        next(self.basalDendrites.computeGen)
        if self.active:
            self.basalDendrites.reset()
            self.proximalDendrites.reset()

        self._activity = (self._active + self.activity)*.5
        # print("First compute")
        yield self._active
        # print("second compute")
        #proximal only provide bias but investigate if they play role in spiking
        # if self.bias >= self.threshold:
            # self._active = 1
            # self.history[1].append((self._active, self.proximalDendrites.root.value ))
            # self.fire()
        # else:
            # self._active = 0
        self.proximalDendrites.computeGen = self.proximalDendrites.compute()
        
        self.history[1].append((self._active, self.proximalDendrites.root.value ))

        yield None
        
        # self.distalDendrites.compute()
        # self.threshold = 0.6*(self.distalDendrites.levels)
        # if self.distalDendrites.root.value > self.threshold:
        #     self._active = 1
        # else:
        #     self._active = 0
        # self.history[2].append((self._active, self.distalDendrites.root.value ))
        # self.fire(self.distalDendrites)

    # def fire(self): #depolarize
    #     self.basalDendrites.reset()
        # self.proximalDendrites.reset()
        


class MiniColumn:
    def __init__(self, numNeurons, inputSDR = None, indx=None, activeNeuronsSDR = None):
        self.numNeurons = numNeurons
        self.inputSDR = inputSDR
        self.neurons = []
        self.indx = indx
        self._active = 0
        self.activeNeuronsSDR = activeNeuronsSDR
        if self.activeNeuronsSDR == None:
            print("You forgot to provide SDR for active Neurons.\nDont forget to register activeNeuronsSDR at later point.")
        else:
            for i in range(numNeurons):
                self.neurons.append(Neuron(inputSDR = self.inputSDR, activeNeuronsSDR = self.activeNeuronsSDR, indx=i))
    
    def compute(self):
        if self.activeNeuronsSDR == None:
            raise Exception("Provide active Neurons SDR with 'size' and 'numActiveBits' parameters")
        tmp = []
        computegens = []
        activity = []
        
        # Create compute generator objects for parallel processing

        for neuron in self.neurons:
            computegens.append(neuron.compute())
        
        # for each neuron compute basalDendrites output
        # remember basalDendrites output is driven by proximal dendrites computation as bias
        # if proximal is absent it serves as a spatial pooler

        for i, neuron in enumerate(self.neurons):
            _active = next(computegens[i])
            activity.append(_active)
        for i, neuron in enumerate(self.neurons):
            if activity[i]:
                tmp.append(neuron.indx)
        tmp.sort(key=lambda x: neuron.response, reverse=True)
        self.activeNeuronsSDR._curSDR = tmp

        # for i, neuron in enumerate(self.neurons):
        #     if activity[i]:
        #         if neuron.indx in self.activeNeuronsSDR.curSDR:
        #             self._active = 1
        #         else: 
        #             self._active = 0

        for i, neuron in enumerate(self.neurons):
            next(computegens[i])

    def getOutputSDR(self):
        return self.activeNeuronsSDR.curSDR


class Layer23:
    def __init__(self, numMiniColumns, numNeurons, miniColumnsSDR = None, inputSDR = None):
        self.numMiniColumns = numMiniColumns
        self.inputSDR = inputSDR
        self.miniColumnsSDR = SDR(self.numMiniColumns, 10, type = "miniColumn") if miniColumnsSDR == None else miniColumnsSDR
        self.miniColumns = []
        self.numNeurons = numNeurons
        self.activeNeuronsSDRs = [SDR(self.numNeurons, 10, type="activeNeuronsSDR") for i in range(self.numMiniColumns)]
        for i in range(self.numMiniColumns):
            self.miniColumns.append(MiniColumn(self.numNeurons ,inputSDR = self.inputSDR, indx = i, activeNeuronsSDR = self.activeNeuronsSDRs[i]))

    def compute(self):
        self.miniColumns.sort(key=lambda x: max([x.neurons[i].response for i in x.getOutputSDR()]) if x.getOutputSDR() else 0, reverse=True)
        # self.miniColumnsSDR._curSDR = [i.indx for i in self.miniColumns]
        for i in self.miniColumns[:10]:
            i.compute()
        self.miniColumnsSDR._curSDR = [i.activeNeuronsSDR.curSDR for i in self.miniColumns]

    def getOutputSDR(self):
        return self.miniColumnsSDR._curSDR
