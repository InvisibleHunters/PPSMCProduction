# PPS2 cluster: sequential LHE to MiniAOD production

This adds an opt-in runner to the attached repository. All original files, including the Execution bash scripts, are unchanged. Only the automation/ directory is added. recipes.json records the active cmsDriver commands extracted from Execution/2017 and Execution/2018. The runner generates configs and actually calls cmsRun after each generation. It does not source the original shell scripts: their interactive proxy creation, remote downloads and hardcoded inputs are unsuitable for unattended work.

The chain has seven cmsRun invocations: step1 LHE conversion, step1 GEN, step2 SIM, step3 premixing, step4 HLT, step5 RECO, step6 MiniAOD. Step7 PPS and NanoAOD are outside this chain. Each stage activates its campaign-specific release in a fresh EL7 process. Campaign global tags, geometry, beamspot, HLT menu and modifiers come from the uploaded scripts. Only input/output filenames, event counts and the premix file selection change.

## Deployment assumptions

Start on pps2-226-srv3, as user dmf, with shared output under /storage/users/dmf. These example paths are configurable, not verified current cluster paths. This is one sequential worker on one node; it does not distribute jobs across srv1–srv4. Enable only one watcher per configuration. Host Python >=3.9, CVMFS, Apptainer/Singularity and the CMS cmssw-el7 wrapper must be working. Test /storage and proxy visibility inside the container. AFS/EOS paths require their mounts to be visible; the watcher here expects a mounted/local directory, not an EOS URL.

```bash
ssh dmf@pps2-226-srv3
mkdir -p /storage/users/dmf/pps-production/{incoming2018,output2018,proxy,cmssw}
cd /storage/users/dmf/pps-production
unzip PPSMCProduction-with-automation.zip
cp PPSMCProduction-master/automation/config.example.json config2018.json
```

Edit config2018.json to your actual paths. The default launcher runs cmssw-el7 with /storage explicitly bound. Test it:

```bash
/cvmfs/cms.cern.ch/common/cmssw-el7 -B /storage -- bash -c 'cat /etc/redhat-release; ls /storage/users/dmf'
```

Do not run these old releases directly under AlmaLinux 10. For a different container launch command, replace the launcher JSON array; the runner appends `bash /absolute/stage-script.sh`.

## Credentials and premix input

Generate credentials interactively as dmf, before production. Use a lifetime covering the expected job duration and renew before expiry. Do not embed a certificate password in a service. The worker checks for at least one hour remaining before each stage; this does not guarantee the proxy survives a long stage. Remote premix and conditions access must be validated. Kerberos tickets, if your local mounts require them, have a separate lifetime.

```bash
/cvmfs/cms.cern.ch/common/cmssw-el7 -B /storage -- bash -c 'source /cvmfs/cms.cern.ch/cmsset_default.sh; voms-proxy-init --voms cms --hours 96 --out /storage/users/dmf/pps-production/proxy/x509up'
chmod 600 proxy/x509up
```

Prepare an on-disk premix list ONCE, outside production jobs, using the supplied get_files_on_disk.py. Its Rucio environment requires a compatible Python 3; use a working CMS/Rucio environment, not necessarily the old CMSSW Python. Set X509_USER_PROXY before running. For 2018:

```bash
export X509_USER_PROXY=/storage/users/dmf/pps-production/proxy/x509up
python3 PPSMCProduction-master/MCProduction/Execution/2018/get_files_on_disk.py \
  -o premix2018.txt -v -a T2_CH_CERN -- \
  /Neutrino_E-10_gun/RunIISummer20ULPrePremix-UL18_106X_upgrade2018_realistic_v11_L1v1-v2/PREMIX
```

For 2017 use the 2017 helper and dataset:
`/Neutrino_E-10_gun/RunIISummer20ULPrePremix-UL17_106X_mc2017_realistic_v6-v3/PREMIX`.
The list must contain one accessible `/store/...` LFN or `root://...` PFN per line, from the correct year's dataset. The runner gives cmsDriver the first file to avoid a per-job DBS query, then appends the full list to process.mixData.input.fileNames before cmsRun. It does not run the original text-replacement helper.

## Prepare releases once

Use a reviewed current hadronizer file. The archive is stamped August 31, 2026; it is not evidence of the current GitHub version. The runner freezes the local fragment and does not fetch master on each job. Replace the bundled fragment with the version you want before preparation. Avoid changing prepared releases or fragments while jobs are queued; use a new cmssw_root/work_root for a revised production.

```bash
python3 PPSMCProduction-master/automation/prepare.py --config config2018.json \
  --fragment PPSMCProduction-master/MCProduction/Configuration/PYTHIA_EXCLUSIVE_HADRONIZATION_PPSX.py \
  --apply-lhe-fix
```

