"""Independent replay of endpoint-cut path propagation certificates."""
from pathlib import Path
from math import gcd
from itertools import combinations
import gzip,json

def check_path(path,color,assignment,extra=None):
    assert len(path)==10 and len(set(path))==10
    assert all(type(v) is int and 1<=v<=17 for v in path)
    for u,v in zip(path,path[1:]):
        e=tuple(sorted((u,v)));assert gcd(u,v)==1
        assert (e==extra or assignment.get(e)==color)

def validate(path):
    doc=json.load(gzip.open(path));base=Path(__file__).parents[1]/'009-near-extremal-structure/endpoint-cuts.json.gz'
    cuts=[r for r in json.load(gzip.open(base))['records'] if r['path'] is None]
    seen=set();steps=0;proved=0
    for r in doc['records']:
        i=r['case'];assert type(i) is int and 0<=i<len(cuts) and i not in seen;seen.add(i)
        assert r['a']==cuts[i]['a'] and r['b']==cuts[i]['b']
        A=set(r['a']);B=set(r['b'])
        colors={tuple(sorted((a,b))):1 for a in A for b in B if gcd(a,b)==1}
        for step in r['steps']:
            e=tuple(step['edge']);c=step['color'];assert c in (0,1) and len(e)==2 and e[0]<e[1] and gcd(*e)==1 and e not in colors
            check_path(step['path'],1-c,colors,e)
            assert e in {tuple(sorted(p)) for p in zip(step['path'],step['path'][1:])}
            colors[e]=c;steps+=1
        assert r['red']==sum(c==0 for c in colors.values()) and r['blue']==sum(c==1 for c in colors.values())
        if r['status']=='contradiction':
            conflict=r['conflict'];c=conflict['color'];assert c in (0,1)
            if conflict['kind']=='path':check_path(conflict['path'],c,colors)
            elif conflict['kind']=='count':raise AssertionError('count input not allowed in the pure path certificate')
            else:raise AssertionError('unsupported contradiction')
            proved+=1
        else:assert r['status'] in ('stalled','inconclusive')
    if doc['status']=='complete':assert seen==set(range(len(cuts)))
    return {'cases':len(seen),'proved':proved,'implications':steps,'complete':doc['status']=='complete' and proved==len(cuts)}

if __name__=='__main__':print(json.dumps(validate(Path(__file__).with_name('propagation.json.gz')),sort_keys=True))
