import csv,re,sys
csv.field_size_limit(10**9)
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8',errors='replace')))
win=lambda r:str(r['is_winner']).upper()=='TRUE'
core=lambda r:((r['project_name'] or '')+' '+(r['what_it_does'] or '')).lower()
th={'election/voter':r'election|voter|voting|ballot','misinfo/factcheck':r'misinformation|fact.?check|fake news|disinformation|deepfake','deepfake':r'deepfake|deep fake|synthetic media|fake (image|video|audio)','women safety':r'women|woman|\bsos\b|harass|assault|personal safety','safety(any)':r'safety|emergency','gamified':r'gamif|quest|game.?based learn|learn.*game','edu':r'education|student|tutor|learn','health':r'health|medical|symptom|patient|doctor','medreport':r'medical report|lab (result|report)|blood test|prescription|symptom','chatbot-whatsapp':r'whatsapp|telegram|sms bot|discord bot','event/outreach':r'event (manag|organi|regist)|hackathon|outreach|registration|volunteer'}
for k,p in th.items():
    m=[r for r in rows if re.search(p,core(r))]
    w=[r for r in m if win(r)]
    print(f'{k:20} n={len(m):4} w={len(w):3} {100*len(w)/len(m):.1f}%')
# integration: count of distinct tech categories & len
def ntech(r): return len([x for x in re.split(r'[,;\n]',r['tech_stack'] or '') if x.strip()])
import statistics
for lab,f in [('win',True),('non',False)]:
    s=[ntech(r) for r in rows if win(r)==f]; print(lab,'ntech mean',statistics.mean(s))
# chatbot only
chat=lambda r: bool(re.search(r'chatbot|chat bot|gpt|openai|llm|gemini',core(r)))
ml=lambda r: bool(re.search(r'tensorflow|pytorch|scikit|opencv|yolo|cnn|computer vision|trained|classifier|detect|whisper|mediapipe|random forest',(r['how_we_built_it'] or '').lower()+(r['tech_stack'] or '').lower()))
for a in [0,1]:
  for b in [0,1]:
    m=[r for r in rows if chat(r)==bool(a) and ml(r)==bool(b)]
    print('chat',a,'ml',b,len(m),f'{100*sum(map(win,m))/len(m):.1f}%')
# themed: ml vs not within edu+health
for k in ['health','edu','women safety','election/voter','misinfo/factcheck']:
    m=[r for r in rows if re.search(th[k],core(r))]
    a=[r for r in m if ml(r)]; b=[r for r in m if not ml(r)]
    print(k,'ml',len(a),f'{100*sum(map(win,a))/max(1,len(a)):.0f}%','nonml',len(b),f'{100*sum(map(win,b))/max(1,len(b)):.0f}%')
for k in ['election/voter','misinfo/factcheck','women safety','health']:
    print('\n#####',k)
    m=[r for r in rows if re.search(th[k],core(r)) and win(r)]
    for r in m[:6]:
        print('-',r['hackathon_name'],'|',r['project_name'],'|',(r['what_it_does'] or '')[:230].replace('\n',' '),'| TECH:',(r['tech_stack'] or '')[:100])