The 2018 preparation optionally applies the same AndreaBellora LHE topic as your uploaded step1. Apply it once in a fresh area, review the merge/build, and omit the flag on subsequent preparations. The tool provisions:

| Stage | 2017 release | 2018 release |
|---|---|---|
| LHE / GEN | CMSSW_10_6_18 | CMSSW_10_6_21 |
| SIM / premix / RECO | CMSSW_10_6_17_patch1 | CMSSW_10_6_17_patch1 |
| HLT | CMSSW_9_4_14_UL_patch1 | CMSSW_10_2_16_UL |
| MiniAOD | CMSSW_10_6_17_patch1 | CMSSW_10_6_20 |

2017 HLT uses slc7_amd64_gcc630; other stages use slc7_amd64_gcc700.

## Manual run and resume

Set events=10 for the initial validation. Then set events=-1 to process all LHE events. Downstream stages always process all upstream events. Changing the event limit/configuration/input/premix list creates a new job identity.

```bash
python3 PPSMCProduction-master/automation/pps_pipeline.py --config config2018.json \
  run /storage/users/dmf/pps-production/incoming2018/sample.lhe --dry-run
python3 PPSMCProduction-master/automation/pps_pipeline.py --config config2018.json \
  run /storage/users/dmf/pps-production/incoming2018/sample.lhe
```

Dry-run lists source recipes and release choices; it does not validate CMSSW/container/credentials. Runtime scripts contain the rewritten input/output paths. Each job lives in output2018/jobs/<identity>/ with a copy of the LHE, generated configs, stage scripts, logs, ROOT files and status.json. The final output is 6-miniaod.root. cmsRun, nonempty output and edmFileUtil must all succeed before advancing. This validates readability, not physics distributions or expected event yields. Inspect event counts and hadronization on the initial sample. Default campaign random seeds are retained: review seed policy before splitting one sample into independent production chunks.

Re-run the same command after fixing a failure: completed upstream stages are skipped; the failed stage is regenerated, its incomplete output removed, and its log appended. Keep intermediate ROOT files for resume. Do not edit existing inputs in place; publish a new filename for a new sample. If you intentionally change campaign settings, use a fresh production directory.

## Automatically process new files only

Register current files first. They will be ignored, even if they have ready markers:

```bash
python3 PPSMCProduction-master/automation/pps_pipeline.py --config config2018.json init-watch
```

Never rerun init-watch while new files are pending: it registers all current files as already seen. For a new sample, write to a temporary name, close it, rename it to .lhe, then create the marker:

```bash
mv incoming2018/new_masspoint.lhe.part incoming2018/new_masspoint.lhe
touch incoming2018/new_masspoint.lhe.ready
```

The producer must create the marker AFTER closing the final file. The watcher polls every 60 seconds, checks file content against persistent state, and runs each new ready LHE sequentially. Without the marker it waits. Directory polling is used so discovery does not rely on receiving remote filesystem events. Keep filenames simple. `.lhe.gz` is not supported by this watcher; decompress to `.lhe` before publishing.

First test in the foreground:

```bash
python3 PPSMCProduction-master/automation/pps_pipeline.py --config config2018.json watch
```

Then install the service as administrator on srv3 (edit User, WorkingDirectory and ExecStart to match your paths). This service uses dmf's credentials and survives logout:

```bash
sudo cp PPSMCProduction-master/automation/pps-lhe-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pps-lhe-watch.service
sudo systemctl status pps-lhe-watch.service
sudo journalctl -u pps-lhe-watch.service -f
```

Stop automatic processing with `sudo systemctl stop pps-lhe-watch.service`. Stopping also terminates the running stage; its next manual run resumes from the last completed stage. Failed files are recorded and not retried every minute. Fix the cause and run them manually. A successful manual retry is recognized on the next watcher restart after removing that input's entry from watch-state.json's failed mapping (stop the service before editing state). Other queued samples continue after a failure. If the top-level watcher fails, systemd restarts it.

For 2017 create a separate config with year=2017, the 2017 premix list and distinct incoming/output directories. If running two watchers concurrently, budget CPU, RAM and disk separately. This starter package retains all intermediate files and does not split events or schedule across nodes. Once validated, a Condor worker per LHE can distribute the same sequential chain, but a Condor pool should be confirmed before generating a cluster-wide submit setup.

## Validation delivered with this package

Host-side integration tests simulate CMSSW execution to verify input chaining, failure stops, resume, and completed-job deduplication for both years. They do not run CMSSW. Run `python3 -m unittest discover -s PPSMCProduction-master/automation -p 'test_*.py'`. A real 10-event run on your cluster is required before enabling unattended production.
