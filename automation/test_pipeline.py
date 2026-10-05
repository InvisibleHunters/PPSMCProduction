import json, pathlib, shlex, subprocess, tempfile, unittest
from unittest.mock import patch
import pps_pipeline as p

class PipelineTest(unittest.TestCase):
    def test_chain_failure_resume_both_years(self):
        for year in ('2017','2018'):
            with self.subTest(year=year), tempfile.TemporaryDirectory() as d:
                root=pathlib.Path(d)
                cfg=json.loads((p.HERE/'config.example.json').read_text())
                cfg.update(year=year, launcher=['fake'])
                for key in ('work_root','cmssw_root','watch_dir'):
                    cfg[key]=str(root/key); pathlib.Path(cfg[key]).mkdir()
                cfg['premix_list']=str(root/'premix.txt'); (root/'premix.txt').write_text('/store/a.root\n/store/b.root\n')
                cfg['proxy']=str(root/'proxy')
                cp=root/'config.json'; cp.write_text(json.dumps(cfg)); cfg=p.settings(cp)
                for r in cfg['recipes']:
                    (pathlib.Path(cfg['cmssw_root'])/r['release']/'src').mkdir(parents=True,exist_ok=True)
                lhe=root/'test.lhe'; lhe.write_text('<LesHouchesEvents>test</LesHouchesEvents>')
                calls=[]; fail=[True]
                def fake_run(argv, **kwargs):
                    script=pathlib.Path(argv[-1]); stage=script.stem
                    text=script.read_text()
                    driver=shlex.split(next(line for line in text.splitlines() if line.startswith('cmsDriver.py')))
                    inp=driver[driver.index('--filein')+1][5:]
                    self.assertTrue(pathlib.Path(inp).is_file())
                    out=pathlib.Path(driver[driver.index('--fileout')+1][5:])
                    self.assertIn('cmsRun ',text)
                    calls.append(stage)
                    if stage=='3-premix' and fail[0]:
                        fail[0]=False
                        raise subprocess.CalledProcessError(1,argv)
                    if stage=='3-premix':
                        self.assertNotIn('dbs:',text)
                        self.assertIn('/store/b.root',text)
                    out.write_bytes(b'fake ROOT')
                with patch.object(p.subprocess,'run',side_effect=fake_run):
                    with self.assertRaises(subprocess.CalledProcessError): p.run(cfg,lhe)
                    self.assertEqual(calls,['1-lhe','1-gen','2-sim','3-premix'])
                    p.run(cfg,lhe)
                    self.assertEqual(calls,['1-lhe','1-gen','2-sim','3-premix','3-premix','4-hlt','5-reco','6-miniaod'])
                    n=len(calls); p.run(cfg,lhe); self.assertEqual(n,len(calls))
                state=json.loads(next((root/'work_root'/'jobs').glob('*/status.json')).read_text())
                self.assertEqual(state['state'],'complete')
                self.assertEqual(len(state['done']),7)

    def test_watch_baseline_and_ready_marker(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); incoming=root/'incoming'; incoming.mkdir()
            cfg={'work_root':str(root/'work'),'watch_dir':str(incoming),'poll_seconds':0}
            old=incoming/'old.lhe'; old.write_text('old'); (incoming/'old.lhe.ready').touch()
            p.watch(cfg,True)
            new=incoming/'new.lhe'; new.write_text('new')
            with patch.object(p,'run') as run, patch.object(p.time,'sleep',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): p.watch(cfg)
                run.assert_not_called()
            (incoming/'new.lhe.ready').touch()
            with patch.object(p,'run') as run, patch.object(p.time,'sleep',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): p.watch(cfg)
                run.assert_called_once_with(cfg,new)
            with patch.object(p,'run') as run, patch.object(p.time,'sleep',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt): p.watch(cfg)
                run.assert_not_called()
if __name__=='__main__': unittest.main()
