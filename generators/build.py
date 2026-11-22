#!/usr/bin/env python3
"""Compile the public routing schema and cached, attributed rule sets."""
from __future__ import annotations
import collections, hashlib, ipaddress, json, os, pathlib, re, shutil, subprocess, sys, tempfile
import jsonschema, yaml

ROOT=pathlib.Path(__file__).resolve().parents[1]
GROUPS=['Proxy','Intelligence','Telegram','YouTube','Google','BiliBili','GlobalMedia','Emby']
CLIENTS=['quantumult-x','mihomo','shadowrocket']
BASE='https://raw.githubusercontent.com/jxtomxu/misub-routing/main/dist'
KINDS={'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','IP-CIDR','IP-CIDR6','IP-ASN','USER-AGENT','PROCESS-NAME','URL-REGEX','OR'}
SUPPORTED={
 'quantumult-x':{'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','IP-CIDR','IP-CIDR6','IP-ASN','USER-AGENT'},
 'mihomo':{'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','IP-CIDR','IP-CIDR6','IP-ASN','PROCESS-NAME'},
 'shadowrocket':{'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','IP-CIDR','IP-CIDR6','IP-ASN','USER-AGENT'},
}

def load():
 data=yaml.safe_load((ROOT/'schema/routing.yaml').read_text())
 schema=json.loads((ROOT/'schema/routing.schema.json').read_text())
 jsonschema.Draft202012Validator.check_schema(schema)
 jsonschema.validate(data,schema)
 if [x['name'] for x in data['groups']]!=GROUPS: raise ValueError('groups must be exactly the eight required groups, in order')
 ids=[s['id'] for s in data['remote_rule_sets']]
 if len(ids)!=len(set(ids)): raise ValueError('duplicate rule-set id')
 seen=set(); priorities=set()
 for r in data['rules']:
  if r['id'] in seen or r['priority'] in priorities: raise ValueError('duplicate rule id or priority: '+r['id'])
  seen.add(r['id']); priorities.add(r['priority'])
  if r['policy'] not in set(GROUPS+['DIRECT','REJECT']): raise ValueError('unknown policy: '+r['policy'])
  if r['type']=='RULE-SET' and r['value'] not in ids: raise ValueError('unknown rule set: '+r['value'])
  if r['type'] in {'IP-CIDR','IP-CIDR6'}: ipaddress.ip_network(r['value'],strict=False)
  if r['type']=='FINAL' and r['value']: raise ValueError('FINAL must have empty value')
 if sorted((r for r in data['rules'] if r['enabled']),key=lambda x:x['priority'])[-1]['type']!='FINAL': raise ValueError('FINAL must be last')
 for d in data['dns']['overrides']:
  if d['rule_set'] not in ids: raise ValueError('unknown DNS rule set')
 return data

def parse_set(meta):
 path=ROOT/'sources/cache'/f"{meta['id']}.txt"
 raw=path.read_bytes(); lines=raw.decode('utf-8-sig').splitlines(); out=[]
 for line in lines:
  line=line.strip()
  if not line or line.startswith(('#',';','//')): continue
  if meta['source_format']=='domain-set':
   kind='DOMAIN-SUFFIX' if line.startswith('.') else 'DOMAIN'; value=line.lstrip('.'); opts=[]
  else:
   parts=[p.strip() for p in line.split(',')]; kind=parts[0].upper()
   if kind not in KINDS: raise ValueError(f"{meta['id']}: unknown rule type {kind}")
   if len(parts)<2 or not parts[1]: raise ValueError(f"{meta['id']}: malformed rule")
   value=parts[1]; opts=parts[2:]
   if kind=='OR': value=line[len(parts[0])+1:];opts=[]
  if not value or '\n' in value or '\r' in value: raise ValueError('bad value')
  if kind in {'IP-CIDR','IP-CIDR6'}: ipaddress.ip_network(value,strict=False)
  out.append((kind,value,tuple(opts)))
 if len(out)<meta['min_rules']: raise ValueError(f"{meta['id']}: only {len(out)} source rules, minimum {meta['min_rules']}")
 return out,hashlib.sha256(raw).hexdigest()

def convert(rule, client, policy=None):
 kind,value,opts=rule
 if kind not in SUPPORTED[client]: return None
 if client=='quantumult-x':
  kind={'DOMAIN':'HOST','DOMAIN-SUFFIX':'HOST-SUFFIX','DOMAIN-KEYWORD':'HOST-KEYWORD','DOMAIN-WILDCARD':'HOST-WILDCARD','IP-CIDR6':'IP6-CIDR'}.get(kind,kind)
 elif client=='shadowrocket' and kind=='IP-CIDR6': kind='IP-CIDR'
 result=[kind,value]
 if policy is not None: result.append(policy.lower() if client=='quantumult-x' and policy in ('DIRECT','REJECT') else policy)
 # Supported no-resolve in the emitted targets. Keep it only on IP rules.
 if kind in {'IP-CIDR','IP-CIDR6','IP6-CIDR','IP-ASN'} and 'no-resolve' in opts: result.append('no-resolve')
 return ','.join(result)

