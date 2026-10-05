#!/usr/bin/env python3
"""Provision campaign releases once, outside the automatic worker."""
import argparse, pathlib, shlex, subprocess
from pps_pipeline import settings, HERE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--config',type=pathlib.Path,required=True)
p.add_argument('--fragment',type=pathlib.Path,required=True,help='Reviewed hadronizer fragment to freeze into the release')
p.add_argument('--apply-lhe-fix',action='store_true',help='Apply the 2018 LHE fix used by the supplied step1 script')
a=p.parse_args(); cfg=settings(a.config.resolve()); fragment=a.fragment.resolve()
if not fragment.is_file(): raise SystemExit('Fragment missing')
root=pathlib.Path(cfg['cmssw_root']); root.mkdir(parents=True,exist_ok=True)
seen=set()
for r in cfg['recipes']:
    release=r['release']
    if release in seen: continue
    seen.add(release)
    src=root/release/'src'
    lines=['#!/bin/bash','set -eo pipefail','export SCRAM_ARCH='+shlex.quote(r['arch']), 'source /cvmfs/cms.cern.ch/cmsset_default.sh','cd '+shlex.quote(str(root)), 'if [ ! -d '+shlex.quote(str(src))+' ]; then scram p CMSSW '+shlex.quote(release)+'; fi','cd '+shlex.quote(str(src)), 'eval "$(scram runtime -sh)"']
    if r['stage']=='1-lhe':
        if cfg['year']=='2018' and a.apply_lhe_fix:
            lines+=['git cms-init','git cms-merge-topic AndreaBellora:CMSSW_10_6_21_fixLHE']
        target=pathlib.Path(r['command'][1])
        lines+=['mkdir -p '+shlex.quote(str(target.parent)),'cp '+shlex.quote(str(fragment))+' '+shlex.quote(str(target))]
    lines+=['scram b -j 4']
    script=root/('prepare-'+release+'.sh'); script.write_text('\n'.join(lines)+'\n')
    subprocess.run(cfg['launcher']+['bash',str(script)],check=True)
print('Releases prepared. Validate a small sample before enabling the watcher.')
