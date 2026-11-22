#!/usr/bin/env python3
"""Fetch all upstreams transactionally; retain cached data on any failure."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from build import load

UUID_PATTERN=re.compile(rb'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')

def sanitize(raw):
 lines=raw.splitlines(keepends=True)
 omitted=sum(1 for line in lines if UUID_PATTERN.search(line))
 return b''.join(line for line in lines if not UUID_PATTERN.search(line)),omitted

def active(raw):
 text=raw.decode('utf-8-sig')
 return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith(('#',';','//'))]

def fetch(meta,directory):
 path=ROOT/'sources/cache'/f"{meta['id']}.txt";old=path.read_bytes()
 req=Request(meta['upstream_url'],headers={'User-Agent':'misub-routing-updater/1.0'})
 with urlopen(req,timeout=45) as res:
  if res.status!=200:raise RuntimeError(f"{meta['id']}: unexpected HTTP {res.status}")
  raw=res.read(20_000_001)
 if len(raw)>20_000_000:raise RuntimeError(f"{meta['id']}: size limit exceeded")
 raw,omitted=sanitize(raw)
 oldlines=active(old);newlines=active(raw)
 minimum=max(meta['min_rules'],int(len(oldlines)*.7))
 if len(newlines)<minimum:raise RuntimeError(f"{meta['id']}: suspicious rule count {len(newlines)} < {minimum}")
 # Preserve the previous source file if only comments or timestamps changed.
 changed=oldlines!=newlines
 (directory/f"{meta['id']}.txt").write_bytes(raw if changed else old)
 return (meta['id'],len(newlines),changed,omitted)

def main():
 data=load();metas=[m for m in data['remote_rule_sets'] if m['enabled']]
 cache=ROOT/'sources/cache';backup=ROOT/'sources/.cache-backup'
 if backup.exists():raise RuntimeError('cache backup exists; manual inspection required')
 with tempfile.TemporaryDirectory(prefix='.sync-',dir=ROOT/'sources') as temp:
  staged=Path(temp)/'cache';staged.mkdir()
  with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda m:fetch(m,staged),metas))
  omitted={id:n for id,_,_,n in results if n}
  old_omitted=json.loads((cache/'_omitted.json').read_text()) if (cache/'_omitted.json').exists() else {}
  (staged/'_omitted.json').write_text(json.dumps(omitted,sort_keys=True,indent=2)+'\n')
  changed=[id for id,_,different,_ in results if different]
  if omitted!=old_omitted:changed.append('omission-counts')
  if not changed:
   print(f'All {len(results)} upstreams checked; no rule changes.');return
  cache.rename(backup)
  try:
   staged.rename(cache)
   subprocess.run([str(ROOT/'scripts/build')],cwd=ROOT,check=True)
  except BaseException:
   if cache.exists():shutil.rmtree(cache)
   backup.rename(cache)
   raise
  shutil.rmtree(backup)
  print('Updated rule sources:',', '.join(changed))

if __name__=='__main__':main()
