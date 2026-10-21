#!/usr/bin/env python3
"""Fetch RSS and publish cautiously AI-summarized articles. Python 3.11+, no packages."""
import datetime as dt, email.utils, json, os, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET

RSS = ['https://techcrunch.com/category/artificial-intelligence/feed/', 'https://blog.google/technology/ai/rss/', 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'https://openai.com/news/rss.xml']
UTC=dt.timezone.utc
now=dt.datetime.now(UTC)
cutoff=now-dt.timedelta(days=int(os.getenv('MAX_NEWS_AGE_DAYS','3')))
entries={}
def get(url, headers=None, body=None):
    req=urllib.request.Request(url,data=body,headers=headers or {'User-Agent':'AIWithGeorgesNewsBot/1.0'})
    with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def txt(el,name):
    found=el.find(name)
    return (found.text or '').strip() if found is not None else ''
def parse_date(raw):
    try:
        value=email.utils.parsedate_to_datetime(raw) if ',' in raw else dt.datetime.fromisoformat(raw.replace('Z','+00:00'))
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    except (ValueError,TypeError):return None
for rss in RSS:
    try:
        root=ET.fromstring(get(rss))
        items=root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
        for item in items:
            atom='{http://www.w3.org/2005/Atom}'
            title=txt(item,'title') or txt(item,atom+'title')
            url=txt(item,'link')
            if not url:
                links=item.findall(atom+'link')
                url=next((a.get('href','') for a in links if a.get('rel','alternate')=='alternate'), links[0].get('href','') if links else '')
            date=parse_date(txt(item,'pubDate') or txt(item,atom+'published') or txt(item,atom+'updated'))
            parsed=urllib.parse.urlparse(url)
            if title and parsed.scheme in ('https','http') and date and cutoff<=date<=now+dt.timedelta(hours=1):
                entries[url]={'title':title,'date':date.strftime('%Y-%m-%d'),'url':url,'source':parsed.hostname or ''}
        print('Feed checked:',rss)
    except Exception as exc:print('Feed unavailable:',rss,str(exc))
candidates=list(entries.values())[:60]
if len(candidates)<2:raise RuntimeError('Fewer than two dated RSS news items. Previous published feed preserved.')
key=os.getenv('OPENAI_API_KEY')
if not key:raise RuntimeError('OPENAI_API_KEY repository secret is required')
prompt=('You are a careful news editor for AI With Georges. Select 2 to 6 significant stories ONLY from the provided recent RSS headlines. '
        'Do not invent any facts beyond the supplied article title and metadata. A title alone cannot establish detailed claims: summarize conservatively. '
        'Output ONLY JSON object with key "stories" (array of objects). Each has exact matching candidate URL and date YYYY-MM-DD, '
        'category one of AI/Cloud/Cybersecurity/Policy, original short factual title, summary 1-2 sentences, takeaway 1 sentence, and source. '
        'Never invent statistics, quotes, URLs, sources or dates. RSS entries: '+json.dumps(candidates))
payload=json.dumps({'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'input':prompt,'max_output_tokens':2500}).encode()
response=json.loads(get('https://api.openai.com/v1/responses',{'Content-Type':'application/json','Authorization':'Bearer '+key},payload))
raw=''.join(c.get('text','') for o in response.get('output',[]) if o.get('type')=='message' for c in o.get('content',[]) if c.get('type')=='output_text').strip()
if raw.startswith('```'):raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
produced=json.loads(raw)
allowed={item['url']:item for item in candidates}
valid=[]
for story in produced.get('stories',[]):
    if not isinstance(story,dict):continue
    orig=allowed.get(story.get('url'))
    if not orig or story.get('date')!=orig['date'] or story.get('category') not in ('AI','Cloud','Cybersecurity','Policy'):continue
    if not all(isinstance(story.get(k),str) and len(story[k].strip())>=5 for k in ('title','summary','takeaway')):continue
    valid.append({k:v for k,v in {'date':orig['date'],'category':story['category'],'title':story['title'][:180],'source':orig['source'],'url':orig['url'],'summary':story['summary'][:1000],'takeaway':story['takeaway'][:400]}.items()})
if len(valid)<2:raise RuntimeError('Insufficient validated AI output. Previous feed preserved.')
path=pathlib.Path('data/news.json')
old=json.loads(path.read_text()) if path.exists() else {'stories':[]}
stories={s['url']:s for s in old.get('stories',[]) if isinstance(s,dict) and 'url' in s}
stories.update({s['url']:s for s in valid})
ordered=sorted(stories.values(),key=lambda x:x['date'],reverse=True)[:60]
path.write_text(json.dumps({'updated_at':now.isoformat(),'stories':ordered},indent=2)+'\n')
print('New articles:',len(valid),'Total stored:',len(ordered))
