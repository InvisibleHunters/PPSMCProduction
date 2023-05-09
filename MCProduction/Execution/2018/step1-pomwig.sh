#!/bin/bash

# Make voms proxy
voms-proxy-init --voms cms --out $(pwd)/voms_proxy.txt --hours 4
export X509_USER_PROXY=$(pwd)/voms_proxy.txt

export SCRAM_ARCH=slc7_amd64_gcc700

source /cvmfs/cms.cern.ch/cmsset_default.sh
if [ -r CMSSW_10_6_21/src ] ; then
  echo release CMSSW_10_6_21 already exists
else
  scram p CMSSW CMSSW_10_6_21
fi
cd CMSSW_10_6_21/src
eval `scram runtime -sh`

# Download fragment from McM
curl -s -k https://raw.githubusercontent.com/InvisibleHunters/PPSMCProduction/master/MCProduction/Configuration/POMWIG_SingleDiffractiveMinusZee_M20_13TeV_cff.py --retry 3 --create-dirs -o Configuration/GenProduction/python/pomwig-zee-fragment.py
[ -s Configuration/GenProduction/python/pomwig-zee-fragment.py ] || exit $?;
scram b
cd ../..

EVENTS=100

# cmsDriver command
cmsDriver.py Configuration/GenProduction/python/pomwig-zee-fragment.py --python_filename Pomwig-Zee_cfg.py --eventcontent RAWSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN --fileout file:PPS-RunIISummer20UL18GEN-00001.root --conditions 106X_upgrade2018_realistic_v4 --beamspot Realistic25ns13TeVEarly2018Collision --step GEN --geometry DB:Extended --era Run2_2018 --no_exec --mc -n $EVENTS || exit $?;
