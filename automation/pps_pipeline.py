#!/usr/bin/env python3
"""Sequential LHE -> MiniAOD worker and ready-file watcher; host Python 3."""
import argparse, contextlib, fcntl, hashlib, json, os, pathlib, shlex, shutil, subprocess, time
HERE = pathlib.Path(__file__).resolve().parent

def write_json(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2)+'\n')
    tmp.replace(path)

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()

@contextlib.contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path,'a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield

def option(cmd, flag, value):
    cmd[cmd.index(flag)+1] = str(value)

def settings(path):
    cfg=json.loads(path.read_text())
    for key in ('work_root','cmssw_root','proxy','premix_list','watch_dir'):
        cfg[key]=str(pathlib.Path(cfg[key]).expanduser().resolve())
    cfg['year']=str(cfg['year'])
    if cfg['year'] not in ('2017','2018'): raise ValueError('year must be 2017 or 2018')
    cfg['premix_sha256']=digest(pathlib.Path(cfg['premix_list']))
    cfg['recipes']=json.loads((HERE/'recipes.json').read_text())[cfg['year']]
    return cfg

def run(cfg, lhe, dry=False):
    lhe=lhe.resolve()
    if not lhe.is_file() or not lhe.stat().st_size: raise ValueError('LHE input missing or empty')
    identity=hashlib.sha256((str(lhe)+digest(lhe)+json.dumps(cfg,sort_keys=True)).encode()).hexdigest()
    job=pathlib.Path(cfg['work_root'])/('jobs/'+identity)
    if dry:
        print('Input:',lhe,'\nJob:',job)
        for r in cfg['recipes']: print(r['stage'],r['release'],shlex.join(r['command']))
        return
    # Deliberately serialize all jobs on one worker, including manual requests.
    with lock(pathlib.Path(cfg['work_root'])/'worker.lock'):
        job.mkdir(parents=True,exist_ok=True)
        status=job/'status.json'
        state=json.loads(status.read_text()) if status.exists() else {'input':str(lhe),'identity':identity,'done':[]}
        if state.get('state')=='complete' and all((job/(r['stage']+'.root')).is_file() and (job/(r['stage']+'.root')).stat().st_size for r in cfg['recipes']):
            print('Already complete:',job,flush=True); return
        if not (job/'input.lhe').exists(): shutil.copyfile(lhe,job/'input.lhe')
        if digest(job/'input.lhe') != digest(lhe): raise RuntimeError('Input changed while copying; publish it atomically')
        previous=job/'input.lhe'
        try:
            for r in cfg['recipes']:
                stage=r['stage']; cmd=list(r['command'])
                output=job/(stage+'.root'); config=job/(stage+'_cfg.py')
                if stage in state['done'] and output.exists() and output.stat().st_size:
                    previous=output; continue
                option(cmd,'--python_filename',config)
                option(cmd,'--filein','file:'+str(previous))
                option(cmd,'--fileout','file:'+str(output))
                option(cmd,'-n',cfg['events'] if stage=='1-lhe' else -1)
                tail=''
                if stage=='3-premix':
                    files=[s.strip() for s in pathlib.Path(cfg['premix_list']).read_text().splitlines() if s.strip() and not s.startswith('#')]
                    if not files: raise ValueError('Premix list is empty')
                    option(cmd,'--pileup_input',files[0])
                    tail='\nprocess.mixData.input.fileNames = cms.untracked.vstring()\n'
                    for start in range(0,len(files),100):
                        tail+='process.mixData.input.fileNames.extend('+repr(files[start:start+100])+')\n'
                # Recompute this stage and everything downstream if its output was lost.
                stage_order=[x['stage'] for x in cfg['recipes']]
                state['done']=[s for s in state['done'] if stage_order.index(s)<stage_order.index(stage)]
                src=pathlib.Path(cfg['cmssw_root'])/r['release']/'src'
                if not src.is_dir(): raise RuntimeError('Prepare release first: '+str(src))
                script=job/(stage+'.sh')
                script.write_text('#!/bin/bash\nset -eo pipefail\nexport SCRAM_ARCH='+shlex.quote(r['arch'])+'\nexport X509_USER_PROXY='+shlex.quote(cfg['proxy'])+'\nsource /cvmfs/cms.cern.ch/cmsset_default.sh\ncd '+shlex.quote(str(src))+'\neval "$(scram runtime -sh)"\ncd '+shlex.quote(str(job))+'\nexport SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_CH_CERN\nexport CMS_PATH=/storage/pps/shared/pps-production/cms-site\nvoms-proxy-info --file "$X509_USER_PROXY" --exists --valid 1:00\n'+shlex.join(cmd)+'\n'+('cat >> '+shlex.quote(str(config))+" <<'PPS_CUSTOMIZATION'\n"+tail+'PPS_CUSTOMIZATION\n' if tail else '')+'cmsRun '+shlex.quote(str(config))+'\ntest -s '+shlex.quote(str(output))+'\nedmFileUtil '+shlex.quote(str(output))+'\n')
                state.update(state='running',stage=stage); write_json(status,state)
                print('Running',stage,'in',job,flush=True)
                # Remove incomplete output on retry; keep completed upstream outputs.
                output.unlink(missing_ok=True)
                with open(job/(stage+'.log'),'a') as log:
                    subprocess.run(cfg['launcher']+['bash',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True)
                state['done'].append(stage); write_json(status,state); previous=output
            state.update(state='complete',output=str(previous)); write_json(status,state)
            print('MiniAOD:',previous,flush=True)
        except Exception as exc:
            state.update(state='failed',error=str(exc)); write_json(status,state)
            raise

def candidates(cfg):
    folder=pathlib.Path(cfg['watch_dir'])
    if not folder.is_dir(): raise ValueError('Watch directory is missing: '+str(folder))
    return sorted(folder.glob('*.lhe'))

def watch(cfg, initialize=False):
    root=pathlib.Path(cfg['work_root']); root.mkdir(parents=True,exist_ok=True)
    with lock(root/'watch.lock'):
        db=root/'watch-state.json'
        state=json.loads(db.read_text()) if db.exists() else {'seen':{},'failed':{}}
        if initialize:
            for p in candidates(cfg): state['seen'][str(p)] = digest(p)
            write_json(db,state); print('Existing LHE files registered; new files will be processed.'); return
        if not db.exists(): raise RuntimeError('First run init-watch to establish the existing-file baseline')
        while True:
            for p in candidates(cfg):
                key=str(p); ready=pathlib.Path(key+'.ready')
                if not ready.exists(): continue
                h=digest(p)
                if state['seen'].get(key)==h or state['failed'].get(key)==h: continue
                try:
                    run(cfg,p)
                    state['seen'][key]=h; state['failed'].pop(key,None)
                except Exception as exc:
                    print('FAILED',p,exc,flush=True); state['failed'][key]=h
                write_json(db,state)
            time.sleep(cfg.get('poll_seconds',60))

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--config',type=pathlib.Path,required=True)
    sub=a.add_subparsers(dest='action',required=True)
    r=sub.add_parser('run'); r.add_argument('lhe',type=pathlib.Path); r.add_argument('--dry-run',action='store_true')
    sub.add_parser('init-watch'); sub.add_parser('watch')
    args=a.parse_args(); cfg=settings(args.config.resolve())
    if args.action=='run': run(cfg,args.lhe,args.dry_run)
    else: watch(cfg,args.action=='init-watch')
if __name__=='__main__': main()
