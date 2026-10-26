# Monte Carlo: P(our team wins the single overall 1st prize | statement we pick)
import random, statistics as st
S=['Electoral','Event','Safety','Deepfake','Learning','Health']
CEIL={'Electoral':42,'Event':41,'Safety':37,'Deepfake':36,'Learning':35,'Health':33}  # judge-agent best-realistic /50
RISK={'Electoral':2,'Event':4,'Safety':5,'Deepfake':8,'Learning':3,'Health':3}        # CTO-agent build risk
CTRL={'Electoral':9,'Event':7,'Safety':6,'Deepfake':2,'Learning':8,'Health':8}        # CTO-agent demo control
TEAMS={'Electoral':3,'Event':6,'Safety':9,'Deepfake':3,'Learning':10,'Health':11}     # crowding-agent estimate
def perf(s,skill,r,P):
    if s=='Deepfake' and r.random()<P['cancel']:   # forced switch mid-event, half the time left
        return (CEIL['Event']-6)*skill - abs(r.gauss(0,4))
    x=CEIL[s]+r.gauss(0,P['ceil_unc'])              # uncertainty in judge ceilings
    x=x*skill - abs(r.gauss(0,1+0.5*RISK[s]))       # execution shortfall
    if r.random()<(10-CTRL[s])*0.025: x-=5          # live-demo failure
    if s=='Electoral' and r.random()<P['pol']: x-=r.uniform(1,P['polmax'])  # a judge uneasy with politics
    if s in('Safety',) : x+=r.gauss(P['emo'],1)     # emotional premium with Indian college judges
    return x
def run(P,our_skill,N=20000,seed=1):
    r=random.Random(seed); pool=[s for s in S for _ in range(TEAMS[s])][:41]
    wins={s:0 for s in S}
    for _ in range(N):
        best=max(perf(s,min(1,max(.4,r.gauss(.70,.10))),r,P) for s in pool)
        for s in S:
            if perf(s,our_skill,r,P)>best: wins[s]+=1
    return {s:round(100*wins[s]/N,1) for s in S}
base=dict(cancel=.37,ceil_unc=2,pol=.25,polmax=5,emo=1.5)
print('STRONG team (skill .90):',run(base,.90))
print('GOOD team   (skill .82):',run(base,.82))
print('Pessimistic on Electoral politics (40%, up to -8):',run({**base,'pol':.4,'polmax':8},.90))
print('Big emotional premium for Safety (+4):',run({**base,'emo':4},.90))
print('Judge ceilings very uncertain (sd 4):',run({**base,'ceil_unc':4},.90))
print('Deepfake surely runs (cancel 0):',run({**base,'cancel':0},.90))
