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
            # Hard process and Higgs decay are already defined in the LHE file.
            # Examples:
            #   pp -> pp H, H -> b bbar
            #   pp -> pp H, H -> gamma gamma
            #
            # Do not let PYTHIA generate a new hard process.
            'ProcessLevel:all = off',

            # Let PYTHIA perform showering from the LHE partons.
            'PartonLevel:all = on',

            # Let PYTHIA perform hadronization, fragmentation and decays.
            # This is needed for H -> b bbar, where b quarks must hadronize.
            # For H -> gamma gamma, photons are passed through, but the same
            # hadronizer configuration is still safe for the event treatment.
            'HadronLevel:all = on',
        ),

        # No jetMatching block is included here.
        # It should not be used for this exclusive Higgs sample.
        parameterSets = cms.vstring(
            'pythia8CommonSettings',
            'pythia8CP5Settings',
            'pythia8PSweightsSettings',
            'lheInput'
        )
    )
)

