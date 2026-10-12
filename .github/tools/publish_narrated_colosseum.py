"""Publish honest, narrated Colosseum evidence videos from a pinned existing artifact.

Built with Pillow and FFmpeg only, not synthetic customer footage. The voice is the
disclosed stock Kokoro AI narrator from the verified remaster asset workflow.
DO NOT claim founder narration, Devnet payouts, independent training hosts or users.
"""
import argparse,hashlib,json,subprocess,math,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

ap=argparse.ArgumentParser()
ap.add_argument('--assets',type=Path,required=True)
ap.add_argument('--plan',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args()
A=a.assets.resolve();O=a.output.resolve();O.mkdir(parents=True,exist_ok=True)
plan=json.loads(a.plan.read_text(encoding='utf8'))
W,H,FPS=1920,1080,30
PAPER='#F3EEE5';INK='#1B2220';ORANGE='#B9432B';GREEN='#86CBA6'
DARK='#111F19';LIGHT='#FFFFFF';GREY='#645F59';LINE='#D4CEC2'
fontdir=Path('/usr/share/fonts/truetype/dejavu')
def font(size,bold=False):
    return ImageFont.truetype(str(fontdir/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size)
def put(draw,point,value,size=32,color=INK,bold=False,width=None,spacing=10):
    f=font(size,bold)
    words=value.replace('\n',' \n ').split()
    rows=[];row=''
    for word in words:
        if word=='\n':
            if row:rows.append(row);row=''
            continue
        candidate=(row+' '+word).strip()
        if row and width and draw.textlength(candidate,font=f)>width:
            rows.append(row);row=word
        else:row=candidate
    if row:rows.append(row)
    rows=rows[:8]
    draw.multiline_text(point,'\n'.join(rows),font=f,fill=color,spacing=spacing)
    return rows
def card(scene,n,total,target):
    kind=scene['kind'];img=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(img)
    d.text((74,35),'GRADIENTMINE',font=font(32,True),fill=INK)
    d.text((1410,48),'AI NARRATOR  •  NOT THE FOUNDER',font=font(17,True),fill=ORANGE)
    d.rectangle((74,104,1846,107),fill=LINE)
    d.text((75,124),('PRODUCT PITCH' if target=='pitch' else 'TECHNICAL DEMO')+
        '  /  '+str(n+1).zfill(2)+' OF '+str(total).zfill(2),font=font(17,True),fill=ORANGE)
    d.rectangle((0,900,1920,1080),fill=DARK)
    d.text((76,919),'RECORDED LOCAL PROOF  /  NAMED EVALUATOR  /  NO FUNDED DEVNET PAYOUT',font=font(17),fill=GREEN)
    file=A/'shots'/(kind+'.png')
    if file.is_file():
        shot=Image.open(file).convert('RGB')
        view=ImageOps.contain(shot,(1250,690),Image.Resampling.LANCZOS)
        x=74+(1250-view.width)//2
        y=184+(690-view.height)//2
        d.rectangle((70,180,1335,876),fill='#DDD6CA')
        img.paste(view,(x,y))
        x0=1385
        put(d,(x0,215),scene['label'],43,INK,True,385,9)
        d.line((x0,430,1830,430),fill=LINE,width=2)
        put(d,(x0,476),scene['text'],25,GREY,False,380,11)
        if kind=='tamper':
            d.rectangle((72,852,1330,888),fill=ORANGE)
            d.text((87,857),'ISOLATED TEST BROWSER ONLY  ·  PRODUCTION FILES UNCHANGED',
                   font=font(17,True),fill=LIGHT)
    else:
        d.rounded_rectangle((74,191,1846,858),radius=13,fill=DARK)
        d.text((135,274),'MODEL IMPROVEMENT BOUNTIES',font=font(19,True),fill=GREEN)
        put(d,(123,343),scene['label'],83,LIGHT,True,1520,22)
        put(d,(140,567),scene['text'],38,'#C9DCD0',False,1580,20)
    for i in range(total):
        x=75+i*(1750/total)
        d.rectangle((int(x),1065,int(x+max(8,1640/total)),1070),
                    fill=ORANGE if i<=n else '#35493D')
    return img

def stamp(n):
    cs=round(n*100);hours,cs=divmod(cs,360000);mins,cs=divmod(cs,6000);sec,cs=divmod(cs,100)
    return f'{hours}:{mins:02}:{sec:02}.{cs:02}'
def ass(scene,seconds,destination):
    body="""[Script Info]
ScriptType: v4.00+
Title: GradientMine Disclosed AI-Narrated Submission
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,33,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1.2,0,2,65,65,27,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    chunks=[];current=[]
    for word in scene['text'].split():
        if current and (len(' '.join([*current,word]))>82 or len(current)>=13):
            chunks.append(current);current=[]
        current.append(word)
    if current:chunks.append(current)
    total=sum(len(x) for x in chunks);start=0.
    for chunk in chunks:
        end=start+seconds*len(chunk)/total
        lines=textwrap.wrap(' '.join(chunk),width=54,break_long_words=False)
        if len(lines)>2:raise RuntimeError('Subtitle exceeds two lines')
        sentence=r'\N'.join(lines).replace('{','').replace('}','')
        body+=f'Dialogue: 0,{stamp(start)},{stamp(end)},Default,,0,0,0,,{sentence}\n'
        start=end
    destination.write_text(body,encoding='utf8')

def probe(path):
    q=subprocess.check_output(['ffprobe','-v','error','-show_format',
                  '-show_streams','-of','json',str(path)],text=True)
    return json.loads(q)

manifest={'source_workflow_run':38114305144,'reused_assets':'Real live browser captures and Kokoro stock-voice WAV files',
          'narration':'Stock AI-generated Kokoro voice, NOT founder',
          'trust':'Recorded local Digits/PyTorch, named evaluator, local compiled Solana program. No Devnet payout, customers or revenue.',
          'outputs':[]}
for name,scenes in plan.items():
    target=119.7 if name=='pitch' else 164.8
    speed=1.0 if name=='pitch' else 1.035
    import wave
    durations=[]
    for sc in scenes:
        with wave.open(str(A/'audio'/(sc['id']+'.wav')),'rb') as w:
            durations.append(w.getnframes()/w.getframerate()/speed)
    pad=(target-sum(durations))/len(scenes)
    if not (.05<pad<1.5):raise RuntimeError(f'Audio/pad budget invalid: {name} {pad}')
    folder=O/name;folder.mkdir(exist_ok=True)
    sceneFiles=[]
    for i,(scene,seconds) in enumerate(zip(scenes,durations)):
        dur=seconds+pad
        cid=scene['id']
        picture=folder/(cid+'.png')
        card(scene,i,len(scenes),name).save(picture)
        subs=folder/(cid+'.ass');ass(scene,dur,subs)
        out=folder/(cid+'.mp4')
        cmd=['ffmpeg','-y','-loglevel','error',
             '-loop','1','-framerate','30','-i',str(picture),
             '-i',str(A/'audio'/(cid+'.wav')),
             '-filter_complex',
             '[0:v]ass='+str(subs)+'[v];[1:a]atempo='+str(speed)+',apad[a]',
             '-map','[v]','-map','[a]','-t',str(dur),
             '-c:v','libx264','-preset','ultrafast','-crf','26',
             '-pix_fmt','yuv420p','-r','30',
             '-c:a','aac','-b:a','96k','-ar','48000','-movflags','+faststart',
             str(out)]
        subprocess.run(cmd,check=True)
        sceneFiles.append(out)
        print(name,cid,round(dur,2),flush=True)
    playlist=folder/'concat.txt'
    playlist.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in sceneFiles))
    result=O/('GradientMine_Pitch_Narrated_119s.mp4' if name=='pitch' else 'GradientMine_Demo_Narrated_165s.mp4')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(playlist),
                    '-t',str(target),'-c','copy','-movflags','+faststart',str(result)],check=True)
    info=probe(result);vid=next(x for x in info['streams'] if x['codec_type']=='video')
    audio=next(x for x in info['streams'] if x['codec_type']=='audio')
    if (vid['width'],vid['height'])!=(1920,1080) or vid['codec_name']!='h264' or audio['codec_name']!='aac':
        raise RuntimeError('Media quality specification failed')
    if not (117<float(info['format']['duration'])<120 if name=='pitch' else 160<float(info['format']['duration'])<166):
        raise RuntimeError('Duration outside expected range')
    manifest['outputs'].append({
        'filename':result.name,'seconds':float(info['format']['duration']),
        'bytes':result.stat().st_size,'sha256':hashlib.sha256(result.read_bytes()).hexdigest(),
        'codec':vid['codec_name'],'audio_codec':audio['codec_name'],
        'dimensions':[vid['width'],vid['height']],
        'source':name,'scene_count':len(sceneFiles)})
(O/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2),flush=True)
