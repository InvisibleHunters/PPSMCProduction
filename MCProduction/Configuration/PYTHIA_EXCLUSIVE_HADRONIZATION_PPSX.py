import FWCore.ParameterSet.Config as cms

from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.PSweightsPythia.PythiaPSweightsSettings_cfi import *

generator = cms.EDFilter(
    "Pythia8HadronizerFilter",

    pythiaPylistVerbosity = cms.untracked.int32(1),
    filterEfficiency = cms.untracked.double(1.0),
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    comEnergy = cms.double(13000.0),
    maxEventsToPrint = cms.untracked.int32(0),

    PythiaParameters = cms.PSet(

        pythia8CommonSettingsBlock,
        pythia8CP5SettingsBlock,
        pythia8PSweightsSettingsBlock,

        processParameters = cms.vstring(

            # Keep Pythia processing the LHE hard event.
            'ProcessLevel:all = on',

            # Enable the parton-level stage, but configure it explicitly
            # for an exclusive pp -> p + central system + p event.
            'PartonLevel:all = on',

            # No MPI / underlying event for the exclusive topology.
            'PartonLevel:MPI = off',

            # No ISR from the incoming exclusive system.
            'PartonLevel:ISR = off',

            # CRITICAL for an LHE event containing outgoing intact protons:
            # do not construct ordinary pp beam remnants.
            'PartonLevel:Remnants = off',

            # Keep final-state radiation.
            # Needed especially for H -> b bbar.
            'PartonLevel:FSR = on',

            # Hadronization / fragmentation / unstable-particle decays.
            # Needed for H -> b bbar showering and B-hadron production.
            'HadronLevel:all = on',

            # The exclusive LHE contains intact outgoing protons and is not
            # a standard inclusive pp event. Disable Pythia's strict event
            # consistency check for this special topology.
            'Check:event = off',
        ),

        parameterSets = cms.vstring(
            'pythia8CommonSettings',
            'pythia8CP5Settings',
            'pythia8PSweightsSettings',
            'processParameters'
        )
    )
)
