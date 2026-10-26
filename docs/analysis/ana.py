import sys,re,csv
csv.field_size_limit(10**9)
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8',errors='ignore')))
W=[r.get('is_winner','').upper()=='TRUE' for r in rows]
T=[(r['project_name']+' '+r['inspiration']+' '+r['what_it_does']).lower() for r in rows]
K=[r['tech_stack'].lower() for r in rows]
print(len(rows),'base win%',round(100*sum(W)/len(W),1))
def rep(lbl,pat,src):
    m=[i for i,s in enumerate(src) if re.search(pat,s)]
    print(f"{lbl:22s} n={len(m):5d} win%={100*sum(W[i] for i in m)/max(1,len(m)):5.1f}")
cats={'election/voter':r'\b(election|voter|ballot|electoral)','misinfo/fact-check':r'misinformation|fact.?check|fake news','deepfake':r'deepfake|synthetic media','event/registration':r'event (organi|registration|promotion|discovery)','women safety':r'women.{0,10}safety|harass|\bsos\b|personal safety','education gamified':r'gamif','education':r'\b(student|learn)','healthcare':r'health|medical|symptom|patient','lab report':r'lab report|medical report|blood test','multilingual':r'hindi|multilingual|translat','whatsapp/telegram':r'whatsapp|telegram','voice':r'voice','wearable':r'wearable|smartwatch','anomaly':r'anomal','explain':r'explainab'}
for k,p in cats.items(): rep(k,p,T)
for t in ['openai','gemini','claude','langchain','whisper','twilio','react','flutter','streamlit','next.js','fastapi','opencv','arduino','elevenlabs','vapi']: rep('tech '+t,re.escape(t),K)
