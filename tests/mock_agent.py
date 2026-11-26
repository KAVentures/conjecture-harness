import json,sys
s=sys.stdin.read()
if s.startswith('Act as a hostile'):
    print(json.dumps({'verdict':'gap','first_issue':'mock has no general proof','tests':[],'unresolved':['general proof']}))
else:
    print(json.dumps({'kind':'observation','claim':'test only','derivation':'synthetic output','gaps':['not research'],'next':'none','sources':[],'witness':None}))
