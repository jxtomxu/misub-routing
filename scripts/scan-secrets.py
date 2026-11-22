#!/usr/bin/env python3
"""Report only paths and line numbers; never print matched secrets."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
patterns={
 'private-key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github-token':re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b'),
 'github-fine-grained-token':re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}\b'),
 'credential-in-url':re.compile(r'https?://[^\s/@:]+:[^\s/@]+@'),
 'credential-query':re.compile(r'[?&](?:token|access_token|auth|apikey|api_key|password)=[A-Za-z0-9_%.-]{12,}',re.I),
 'jwt':re.compile(r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b'),
 'uuid':re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
 'proxy-credentials':re.compile(r'\b(?:psk|password)\s*[=:]\s*["\x27]?[A-Za-z0-9+/_.-]{12,}',re.I),
 'node-uri':re.compile(r'\b(?:ss|ssr|vmess|vless|trojan|hysteria2?)://[A-Za-z0-9@_%+./=-]{20,}',re.I),
}
# Source code contains the scanner's own regexes; local/ and VCS metadata are not publishable.
exclude={'.git','.serena','__pycache__','.venv'}
findings=[];files=0
for p in ROOT.rglob('*'):
 if not p.is_file() or any(part in exclude for part in p.relative_to(ROOT).parts):continue
 if p.relative_to(ROOT).parts[0]=='local' and not p.name.endswith('.example.yaml'):continue
 if p==Path(__file__).resolve():continue
 try:lines=p.read_text(encoding='utf-8').splitlines()
 except (UnicodeError,OSError):continue
 files+=1
 for i,line in enumerate(lines,1):
  for name,pattern in patterns.items():
   if pattern.search(line):findings.append((str(p.relative_to(ROOT)),i,name))
if findings:
 for path,line,name in findings:print(f'{path}:{line}: {name}')
 print('Potential secrets found; publication blocked.');raise SystemExit(1)
print(f'Secret scan passed: {files} text files; signatures only, not a guarantee.')
