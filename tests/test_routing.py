#!/usr/bin/env python3
"""Exercise generated rule order on representative domains and IPs, offline."""
from __future__ import annotations
import fnmatch, ipaddress, json, pathlib, sys, yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
DIST=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist'
GROUPS=['Proxy','Intelligence','Telegram','YouTube','Google','BiliBili','GlobalMedia','Emby']
CASES=[('chatgpt.com','Intelligence'),('claude.ai','Intelligence'),('gemini.google.com','Intelligence'),('api.deepseek.com','Intelligence'),('grok.com','Intelligence'),('www.perplexity.ai','Intelligence'),('copilot.microsoft.com','Intelligence'),('t.me','Telegram'),('www.youtube.com','YouTube'),('www.google.com','Google'),('www.bilibili.com','BiliBili'),('www.netflix.com','GlobalMedia'),('www.disneyplus.com','GlobalMedia'),('open.spotify.com','GlobalMedia'),('www.tiktok.com','GlobalMedia'),('emby.media','Emby'),('www.apple.com.cn','DIRECT'),('www.icloud.com.cn','DIRECT'),('www.baidu.com','DIRECT'),('192.168.27.8','DIRECT'),('unmatched-name.example','Proxy')]
MAP={'HOST':'DOMAIN','HOST-SUFFIX':'DOMAIN-SUFFIX','HOST-KEYWORD':'DOMAIN-KEYWORD','HOST-WILDCARD':'DOMAIN-WILDCARD','IP6-CIDR':'IP-CIDR6'}
class Matcher:
 def __init__(self, lines):
  self.exact=set();self.suffix=set();self.keyword=[];self.wild=[];self.network=[]
  for line in lines:
   a=line.strip().split(',')
   if len(a)<2:continue
   k=MAP.get(a[0].upper(),a[0].upper());v=a[1].lower()
   if k=='DOMAIN':self.exact.add(v)
   elif k=='DOMAIN-SUFFIX':self.suffix.add(v)
   elif k=='DOMAIN-KEYWORD':self.keyword.append(v)
   elif k=='DOMAIN-WILDCARD':self.wild.append(v)
   elif k in ('IP-CIDR','IP-CIDR6'):
    try:self.network.append(ipaddress.ip_network(v,strict=False))
    except ValueError:raise AssertionError('invalid network in generated file')
 def matches(self, target):
  try:ip=ipaddress.ip_address(target)
  except ValueError:ip=None
  if ip is not None:return any(ip.version==n.version and ip in n for n in self.network)
  h=target.lower().rstrip('.')
  if h in self.exact:return True
  labels=h.split('.')
  if any('.'.join(labels[i:]) in self.suffix for i in range(len(labels))):return True
  return any(x in h for x in self.keyword) or any(fnmatch.fnmatchcase(h,x) for x in self.wild)

def compiled(client):
 result=[]
 if client=='mihomo':
  cfg=yaml.safe_load((DIST/'mihomo/config.template.yaml').read_text())
  assert [x['name'] for x in cfg['proxy-groups']]==GROUPS
  assert cfg['dns']['nameserver']==['https://1.1.1.1/dns-query#LOCAL_SNELL']
  lines=cfg['rules'];folder=DIST/'mihomo/sets'
 elif client=='shadowrocket':
  text=(DIST/'shadowrocket/config.template.conf').read_text();blocks={}
  section=None
  for line in text.splitlines():
   if line.startswith('['):section=line.strip('[]');blocks[section]=[]
   elif section:blocks[section].append(line)
  groups=[line.split('=',1)[0].strip() for line in blocks['Proxy Group'] if '=' in line]
  assert groups==GROUPS
  lines=blocks['Rule'];folder=DIST/'shadowrocket/sets'
 else:
  text=(DIST/'quantumult-x/config.template.conf').read_text();blocks={};section=None
  for line in text.splitlines():
   if line.startswith('['):section=line.strip('[]');blocks[section]=[]
   elif section:blocks[section].append(line)
  groups=[line.split('=',1)[1].split(',',1)[0].strip() for line in blocks['policy'] if line.startswith('static =')]
  assert groups==GROUPS
  for entry in blocks['filter_remote']:
   if not entry.startswith('https://'):continue
   name=entry.split(',',1)[0].rsplit('/',1)[-1]
   raw=(DIST/'quantumult-x/sets'/name).read_text().splitlines()
   # Same source has a single policy; inline sources may contain several policies.
   last=None;run=[]
   for line in raw:
    if not line or line.startswith('#'):continue
    parts=line.split(',');p=parts[2];p=p.upper() if p.lower() in ('direct','reject') else p
    if last is not None and p!=last:result.append((Matcher(run),last));run=[]
    last=p;run.append(line)
   if run:result.append((Matcher(run),last))
  result.append((None,'Proxy'))
  return result
 for line in lines:
  line=line.strip()
  if not line or line.startswith('#'):continue
  parts=line.split(',');kind=parts[0]
  if kind in ('MATCH','FINAL'):result.append((None,parts[1]));continue
  if kind=='RULE-SET':
   name=parts[1].rsplit('/',1)[-1]
   if not name.endswith('.list'):name+='.list'
   result.append((Matcher((folder/name).read_text().splitlines()),parts[2]));continue
  result.append((Matcher([line]),parts[2]))
 return result

def check(client):
 rules=compiled(client)
 for target,want in CASES:
  actual=next((policy for matcher,policy in rules if matcher is None or matcher.matches(target)),None)
  if actual!=want:raise AssertionError(f'{client}: {target} -> {actual}, expected {want}')
 print(f'{client}: {len(CASES)} first-match checks passed')

if __name__=='__main__':
 for c in ('quantumult-x','mihomo','shadowrocket'):check(c)
 print('Caution: offline model; native matching, DNS path and actual networking are not verified.')
