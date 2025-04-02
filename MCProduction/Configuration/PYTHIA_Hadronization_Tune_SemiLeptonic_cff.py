import FWCore.ParameterSet.Config as cms

from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.PSweightsPythia.PythiaPSweightsSettings_cfi import *

generator = cms.EDFilter("Pythia8HadronizerFilter",
    pythiaPylistVerbosity = cms.untracked.int32(1),
    filterEfficiency = cms.untracked.double(1.0),
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    comEnergy = cms.double(13000.0),  # LHC collision energy
    maxEventsToPrint = cms.untracked.int32(0),
    PythiaParameters = cms.PSet(
        pythia8CommonSettingsBlock,
        pythia8CP5SettingsBlock,
        pythia8PSweightsSettingsBlock,
        # Skip hard process generation (use LHE input)
        skip_hadronization = cms.vstring(
            'ProcessLevel:all = off',  # Disable Pythia hard process generation
            'Check:event = off'        # Skip event validation checks
        ),
        # Enable semi-leptonic decays for b- and c-hadrons
        lepton_in_jets = cms.vstring(
            '6:all = on',                # Enable all bottom quark decays
            '-6:all = on',               # Enable all bottom quark decays
            '4:all = on',                # Enable all charm quark decays
            '-4:all = on',                # Enable all charm quark decays
            # Semi-leptonic decays for B-mesons (b-hadrons)
            #'B+:addChannel = 1.0 e+ nu_e D0'     
            #'B+:addChannel = 1.0 mu+ nu_mu D0'   
            #'B+:addChannel = 1.0 tau+ nu_tau D0'
            '521:addChannel = 1 1.0 91 -11 12 421',
            '521:addChannel = 1 1.0 91 -13 14 421',
            '521:addChannel = 1 1.0 91 -15 16 421',
            # Semi-leptonic decays for D-mesons (c-hadrons)
            #'D+:addChannel = 1.0 e+ nu_e K-',     
            #'D+:addChannel = 1.0 mu+ nu_mu K-',
            '411:addChannel = 1 1.0 91 -11 12 -321',
            '411:addChannel = 1 1.0 91 -13 14 -321',
            # General decay settings for detector acceptance
            'ParticleDecays:limitTau0 = on',      # Enable lifetime-based decays
            'ParticleDecays:tauMax = 10.0'        # Decay within ~10 mm of detector volume
        ),
        # Jet matching parameters for LHE input consistency
        jet_matching = cms.vstring(
            'JetMatching:setMad = off',
            'JetMatching:scheme = 1',
            'JetMatching:merge = on',
            'JetMatching:jetAlgorithm = 2',
            'JetMatching:etaJetMax = 5.',
            'JetMatching:coneRadius = 1.',
            'JetMatching:slowJetPower = 1',
            'JetMatching:qCut = 20.',          # Merging scale (GeV)
            'JetMatching:nQmatch = 5',         # Matching flavor scheme (5-flavor)
            'JetMatching:nJetMax = 4'          # Max number of partons in Born matrix element
        ),
        parameterSets = cms.vstring('skip_hadronization','pythia8CommonSettings','pythia8CP5Settings','pythia8PSweightsSettings', 'lepton_in_jets', 'jet_matching')
    )
)