def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf8')

def render(data, stage):
 metas={s['id']:s for s in data['remote_rule_sets'] if s['enabled']}; parsed={}; report={'sources':{},'unsupported':{c:{} for c in CLIENTS},'duplicates':{c:{} for c in CLIENTS}}
 for id,meta in metas.items():
  parsed[id],sha=parse_set(meta);report['sources'][id]={'count':len(parsed[id]),'sha256':sha,'url':meta['upstream_url'],'attribution':meta['attribution']}
 omissions=ROOT/'sources/cache/_omitted.json'
 report['uuid_domain_omissions']=json.loads(omissions.read_text()) if omissions.exists() else {}
 routes=sorted([r for r in data['rules'] if r['enabled']],key=lambda x:x['priority'])
 seen_rules={};same_policy=0;different_policy=0
 for route in routes:
  if route['type']!='RULE-SET' or route['value'] not in parsed:continue
  for item in parsed[route['value']]:
   if item in seen_rules and seen_rules[item][0]!=route['value']:
    if seen_rules[item][1]==route['policy']:same_policy+=1
    else:different_policy+=1
   else:seen_rules.setdefault(item,(route['value'],route['policy']))
 report['cross_source_duplicates']={'same_policy':same_policy,'different_policy':different_policy,'handling':'preserved to retain first-match priority'}
 report['configuration_limitations']={'quantumult-x':'rule-set based DNS override is not generated','shadowrocket':'DNS host overrides and rule-set based DNS overrides are not generated'}
 defaults={g['name']:g['default'] for g in data['groups']}
 if defaults['Proxy']!='SELECT_NODE' or any(defaults[g] not in ('Proxy','DIRECT') for g in GROUPS[1:]):raise ValueError('unsupported group default')
 for host in data['hosts']:
  if 'ip' in host:ipaddress.ip_address(host['ip'])
  if host.get('rule_set') and host['rule_set'] not in parsed:raise ValueError('unknown Host rule set')
 for name,options in data['client_overrides'].items():
  allowed={'quantumult-x':{'dns_lines'},'mihomo':{'dns','tun'},'shadowrocket':{'general_lines'}}[name]
  if set(options)-allowed:raise ValueError('unsupported client override in '+name)
 for client in CLIENTS:
  out=stage/client; (out/'sets').mkdir(parents=True)
  qx_refs=[]; shadow_rules=[]; mh_rules=[]; mh_providers={}; pending=[]; stage_number=0
  def flush():
   nonlocal stage_number,pending
   if not pending:return
   id=f'inline-{stage_number:02d}'; stage_number+=1
   if client=='quantumult-x':
    values=[convert((r['type'],r['value'],('no-resolve',) if r['options'].get('no_resolve') else ()),client,r['policy']) for r in pending if r['type']!='FINAL']
    values=[v for v in values if v]
    if values:
     write(out/'sets'/f'{id}.list','\n'.join(values)+'\n'); qx_refs.append((id,None))
   elif client=='mihomo':
    for r in pending:
     if r['type']=='FINAL':mh_rules.append('MATCH,'+r['policy']);continue
     rule=(r['type'],r['value'],('no-resolve',) if r['options'].get('no_resolve') else ())
     text=convert(rule,client,r['policy'])
     if text: mh_rules.append(text)
   else:
    for r in pending:
     if r['type']=='FINAL':shadow_rules.append('FINAL,'+r['policy']);continue
     text=convert((r['type'],r['value'],('no-resolve',) if r['options'].get('no_resolve') else ()),client,r['policy'])
     if text: shadow_rules.append(text)
   pending=[]
  for r in routes:
   if r['type']!='RULE-SET':pending.append(r);continue
   flush(); id=r['value']; meta=metas.get(id)
   if not meta: raise ValueError('disabled rule set referenced: '+id)
   if client not in meta['target_formats']:raise ValueError('rule-set lacks target '+client+': '+id)
   seen=set(); lines=[]; skipped=collections.Counter(); duplicate=0
   for item in parsed[id]:
    s=convert(item,client,r['policy'] if client=='quantumult-x' else None)
    if s is None:skipped[item[0]]+=1;continue
    if s in seen:duplicate+=1;continue
    seen.add(s);lines.append(s)
   if not lines:raise ValueError(f'{client}/{id} is empty')
   report['unsupported'][client][id]=dict(skipped);report['duplicates'][client][id]=duplicate
   write(out/'sets'/f'{id}.list',f"# Source: {meta['upstream_url']}\n# Attribution: {meta['attribution']}\n"+'\n'.join(lines)+'\n')
   if client=='quantumult-x': qx_refs.append((id,r['policy']))
   elif client=='shadowrocket':shadow_rules.append(f'RULE-SET,{BASE}/shadowrocket/sets/{id}.list,{r["policy"]}')
   else:
    mh_providers[id]={'type':'http','behavior':'classical','format':'text','url':f'{BASE}/mihomo/sets/{id}.list','path':f'./rules/{id}.list','interval':meta['update_interval']}
    mh_rules.append(f'RULE-SET,{id},{r["policy"]}')
  flush()
  if client=='quantumult-x':
   groups=['static = Proxy, reject, direct, resource-tag-regex=^MiSub$']
   for g in GROUPS[1:]:
    first='direct, Proxy' if defaults[g]=='DIRECT' else 'Proxy, direct'
    groups.append(f'static = {g}, {first}, resource-tag-regex=^MiSub$')
   refs=[]
   for id,policy in qx_refs:
    force=(', force-policy='+policy.lower() if policy in ('DIRECT','REJECT') else ', force-policy='+policy) if policy else ''
    refs.append(f'{BASE}/quantumult-x/sets/{id}.list, tag={id}{force}, update-interval=86400, enabled=true')
   text='''# 模板：在本地添加 MiSub 订阅和私有例外；不可把凭据上传 GitHub。\n[general]\nserver_check_url = https://www.gstatic.com/generate_204\n[dns]\nno-ipv6\nserver = 1.1.1.1\nserver = 9.9.9.9\ndoh-server = https://1.1.1.1/dns-query\nserver = /bilibili.com/223.5.5.5\n[policy]\n'''+ '\n'.join(groups)+'\n[server_remote]\n# 在此处添加本地 MiSub URL，tag=MiSub, update-interval=3600\n[filter_remote]\n'+'\n'.join(refs)+'\n[filter_local]\n# 私有规则放在此处；切勿加入公开仓库。\nfinal, Proxy\n'
   dns_lines=['no-ipv6']+['server = '+s for s in data['dns']['servers']]+['doh-server = '+data['dns']['doh']]
   for host in data['hosts']:
    if host.get('ip'):dns_lines.append('address = /'+host['domain']+'/'+host['ip'])
    if host.get('dns_server') and not host.get('rule_set'):dns_lines.append('server = /'+host['domain']+'/'+host['dns_server'])
   for line in data['client_overrides']['quantumult-x'].get('dns_lines',[]):
    if not isinstance(line,str) or '\n' in line or line.startswith('['):raise ValueError('invalid QX DNS override')
    dns_lines.append(line)
   text=re.sub(r'(?s)(\\[dns\\]\\n).*?(?=\\[policy\\])',lambda m:m.group(1)+'\\n'.join(dns_lines)+'\\n',text,count=1)
   write(out/'config.template.conf',text)
  elif client=='shadowrocket':
   # Device-local subscription and node selection must be added in Shadowrocket itself.
   groups=['Proxy = select, policy-regex-filter=.*']+[f'{g} = select, '+('DIRECT, Proxy' if defaults[g]=='DIRECT' else 'Proxy, DIRECT') for g in GROUPS[1:]]
   text='''# 模板：节点订阅、真实节点和私有例外在本机添加。\n[General]\ndns-server = https://1.1.1.1/dns-query\n[Proxy Group]\n'''+ '\n'.join(groups)+'\n[Rule]\n# 请在此行之后、公开规则之前添加本地私有例外。\n'+'\n'.join(shadow_rules)+'\n[Host]\n'
   general=data['client_overrides']['shadowrocket'].get('general_lines',[])
   if any(not isinstance(line,str) or '\n' in line or line.startswith('[') for line in general):raise ValueError('invalid Shadowrocket general override')
   text=text.replace('dns-server = https://1.1.1.1/dns-query','dns-server = '+data['dns']['doh']+('\\n'+'\\n'.join(general) if general else ''))
   for host in data['hosts']:
    if host.get('ip'):text+=host['domain']+' = '+host['ip']+'\\n'
   write(out/'config.template.conf',text)
  else:
   # A domain-only classical provider is used for DNS, so IP/process rules cannot cause recursive resolution.
   dns_sets={d['rule_set'] for d in data['dns']['overrides']}
   dns_sets.update(h['rule_set'] for h in data['hosts'] if h.get('rule_set') and h.get('dns_server'))
   for set_id in sorted(dns_sets):
    dns_lines=[]; dns_seen=set()
    for k,v,o in parsed[set_id]:
     if k in {'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD'}:
      line=convert((k,v,()),client)
      if line not in dns_seen:dns_seen.add(line);dns_lines.append(line)
    if not dns_lines:raise ValueError('DNS rule set has no domain rules: '+set_id)
    meta=metas[set_id];id=set_id+'-dns'
    write(out/'sets'/f'{id}.list',f"# Source: {meta['upstream_url']}\n# Attribution: {meta['attribution']}\n"+'\n'.join(dns_lines)+'\n')
    mh_providers[id]={'type':'http','behavior':'classical','format':'text','url':f'{BASE}/mihomo/sets/{id}.list','path':f'./rules/{id}.list','interval':meta['update_interval']}
   groups=[]
   for name in GROUPS:
    if name=='Proxy':choices=['REJECT','DIRECT','LOCAL_SNELL','LOCAL_STATIC']
    elif defaults[name]=='DIRECT':choices=['DIRECT','Proxy','LOCAL_SNELL','LOCAL_STATIC']
    else:choices=['Proxy','DIRECT','LOCAL_SNELL','LOCAL_STATIC']
    groups.append({'name':name,'type':'select','proxies':choices,'use':['MiSub']})
   config={'mixed-port':7890,'allow-lan':False,'mode':'rule','ipv6':False,'proxy-providers':{'MiSub':{'type':'http','url':'https://example.invalid/LOCAL_MISUB_URL','interval':3600,'health-check':{'enable':True,'url':'https://www.gstatic.com/generate_204','interval':300}}},'proxies':[], 'proxy-groups':groups,'dns':{'enable':True,'ipv6':False,'default-nameserver':data['dns']['servers'],'proxy-server-nameserver':data['dns']['servers'],'nameserver':[data['dns']['doh']+'#LOCAL_SNELL'],'nameserver-policy':{'rule-set:chinamax-dns':['223.5.5.5','223.6.6.6']}},'tun':{'enable':False,'dns-hijack':data['dns']['hijack']},'rule-providers':mh_providers,'rules':mh_rules}
   config['dns']['nameserver']=[data['dns']['doh']+'#'+data['dns']['doh_outbound']]
   config['dns']['nameserver-policy']={'rule-set:'+d['rule_set']+'-dns':d['servers'] for d in data['dns']['overrides']}
   config['hosts']={h['domain']:h['ip'] for h in data['hosts'] if h.get('ip')}
   for h in data['hosts']:
    if h.get('dns_server'):
     key='rule-set:'+h['rule_set']+'-dns' if h.get('rule_set') else '+.'+h['domain']
     config['dns']['nameserver-policy'][key]=[h['dns_server']]
   overrides=data['client_overrides']['mihomo']
   for key in ('dns','tun'):
    if key in overrides:
     if not isinstance(overrides[key],dict):raise ValueError('Mihomo override must be a mapping')
     config[key].update(overrides[key])
   write(out/'config.template.yaml','# 模板：须通过本地覆写提供 LOCAL_SNELL、LOCAL_STATIC 和 MiSub URL。\n'+yaml.safe_dump(config,allow_unicode=True,sort_keys=False))
 # Stable report: do not put current timestamps in generated output.
 write(stage/'BUILD_REPORT.json',json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 return report

def validate_stage(data, stage):
 config=yaml.safe_load((stage/'mihomo/config.template.yaml').read_text())
 if [g['name'] for g in config['proxy-groups']]!=GROUPS:raise ValueError('Mihomo group count mismatch')
 for client in CLIENTS:
  files=list((stage/client/'sets').glob('*.list'))
  if not files or any(f.stat().st_size==0 for f in files):raise ValueError('empty generated rule set')
  for f in files:
   seen=set()
   for line in f.read_text().splitlines():
    if line in seen:raise ValueError(f'duplicate line in {f.name}')
    seen.add(line)
 for client in ('quantumult-x','shadowrocket'):
  text=(stage/client/'config.template.conf').read_text()
  for name in GROUPS:
   if name not in text:raise ValueError(f'{client}: missing {name}')

def build():
 data=load()
 with tempfile.TemporaryDirectory(prefix='.build-',dir=ROOT) as temp:
  stage=pathlib.Path(temp)/'dist';stage.mkdir()
  report=render(data,stage);validate_stage(data,stage)
  subprocess.run([sys.executable, str(ROOT/'tests/test_routing.py'), str(stage)], check=True)
  dest=ROOT/'dist';backup=ROOT/'.dist-backup'
  if backup.exists():raise RuntimeError('previous dist backup exists; inspect it before building')
  if dest.exists():dest.rename(backup)
  try:stage.rename(dest)
  except BaseException:
   if backup.exists():backup.rename(dest)
   raise
  if backup.exists():shutil.rmtree(backup)
 print('Build succeeded:',len(report['sources']),'upstreams, 8 groups, 3 targets')

if __name__=='__main__':build()
