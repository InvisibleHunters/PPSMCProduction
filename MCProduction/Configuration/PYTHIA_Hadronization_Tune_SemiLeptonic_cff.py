import FWCore.ParameterSet.Config as cms

from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.PSweightsPythia.PythiaPSweightsSettings_cfi import *

generator = cms.EDFilter("Pythia8HadronizerFilter",
    pythiaPylistVerbosity = cms.untracked.int32(1),
    filterEfficiency = cms.untracked.double(1.0),
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    comEnergy = cms.double(13000.0),
    maxEventsToPrint = cms.untracked.int32(0),
    PythiaParameters = cms.PSet(
        pythia8CommonSettingsBlock,
        pythia8CP5SettingsBlock,
        pythia8PSweightsSettingsBlock,
        lheInput = cms.vstring(
            # Hard Process already defined in the LHE file from the Toy MC, hence no need to specify the hadronization of specific quarks.
            #   pp -> pp X H -> bb
            #   pp -> pp X H -> gamma gamma
            # PYTHIA will not create more hard process
            'ProcessLevel:all = off',
            # PYTHIA does parton showering (already included by default, but forcing) 
            'PartonLevel:all = on',
            # PYTHIA does hadronization, fragmentation and decays (already included by default, but forcing)
            'HadronLevel:all = on',
            # Debugging.
            # 'Check:event = off',
        ),
        jetMatching = cms.vstring(
            # Matching useful for MadGraph/MadEvent
            'JetMatching:setMad = off',
            'JetMatching:scheme = 1',
            'JetMatching:merge = on',
            # Jet algo used for the matching
            'JetMatching:jetAlgorithm = 2',
            'JetMatching:etaJetMax = 5.',
            'JetMatching:coneRadius = 1.',
            'JetMatching:slowJetPower = 1',
            # Matching scale in GeV.
            # This must be consistent with the xqcut/qcut choice used
            # when generating the LHE file.
            'JetMatching:qCut = 20.',
            # Matching flavour scheme.
            # Use 5 for a five-flavour scheme, where b quarks are treated
            # as matchable partons.
            'JetMatching:nQmatch = 5',
            # Maximum number of additional matrix-element partons.
            # Use 4 for samples generated as H + 0,1,2,3,4 partons.
            'JetMatching:nJetMax = 4',
            # Common setting used in CMS MLM-matched Pythia8 fragments.
            'JetMatching:doShowerKt = off'
        ),
        parameterSets = cms.vstring('pythia8CommonSettings','pythia8CP5Settings','pythia8PSweightsSettings','lheInput','jetMatching')
    )
)
