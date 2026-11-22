#!/usr/bin/env python3
"""Verify failed downloads/builds cannot replace last-known-good artifacts."""
from pathlib import Path
import hashlib, importlib.util, shutil, sys, tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
 h=hashlib.sha256()
 for f in sorted(p for p in path.rglob('*') if p.is_file()):
  h.update(str(f.relative_to(path)).encode());h.update(f.read_bytes())
 return h.hexdigest()

with tempfile.TemporaryDirectory(prefix='routing-rollback-') as temp:
 root=Path(temp)/'repo'
 shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','.serena','__pycache__','.venv','.sync-*'))
 spec=importlib.util.spec_from_file_location('sync_upstream_test',root/'scripts/sync-upstream.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 cache=root/'sources/cache';dist=root/'dist';before=(digest(cache),digest(dist))
 def fail(*args):raise OSError('simulated network failure')
 try:
  with patch.object(mod,'fetch',side_effect=fail):mod.main()
 except OSError:pass
 else:raise AssertionError('download failure should stop synchronization')
 assert before==(digest(cache),digest(dist)), 'failed download changed prior version'
 def malformed(meta,directory):
  old=(cache/(meta['id']+'.txt')).read_bytes()
  changed=meta['id']=='ai'
  (directory/(meta['id']+'.txt')).write_bytes(old+(b'\nUNKNOWN-RULE,invalid.example\n' if changed else b''))
  return (meta['id'],100,changed,0)
 real_run=mod.subprocess.run
 def quiet_run(*args,**kwargs):
  return real_run(*args,**kwargs,stdout=mod.subprocess.PIPE,stderr=mod.subprocess.PIPE)
 try:
  with patch.object(mod,'fetch',side_effect=malformed), patch.object(mod.subprocess,'run',side_effect=quiet_run):mod.main()
 except Exception:pass
 else:raise AssertionError('invalid source should stop synchronization')
 assert before==(digest(cache),digest(dist)), 'failed build changed prior version'
 assert not (root/'sources/.cache-backup').exists(), 'backup not restored'
 print('Rollback verified: network failure and malformed upstream preserve cache and dist.')
