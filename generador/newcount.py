import json, sys
src=open('build3.py').read().split("if __name__ == '__main__':")[0]
g={'__file__':'build3.py','__name__':'b3'}; exec(src,g)
W=g['W']; B=g['B']
used=set(json.load(open('used_v1v2.json'))['words'])
base_free=[k for k in W if k not in used]
tot=0
for fn in sys.argv[1:]:
    new=set()
    for line in open(fn):
        if line.count('|')!=2: continue
        w,c,t=line.strip().split('|')
        if t not in '123' or ' ' in w: continue
        k=B.norm(w)
        if len(k)>=3 and k not in W and k not in used: new.add(k)
    for k in new: W[k]={}
    tot+=len(new); print(fn,len(new))
print('libres antes',len(base_free),'nuevas',tot,'total libres',len(base_free)+tot)
