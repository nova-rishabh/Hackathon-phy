import importlib.util,sys
spec=importlib.util.spec_from_file_location('sim',sys.argv[1]); 
src=open(sys.argv[1]).read().split("base=dict")[0]; exec(src)
# Overboard: extra capacity raises each ceiling by how much headroom the statement has for more modules/depth
HEAD={'Electoral':5,'Event':3,'Safety':3,'Deepfake':2,'Learning':3,'Health':2}
for k in CEIL: CEIL[k]+=0  # rivals unchanged
base=dict(cancel=.37,ceil_unc=2,pol=.25,polmax=5,emo=1.5)
def run_over(P,skill,N=20000,seed=2):
    r=random.Random(seed); pool=[s for s in S for _ in range(TEAMS[s])][:41]; w={s:0 for s in S}
    for _ in range(N):
        best=max(perf(s,min(1,max(.4,r.gauss(.70,.10))),r,P) for s in pool)
        for s in S:
            CEIL[s]+=HEAD[s]; v=perf(s,skill,r,P); CEIL[s]-=HEAD[s]
            w[s]+=v>best
    return {s:round(100*w[s]/N,1) for s in S}
print('Elite + overboard (skill .97):',run_over(base,.97))
print('Elite + overboard, judges wary of politics:',run_over({**base,'pol':.4,'polmax':8},.97))
print('Elite + overboard, big Safety emotion bonus:',run_over({**base,'emo':4},.97))
