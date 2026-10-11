#!/usr/bin/env python3
"""Capture real public GradientMine UI as captioned Colosseum videos.
Only a recorded local evidence viewer is used. No chain payout or live training is fabricated.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
import subprocess,textwrap,time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"_submission_media"
PITCH_TIMES=[0,16,42,61,80,101,111,120]
DEMO_TIMES=[0,21,45,67,91,116,142,165]
DEMO=[
"GradientMine is a model bug bounty prototype. This is the actual deployed public evidence viewer, showing a completed local training run, not a live customer marketplace.",
"A model owner defines a frozen parent, target improvement, evaluator, deadline and reward. Workers submit bounded model updates. Hidden final evaluation, not self-reported worker scores, determines eligibility.",
"The recorded run trained real PyTorch adapters using three operating-system processes on one machine. One process was a disclosed shuffled-label negative control. These are not three remote mining nodes.",
"Here is the immutable policy in the product's own inspector. Its content hash is checked. The named evaluator and evaluation split are committed before final scoring.",
"The actual parent scores 84.72 percent on 360 held-out examples. The selected candidate reaches 95.28 percent. That is a 10.56 percentage-point improvement.",
"The product displays signed worker manifests and the evaluator's signed winning receipt. The Fix Passport links the parent, submitted adapter, accepted model, evaluator and scoring terms. Signatures authenticate evidence, not training itself.",
"The Solana escrow program supports payout rules and refunds, tested as a compiled program locally. This particular recorded job is unpaid and has no finalized live Devnet transfer. No invented Explorer payment."
]

def pitch_paragraphs():
    source=(ROOT/"submission/PITCH_120S_2026-10-10.md").read_text(encoding="utf8")
    section=source.split("## Founder narration",1)[1].split("## 2:00",1)[0]
    result=[];current=[]
    for line in section.splitlines():
        if line.startswith("> "):current.append(line[2:])
        elif (line.strip()==">" or not line.strip()) and current:
            result.append(" ".join(current));current=[]
    if current:result.append(" ".join(current))
    if len(result)!=7:raise ValueError(f"Expected seven pitch paragraphs, got {len(result)}")
    return result

def stamp(seconds):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def subtitles(paragraphs,times,path):
    lines=[]
    for paragraph,a,b in zip(paragraphs,times[:-1],times[1:],strict=True):
        chunks=[];chunk=[]
        for word in paragraph.split():
            if chunk and (len(" ".join([*chunk,word]))>68 or len(chunk)>=11):
                chunks.append(chunk);chunk=[]
            chunk.append(word)
        if chunk:chunks.append(chunk)
        total=sum(map(len,chunks));used=0
        for chunk in chunks:
            start=a+(b-a)*used/total;used+=len(chunk);end=a+(b-a)*used/total
            wrap=textwrap.wrap(" ".join(chunk),width=46,break_long_words=False)
            if len(wrap)>2:raise ValueError("Caption overflow")
            lines.append(f"{len(lines)+1}\n{stamp(start)} --> {stamp(end)}\n"+"\n".join(wrap)+"\n")
    path.write_text("\n".join(lines),encoding="utf8")

def scroll(page,selector):
    item=page.locator(selector).first
    if not item.count():raise ValueError("Actual UI section missing: "+selector)
    item.scroll_into_view_if_needed(timeout=12000)
    page.wait_for_timeout(400)

def capture(name,url,duration,scenes,paragraphs,times):
    dest=OUT/name;dest.mkdir(parents=True,exist_ok=True)
    captions=dest/(name+".srt")
    subtitles(paragraphs,times,captions)
    timeline=[];errors=[];writes=[]
    with sync_playwright() as api:
        browser=api.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1920,"height":900},
           record_video_dir=str(dest/"original"),record_video_size={"width":1920,"height":900},
           reduced_motion="reduce",locale="en-US",timezone_id="UTC")
        page=context.new_page()
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda r:writes.append(r.url) if r.method not in ("GET","HEAD") else None)
        response=page.goto(url,wait_until="domcontentloaded",timeout=60000)
        if not response or response.status!=200:raise ValueError("Public viewer not HTTP 200")
        page.locator("#hero-title").wait_for(timeout=25000)
        page.wait_for_function("() => /Recorded local experiment/i.test(document.getElementById('mode-banner')?.innerText||'')",timeout=30000)
        page.locator("#jobs .job").first.wait_for(timeout=15000)
        page.locator("tr.winner").first.wait_for(timeout=15000)
        page.evaluate("""name=>{
          const tag=document.createElement('div');
          tag.textContent=name.toUpperCase()+' / GRADIENTMINE / ACTUAL RECORDED EVIDENCE';
          tag.style.cssText='position:fixed;z-index:9999999;top:15px;left:20px;pointer-events:none;padding:10px 16px;border-radius:3px;background:rgba(12,12,13,.9);color:white;font:bold 16px Arial';
          document.body.appendChild(tag);
          const note=document.createElement('div');
          note.textContent='READ-ONLY LOCAL RUN · PUBLIC BENCHMARK · NO FUNDS MOVED';
          note.style.cssText='position:fixed;z-index:9999999;bottom:16px;left:20px;pointer-events:none;padding:9px 14px;color:white;background:rgba(12,12,13,.9);font:bold 13px Arial';
          document.body.appendChild(note);
        }""",name)
        video=page.video
        began=time.monotonic()
        for when,action in scenes:
            wait=when-(time.monotonic()-began)
            if wait>0:page.wait_for_timeout(wait*1000)
            if action.startswith("scroll:"):
                if page.locator("#evidence-dialog").is_visible():page.locator("#evidence-dialog .close").click()
                scroll(page,action[7:])
            elif action=="policy":
                scroll(page,"#workspace")
                page.get_by_role("button",name="Inspect immutable policy",exact=True).first.click(timeout=12000)
                page.locator("#evidence-dialog").wait_for(state="visible",timeout=12000)
            elif action=="receipt":
                if page.locator("#evidence-dialog").is_visible():page.locator("#evidence-dialog .close").click()
                scroll(page,"#workspace")
                page.locator("tr.winner").get_by_role("button",name="Receipt",exact=True).click(timeout=12000)
                page.locator("#evidence-dialog").wait_for(state="visible",timeout=12000)
            elif action=="passport":
                if page.locator("#evidence-dialog").is_visible():page.locator("#evidence-dialog .close").click()
                scroll(page,".passport")
            else:raise ValueError("Unknown action "+action)
            page.screenshot(path=str(dest/f"scene-{when:03}.png"))
            timeline.append({"second":when,"action":action})
            print(f"{name} {when}: {action}",flush=True)
        remain=duration+0.7-(time.monotonic()-began)
        if remain>0:page.wait_for_timeout(remain*1000)
        context.close();browser.close()
        original=video.path()
    if errors:raise ValueError("Browser JS errors: "+repr(errors[:3]))
    if writes:raise ValueError("Read-only browser sent writes: "+repr(writes[:3]))
    target=OUT/f"gradientmine-{name}-colosseum-2026.mp4"
    filt=("fps=30,pad=1920:1080:0:0:color=0x171719,"
       f"subtitles={captions}:force_style='FontName=DejaVu Sans,FontSize=26,"
       "PrimaryColour=&H00FFFFFF,OutlineColour=&H000F1011,BorderStyle=1,Outline=1,Shadow=0,MarginV=38,Alignment=2'")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(original),
       "-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=48000",
       "-t",str(duration),"-vf",filt,
       "-c:v","libx264","-preset","veryfast","-crf","25","-pix_fmt","yuv420p",
       "-r","30","-movflags","+faststart","-c:a","aac","-b:a","48k","-shortest",str(target)],check=True)
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-of","json",str(target)],text=True))["format"]
    if abs(float(info["duration"])-duration)>0.5:raise ValueError("Incorrect video duration")
    if int(info["size"])<100000:raise ValueError("Video output unexpectedly small")
    return {"file":target.name,"seconds":float(info["duration"]),"bytes":int(info["size"]),
      "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"url":url,
      "mode":"public recorded local evidence viewer, not customer data or real Devnet payout",
      "audio":"caption-led, no narrator","scenes":timeline}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="https://gradientmine.pages.dev")
    opts=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    pitch=[(0,"scroll:#top"),(16,"scroll:#how-it-works"),(37,"scroll:#the-proof"),
      (57,"scroll:#workspace"),(80,"scroll:#trust"),(100,"scroll:#top")]
    demo=[(0,"scroll:#top"),(21,"scroll:#how-it-works"),(42,"scroll:#the-proof"),
      (63,"scroll:#workspace"),(83,"policy"),(107,"receipt"),(132,"passport"),(150,"scroll:#trust")]
    result={"recordings":[
       capture("pitch",opts.url,120,pitch,pitch_paragraphs(),PITCH_TIMES),
       capture("demo",opts.url,165,demo,DEMO,DEMO_TIMES)]}
    (OUT/"media-manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2),flush=True)

if __name__=="__main__":main()
