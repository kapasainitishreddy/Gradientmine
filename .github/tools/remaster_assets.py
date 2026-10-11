"""Generate disclosed stock-voice narration and capture actual public GradientMine UI.
No product edits, wallet signing, customer claims or production artifact tampering.
The tamper scene alters responses only in an isolated test browser, explicitly logged.
"""
from pathlib import Path
import hashlib,json,os,re,socket,subprocess,time,urllib.request
import numpy as np
import soundfile as sf
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'remaster-assets'
OUT.mkdir(exist_ok=True)
BASE='https://gradientmine.pages.dev'
PLAN=json.loads((ROOT/'submission/remaster-20261011/plan.json').read_text())
META={'source_commit':os.environ.get('GITHUB_SHA'),'narration':'Stock Kokoro af_heart, AI-generated; not the founder','captures':[],'audio':[]}

def save_meta():
    (OUT/'assets.json').write_text(json.dumps(META,indent=2))

def capture_all():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for name in ['studio','invalid','rights','workers','result','audit','tamper','receipt','solana']:
            dest=OUT/'clips';dest.mkdir(exist_ok=True)
            shots=OUT/'shots';shots.mkdir(exist_ok=True)
            context=browser.new_context(viewport={'width':1600,'height':900},record_video_dir=str(OUT/'raw'),record_video_size={'width':1600,'height':900},reduced_motion='reduce',locale='en-US')
            created=time.monotonic()
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            path='/bounty.html' if name in ['studio','invalid','rights'] else '/judge.html'
            if name=='receipt':path='/'
            response=page.goto(BASE+path,wait_until='networkidle',timeout=60000)
            assert response and response.status==200,(name,'non-200')
            page.evaluate("document.documentElement.style.zoom='0.9'")
            if path=='/bounty.html':
                page.locator('#sample').click()
                assert not page.locator('#rights').is_checked()
                page.locator('#baseline').scroll_into_view_if_needed()
            elif name=='receipt':
                page.locator('tr.winner').wait_for(timeout=25000)
                page.locator('tr.winner').get_by_role('button',name='Receipt',exact=True).click()
                page.wait_for_function("() => document.querySelector('#evidence-status').textContent.includes('Ed25519 signature verified')",timeout=25000)
            else:
                page.wait_for_function("() => document.querySelector('#evidence-status').textContent.includes('Loaded actual recorded local job')",timeout=25000)
                if name in ['workers','result','solana']:
                    step={'workers':2,'result':3,'solana':4}[name]
                    page.locator('[data-step="'+str(step)+'"]').click()
                    page.locator('[data-panel="'+str(step)+'"] .tour-detail').scroll_into_view_if_needed()
                else:
                    page.locator('.evidence-audit-control').evaluate("e => e.scrollIntoView({block:'center'})")
            page.wait_for_timeout(500)
            start=time.monotonic()-created
            extra={}
            if name=='invalid':
                page.locator('#target').fill('82')
                assert 'Target must improve' in page.locator('#issues').inner_text()
                page.locator('#issues').scroll_into_view_if_needed()
                page.wait_for_timeout(3500)
                page.locator('#target').fill('92')
                assert 'Target must improve' not in page.locator('#issues').inner_text()
                page.locator('#preview-total').scroll_into_view_if_needed()
                extra['invalid_target_rejected']=True
            elif name=='rights':
                page.locator('#download').scroll_into_view_if_needed()
                assert page.locator('#download').is_disabled()
                assert not page.locator('#rights').is_checked()
                extra['rights_not_attested']=True
            elif name in ['audit','tamper']:
                if name=='tamper':
                    page.route('**/assets/artifacts/*.json',lambda r:r.fulfill(status=200,content_type='application/json',body='{"disclosed_browser_tamper_test":true}'))
                    extra['browser_only_negative_control']='Intercepted artifact download in this isolated test browser only. Production files unchanged.'
                page.locator('#run-evidence-audit').click()
                expected='fail' if name=='tamper' else 'pass'
                page.wait_for_function("x => document.querySelector('#evidence-audit-result').dataset.result===x",arg=expected,timeout=45000)
                extra['audit_result']=page.locator('#evidence-audit-result').inner_text()
                if expected=='pass':assert '14 artifact hashes' in extra['audit_result'] and '6 Ed25519 signatures' in extra['audit_result']
                if expected=='fail':assert 'SHA-256' in extra['audit_result']
            if name=='result':
                assert page.locator('#tour-selected').inner_text()=='95.28%'
                extra['baseline']=page.locator('#tour-baseline').inner_text()
                extra['selected']=page.locator('#tour-selected').inner_text()
            page.wait_for_timeout(7000)
            page.screenshot(path=str(shots/(name+'.png')))
            end=time.monotonic()-created
            video=page.video
            context.close()
            original=Path(video.path())
            clip=dest/(name+'.mp4')
            subprocess.run(['ffmpeg','-y','-v','error','-ss',str(max(0,start-.1)),'-i',str(original),'-t',str(end-start),'-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(clip)],check=True)
            original.unlink()
            if errors:raise RuntimeError(str(errors))
            META['captures'].append({'scene':name,'url':BASE+path,'filename':str(clip.relative_to(OUT)),'seconds':end-start,'bytes':clip.stat().st_size,'sha256':hashlib.sha256(clip.read_bytes()).hexdigest(),**extra})
            save_meta()
            print('Captured',name,extra,flush=True)
        browser.close()

def speak_all():
    from kokoro_onnx import Kokoro
    models=ROOT/'.local-remaster-models';models.mkdir(exist_ok=True)
    socket.setdefaulttimeout(90)
    for filename in ['kokoro-v1.0.onnx','voices-v1.0.bin']:
        dest=models/filename
        if not dest.exists():
            url='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+filename
            urllib.request.urlretrieve(url,dest)
        assert dest.stat().st_size>1000000
    kokoro=Kokoro(str(models/'kokoro-v1.0.onnx'),str(models/'voices-v1.0.bin'))
    audio_dir=OUT/'audio';audio_dir.mkdir(exist_ok=True)
    for project,scenes in PLAN.items():
        for scene in scenes:
            chunks=re.split(r'(?<=[.!?])\s+',scene['text'])
            sequence=[];cues=[];cursor=0.;rate=24000
            for sentence in chunks:
                spoken=sentence.replace('GradientMine','Gradient Mine')
                samples,rate=kokoro.create(spoken,voice='af_heart',speed=1.04,lang='en-us')
                samples=np.asarray(samples,dtype=np.float32)
                assert len(samples)>500 and np.isfinite(samples).all()
                seconds=len(samples)/rate
                sequence.append(samples)
                cues.append({'start':cursor,'end':cursor+seconds,'text':sentence})
                cursor+=seconds
                pause=np.zeros(round(rate*.14),dtype=np.float32)
                sequence.append(pause);cursor+=.14
            output=audio_dir/(scene['id']+'.wav')
            sf.write(output,np.concatenate(sequence),rate,subtype='PCM_16')
            META['audio'].append({**scene,'project':project,'rate':rate,'seconds':cursor,'filename':str(output.relative_to(OUT)),'cues':cues})
            save_meta()
            print('Voiced',scene['id'],round(cursor,2),flush=True)
    META['model_sha256']=hashlib.sha256((models/'kokoro-v1.0.onnx').read_bytes()).hexdigest()
    META['voices_sha256']=hashlib.sha256((models/'voices-v1.0.bin').read_bytes()).hexdigest()
    save_meta()

if __name__=='__main__':
    capture_all()
    speak_all()
    print('All media assets generated',flush=True)
