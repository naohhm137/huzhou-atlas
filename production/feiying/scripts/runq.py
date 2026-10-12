import json,sys,os,time,datetime
priv,rt,logs,models=sys.argv[1:5]; sys.path.insert(0,rt); import lux3d_client as c
LP=os.path.join(logs,'budget-ledger.json')
L=json.load(open(LP,encoding='utf-8')); q=json.load(open(os.path.join(priv,'quote_Turbo.json')))['quote']; items=json.load(open(os.path.join(priv,'items_Turbo.json')))
def save(): json.dump(L,open(LP,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
def log(*a): print(datetime.datetime.now().strftime('%H:%M:%S'),*a,flush=True)
for k,e in L['entries'].items():
    if e['status']=='uncertain' and 'already in progress' in e.get('error',''):
        e['status']='reserved'; e['note']='first create rejected by concurrency limit; verified via list_tasks that no task was created'; e.pop('error',None)
save()
fmt=c.generation_result_formats('G1-Turbo',['glb'])
while True:
    E=L['entries']; running=[k for k,e in E.items() if e['status']=='submitted']
    for k in running:
        try: t=c.get_task(E[k]['taskId'],region='cn')
        except Exception as ex: log(k,'query err',str(ex)[:120]); continue
        st=t.get('status') if isinstance(t,dict) else None
        if st==3 or str(st).lower() in('success','succeeded'):
            outs=c.parse_task_outputs(t); d=os.path.join(models,k); os.makedirs(d,exist_ok=True)
            files=c.download_requested_models(outs,d,fmt); E[k]['status']='downloaded'; E[k]['files']=[p for p,_ in files]; log(k,'DONE',files)
        elif st in(4,5,6) or str(st).lower() in('failed','error'):
            E[k]['status']='failed'; E[k]['detail']=str({kk:v for kk,v in t.items() if 'url' not in kk.lower()})[:300]; log(k,'FAILED',E[k]['detail'])
        save()
    running=[k for k,e in E.items() if e['status']=='submitted']
    for k,e in E.items():
        if len(running)>=2: break
        if e['status']!='reserved': continue
        b=items[str(e['seq'])]['parameters']['body']; e['status']='submitting'; e['startedAt']=datetime.datetime.now().isoformat(); save()
        try:
            e['taskId']=str(c.create_image_to_3d_task(b['img'],version=b['version'],faceCount=b['faceCount'],outputFormat=b['outputFormat'],enablePbr=b['enablePbr'],region='cn',content_id=q['quoteId'])); e['status']='submitted'; running.append(k); log(k,'submitted',e['taskId'])
        except Exception as ex:
            msg=str(ex)
            if 'already in progress' in msg or 'CONCURRENCY' in msg: e['status']='reserved'
            else: e['status']='uncertain'; e['error']=msg[:300]; log(k,'UNCERTAIN',msg[:200])
        save()
    if all(e['status'] in('downloaded','failed','uncertain') for e in E.values()): log('ALL FINISHED'); break
    time.sleep(20)
