#!/usr/bin/env python3
"""Check the constraints that keep generated policy references valid."""
import copy, json, pathlib, sys, tempfile
import jsonschema, yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
import build
original=yaml.safe_load((ROOT/'schema/routing.yaml').read_text())
schema=json.loads((ROOT/'schema/routing.schema.json').read_text())
jsonschema.validate(original,schema)

def rejected(mutator, label):
 data=copy.deepcopy(original);mutator(data)
 with tempfile.TemporaryDirectory(prefix='routing-schema-') as t:
  root=pathlib.Path(t);(root/'schema').mkdir()
  (root/'schema/routing.yaml').write_text(yaml.safe_dump(data,allow_unicode=True))
  (root/'schema/routing.schema.json').write_text(json.dumps(schema))
  old=build.ROOT;build.ROOT=root
  try:
   try:build.load()
   except (ValueError,jsonschema.ValidationError):return
   raise AssertionError(label+' was accepted')
  finally:build.ROOT=old
rejected(lambda d:d['groups'].append({'name':'Proxy','default':'SELECT_NODE'}),'ninth group')
rejected(lambda d:d['groups'].__setitem__(7,{'name':'Proxy','default':'SELECT_NODE'}),'duplicate/missing group')
rejected(lambda d:d['rules'][0].__setitem__('policy','NoSuchGroup'),'invalid policy')
rejected(lambda d:d['rules'][7].__setitem__('value','missing-upstream'),'invalid rule-set reference')
print('Schema negative checks passed: ninth group, duplicate group, invalid policy and missing upstream.')
