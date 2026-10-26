import sys
src=open(sys.argv[1]).read().split("base=dict")[0]; exec(src)
base=dict(cancel=.37,ceil_unc=2,pol=.25,polmax=5,emo=1.5)
worst={**base,'pol':.4,'polmax':8}
print('Base:',run(base,.90))
TEAMS.update(Electoral=9,Health=7,Learning=8)
print('Electoral crowded (9 teams):',run(base,.90))
print('Electoral crowded + judges wary of politics:',run(worst,.90))
