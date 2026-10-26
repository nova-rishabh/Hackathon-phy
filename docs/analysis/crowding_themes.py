import csv,re,sys
csv.field_size_limit(10**9)
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8',errors='replace')))
print(len(rows), list(rows[0].keys()))
def win(r): return str(r.get('is_winner')).strip().upper()=='TRUE'
base=sum(win(r) for r in rows); print('base',base,base/len(rows))
def txt(r): return ' '.join((r.get(k) or '') for k in ['project_name','inspiration','what_it_does','how_we_built_it','tech_stack']).lower()
T=[(r,txt(r)) for r in rows]
themes={
'election':[r'elector',r'voter',r'election',r'\bvoting\b'],
'misinfo/factcheck':[r'misinformation',r'fact[- ]?check',r'fake news',r'disinformation',r'claim'],
'event/community':[r'event',r'whatsapp',r'telegram bot',r'registration',r'outreach',r'community'],
'whatsapp/telegram bot':[r'whatsapp',r'telegram'],
'deepfake':[r'deepfake',r'synthetic media',r'ai-generated (image|video)',r'manipulated media',r'fake (image|video|audio)'],
'women safety':[r'women',r'\bsos\b',r'personal safety',r'harass',r'safety'],
'gamified edu':[r'gamif',r'educat',r'learning',r'tutor',r'students?'],
'gamif strict':[r'gamif'],
'healthcare':[r'health',r'medical',r'symptom',r'patient',r'diagnos',r'medic'],
'med report/symptom':[r'symptom',r'medical report',r'lab report',r'prescription'],
}
for k,pats in themes.items():
    print('##',k)
    for p in pats:
        m=[r for r,t in T if re.search(p,t)]
        w=sum(win(r) for r in m)
        print(f'  {p:30} n={len(m):5} w={w:4} {100*w/max(1,len(m)):.1f}%')
    m=[r for r,t in T if any(re.search(p,t) for p in pats)]
    w=sum(win(r) for r in m); print(f'  ANY n={len(m)} w={w} {100*w/max(1,len(m)):.1f}%')
# features
def feat(r):
    t=txt(r)
    ml=bool(re.search(r'tensorflow|pytorch|scikit|sklearn|keras|opencv|yolo|cnn|random forest|xgboost|trained|custom model|fine-?tun|bert|whisper|mediapipe|hugging',t))
    llm=bool(re.search(r'openai|gpt|chatgpt|gemini|llm|claude|langchain|chatbot',t))
    return ml,llm
cnt={}
for r in rows:
    ml,llm=feat(r); cnt.setdefault((ml,llm),[0,0]); cnt[(ml,llm)][0]+=1; cnt[(ml,llm)][1]+=win(r)
for k,v in cnt.items(): print('ml,llm',k,v,f'{100*v[1]/v[0]:.1f}%')
# length of what_it_does / hows
import statistics
wl=[len(r.get('how_we_built_it') or '') for r in rows if win(r)]
nl=[len(r.get('how_we_built_it') or '') for r in rows if not win(r)]
print('how len win/non',statistics.median(wl),statistics.median(nl))
# hackathon sizes
from collections import Counter
c=Counter(r['hackathon_name'] for r in rows); print(len(c)); 
print(Counter(r['hackathon_name'] for r in rows if win(r)).most_common(3))
