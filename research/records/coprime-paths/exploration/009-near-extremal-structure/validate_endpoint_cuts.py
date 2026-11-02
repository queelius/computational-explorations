"""Independent complete validator for 6/8 endpoint cut classification."""
from pathlib import Path
from itertools import combinations,product
from math import gcd
import gzip,json

def validate(path):
    d=json.load(gzip.open(path));assert d['status']=='complete'
    V=set(range(1,18));edges={frozenset(e) for e in combinations(V,2) if gcd(*e)==1}
    # Derive interchangeability directly by testing transpositions on host edges.
    classes=[];remaining=set(V)
    while remaining:
        v=min(remaining);cl=[]
        for w in sorted(remaining):
            swap=lambda x:w if x==v else v if x==w else x
            if all((gcd(x,y)==1)==(gcd(swap(x),swap(y))==1) for x,y in combinations(V,2)):cl.append(w)
        classes.append(cl);remaining-=set(cl)
    assert classes==d['classes']
    expected=set()
    def enumerate_signatures(i,a,b,signature):
        if i==len(classes):
            if a==b==0:expected.add(tuple(signature))
            return
        for na in range(len(classes[i])+1):
            for nb in range(len(classes[i])-na+1):
                if na<=a and nb<=b:enumerate_signatures(i+1,a-na,b-nb,signature+[(na,nb)])
    enumerate_signatures(0,6,8,[])
    seen=set();negative=[]
    for r in d['records']:
        A=set(r['a']);B=set(r['b']);assert len(A)==6 and len(B)==8 and not A&B and A|B<=V
        sig=tuple((len(A&set(c)),len(B&set(c))) for c in classes)
        assert sig in expected and sig not in seen;seen.add(sig)
        p=r['path']
        if p is not None:
            assert len(p)==10 and len(set(p))==10 and set(p)<=A|B
            assert all(gcd(u,v)==1 and ((u in A)!=(v in A)) for u,v in zip(p,p[1:]))
        else:
            # Independent Held-Karp endpoint-set DP, exhaustive through 10 vertices.
            vertices=sorted(A|B);adj=[sum(1<<j for j,w in enumerate(vertices) if gcd(v,w)==1 and ((v in A)!=(w in A))) for v in vertices]
            dp={1<<i:1<<i for i in range(14)}
            for size in range(1,10):
                nxt={}
                for mask,ends in dp.items():
                    for i in range(14):
                        if ends>>i&1:
                            for j in range(14):
                                if adj[i]>>j&1 and not mask>>j&1:nxt[mask|1<<j]=nxt.get(mask|1<<j,0)|(1<<j)
                dp=nxt
            assert not dp
            assert {6,12}<=A
            negative.append(r)
    assert seen==expected
    return {'orbits':len(seen),'positive':len(seen)-len(negative),'negative':len(negative),'all_negative_include_6_and_12':True}

if __name__=='__main__':print(json.dumps(validate(Path(__file__).with_name('endpoint-cuts.json.gz')),sort_keys=True))
