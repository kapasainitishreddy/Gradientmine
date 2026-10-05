"""Build original seek-safe /brag compositions from strictly verified public evidence."""
from __future__ import annotations
import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOUR = ROOT / 'submission/tour'


def build(vertical=False):
    manifest = json.loads((TOUR / 'evidence-manifest.json').read_text())
    assert manifest['job_id'] == json.loads((ROOT / 'web/assets/recorded-run.json').read_text())['job']['id']
    duration = 20 if vertical else 22
    width, height = (1080, 1920) if vertical else (1920, 1080)
    target = ROOT / '.local/tour/vertical/composition' if vertical else TOUR / 'composition'
    target.mkdir(parents=True, exist_ok=True)
    assets = TOUR / 'composition/assets'
    if vertical and not (target / 'assets').exists():
        (target / 'assets').symlink_to(assets, target_is_directory=True)
    shutil.copy(target / 'assets/gsap.min.js' if vertical else TOUR / 'composition/node_modules/gsap/dist/gsap.min.js', assets / 'gsap.min.js') if not vertical else None
    audio_name = 'evidence-bed-vertical.wav' if vertical else 'evidence-bed.wav'
    audio = ROOT / '.local/tour' / audio_name
    link = assets / audio_name
    if not link.exists():
        link.symlink_to(audio)
    audio_data_name = 'audio-data-vertical.json' if vertical else 'audio-data.json'
    audio_data = json.loads((ROOT / '.local/tour' / audio_data_name).read_text())
    losses = json.loads((assets / 'losses.json').read_text())
    def small(value):
        return value[:12] + '…' + value[-8:]

    baseline = f"{100*manifest['baseline_accuracy']:.2f}%"
    candidate = f"{100*manifest['candidate_accuracy']:.2f}%"
    delta = f"+{100*manifest['delta']:.2f} pp"
    log = html.escape((assets / 'worker-log.txt').read_text())
    # Preserve the film's endpoint and all reading holds; vertical is a deliberate reframe.
    starts = [0, 2, 6, 10, 14, 18, 20] if not vertical else [0, 1.8, 5.4, 9, 12.8, 16.6, 18]
    scenes = [
        ('hook', '<div class="hook-copy"><h1 class="enter">PAY FOR IMPROVEMENT.</h1><p class="enter">Not compute hours.</p></div>'),
        ('target', f'<div class="two"><div class="statement"><p class="eyebrow enter">01 / COMMIT THE TARGET</p><h1 class="enter">Freeze the target.</h1><p class="body enter">Accuracy. Cutoff. A named validator.</p><p class="data enter">Policy SHA-256</p><p class="hash enter">{small(manifest["policy_sha256"])}</p></div><figure class="panel enter"><img src="assets/policy.png" alt="Actual immutable policy evidence trail" /></figure></div>'),
        ('work', f'<div class="two"><div class="statement"><p class="eyebrow enter">02 / DO THE WORK</p><h1 class="enter">Real CPU training.</h1><p class="body enter">Signed artifacts.</p><p class="plot-label enter">Winning worker training loss 60 actual epochs</p><p class="loss-range enter">{losses[0]:.3f} → {losses[-1]:.3f}</p><p class="plot-foot enter">Epoch 1 → 60 · 3 processes, 1 host</p></div><div class="worker-stack"><figure class="panel enter"><img src="assets/workers.png" alt="Actual submitted models, including disclosed negative control" /></figure><pre class="terminal enter">{log}</pre></div></div>'),
        ('result', f'<div class="result-content"><p class="eyebrow enter">03 / MEASURE THE RESULT</p><h1 class="enter">Measured improvement.</h1><div class="numbers"><div class="enter"><p>Frozen parent</p><strong>{baseline}</strong></div><div class="enter"><p>Best eligible model</p><strong>{candidate}</strong></div><div class="enter"><p>Improvement</p><strong>{delta}</strong></div></div><p class="result-note enter">{manifest["heldout_examples"]} held-out examples · Public Digits task</p><figure class="metrics-ui panel enter"><img src="assets/metrics.png" alt="Actual UI held-out score comparison for this recorded local experiment" /></figure></div>'),
        ('proof', f'<div class="two"><div class="statement"><p class="eyebrow enter">04 / FOLLOW THE EVIDENCE</p><h1 class="enter">HASHED. SIGNED. INSPECTABLE.</h1><p class="body enter">Authenticated evidence. Not proof of training.</p><p class="data enter">Winning adapter</p><p class="hash enter">{small(manifest["artifact_sha256"])}</p></div><div class="proof-stack"><figure class="panel enter"><img src="assets/receipt.png" alt="Actual SHA-256 and expected-validator Ed25519 verification state" /></figure><p class="receipt-proof enter">SHA-256 matched · Expected validator signature verified</p><figure class="lineage-ui panel enter"><img src="assets/lineage.png" alt="Actual parent to accepted model lineage" /></figure></div></div>'),
        ('boundary', '<div class="boundary-copy"><p class="eyebrow enter">THE HONEST BOUNDARY</p><h1 class="enter">Devnet settlement path implemented</h1><p class="pending enter">Live payout evidence pending</p><p class="body enter">This local run selected an eligible winner. No blockchain payment occurred.</p></div>'),
        ('brand', '<div class="brand-copy"><div class="lockup enter"><img src="assets/mark.svg" alt="" /><h1>Gradient<span>Mine</span></h1></div><p class="tagline enter">Measure the work. Reward the improvement.</p></div>'),
    ]
    scene_html = []
    for index, (name, content) in enumerate(scenes):
        start = starts[index]
        end = min(duration, starts[index+1]+.6) if index+1 < len(starts) else duration
        scene_html.append(f'<section id="{name}" class="clip scene" data-start="{start}" data-duration="{end-start:.3f}" data-track-index="{index+1}"><div class="canvas" data-layout-allow-overflow>{content}</div></section>')
    css = '''
*{box-sizing:border-box;margin:0}body{margin:0;background:#0a0a0b;color:#f4f6f8;font-family:Montserrat,sans-serif}#root{width:100%;height:100%;position:relative;overflow:hidden}#bg{position:absolute;inset:0;background:#0a0a0b}.clip,.canvas{position:absolute;inset:0}.canvas{background:#0a0a0b;padding:100px}.eyebrow{font:28px/1.4 "IBM Plex Mono",monospace;color:#b3a9ff;margin-bottom:26px}h1{font-size:80px;font-weight:700;letter-spacing:-.045em;line-height:1.12;max-width:650px}.body{font-size:34px;line-height:1.5;color:#b0b1bf;margin-top:30px;max-width:650px}.data{font:24px/1.5 "IBM Plex Mono",monospace;color:#b0b1bf;margin-top:32px}.hash{font:28px/1.5 "IBM Plex Mono",monospace;color:#b3a9ff;margin-top:8px;white-space:nowrap}.two{height:100%;display:grid;grid-template-columns:.8fr 1.2fr;gap:70px;align-items:center}.statement{align-self:center}.panel{border:1px solid #303039;background:#0a0a0b;border-radius:12px;overflow:hidden;padding:22px}.panel img{display:block;width:100%;height:auto}.hook-copy{padding:230px 40px}.hook-copy h1{font-size:130px;max-width:1660px}.hook-copy p{font-size:46px;color:#b0b1bf;margin-top:28px}.worker-stack,.proof-stack{display:grid;gap:22px;max-width:100%}.terminal{font:20px/1.65 "IBM Plex Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere;padding:24px;border:1px solid #303039;border-radius:12px;background:#141418;color:#b0b1bf}.plot-label{font:24px/1.4 "IBM Plex Mono",monospace;color:#b0b1bf;margin-top:50px}.loss-range{font:30px/1.5 "IBM Plex Mono",monospace;color:#f4f6f8;margin-top:15px}.plot-foot{font:22px/1.5 "IBM Plex Mono",monospace;color:#b0b1bf;margin-top:270px}.result-content{padding-top:60px}#result h1{max-width:1600px;font-size:85px}.numbers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px;margin-top:80px}.numbers p{font-size:28px;color:#b0b1bf;margin-bottom:16px}.numbers strong{font:100px/1.2 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;letter-spacing:-.04em;white-space:nowrap}.numbers>div:last-child strong{color:#b3a9ff}.result-note{font-size:30px;color:#b0b1bf;margin-top:36px}.metrics-ui{margin-top:72px;width:1500px;padding:14px 22px}.boundary-copy{padding:150px 55px}.boundary-copy h1{max-width:1530px;font-size:96px}.pending{font-size:50px;line-height:1.4;color:#b3a9ff;margin-top:40px}.boundary-copy .body{max-width:1450px;font-size:34px}.brand-copy{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px}.lockup{display:flex;align-items:center;gap:32px}.lockup img{width:112px;height:112px}.lockup h1{font-size:145px;max-width:none}.lockup h1 span{color:#b0b1bf}.tagline{font-size:38px;color:#b0b1bf}.footer{position:absolute;left:100px;right:100px;bottom:38px;z-index:20;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #303039;padding-top:22px;font:26px/1.4 "IBM Plex Mono",monospace;color:#b0b1bf}.footer span:first-child{color:#b3a9ff}#thread{position:absolute;inset:0;z-index:15;pointer-events:none;width:100%;height:100%}#thread-line{fill:none;stroke:#b3a9ff;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.display-break{display:block}.receipt-proof{font:26px/1.5 "IBM Plex Mono",monospace;color:#a6e3c3}#film-brand{position:absolute;left:100px;top:58px;z-index:20;display:flex;align-items:center;gap:12px;font-size:28px;color:#b0b1bf}#film-brand img{width:36px;height:36px}
'''
    css += '\n.eyebrow,.data,.hash,.terminal,.plot-label,.loss-range,.plot-foot,.numbers strong,.footer{font-family:"IBM Plex Mono",monospace}\n'
    if vertical:
        css += '''
.canvas{padding:100px 72px}#film-brand{left:72px;top:58px;font-size:32px}.receipt-proof{font-size:30px}.eyebrow{font-size:28px;margin-bottom:30px}h1{font-size:96px;max-width:936px}.body{font-size:38px;max-width:900px}.two{grid-template-columns:1fr;grid-template-rows:auto auto;gap:70px;align-content:center;height:1650px}.statement{align-self:end}.panel{padding:24px}.data{font-size:28px;margin-top:28px}.hash{font-size:36px}.hook-copy{padding:430px 0 0}.hook-copy h1{font-size:118px;max-width:920px}.hook-copy p{font-size:52px;line-height:1.3;margin-top:45px}.worker-stack{gap:30px}.terminal{font-size:24px;line-height:1.6}.plot-label{margin-top:40px;font-size:28px}.loss-range{font-size:42px;margin-top:15px}.plot-foot{margin-top:260px;font-size:26px}#work .two{gap:45px;grid-template-rows:790px auto;height:1700px}#work .worker-stack{align-self:start}#work .panel{max-height:390px;overflow:hidden}#work .terminal{font-size:22px}.result-content{padding-top:120px}#result h1{font-size:105px;max-width:936px}.numbers{grid-template-columns:1fr;gap:55px;margin-top:70px}.numbers>div{display:flex;align-items:center;justify-content:space-between;gap:20px}.numbers p{font-size:30px;max-width:270px}.numbers strong{font-size:94px;letter-spacing:-.06em}.result-note{font-size:34px;line-height:1.5;margin-top:60px}.metrics-ui{width:936px;margin-top:100px}#proof .two{gap:90px;height:1680px}.proof-stack{gap:65px}#proof h1{font-size:110px;max-width:940px}.boundary-copy{padding:350px 0 0}.boundary-copy h1{font-size:104px;max-width:936px}.pending{font-size:60px;margin-top:70px}.boundary-copy .body{font-size:40px;line-height:1.6;margin-top:60px}.lockup{gap:22px;flex-wrap:wrap;justify-content:center}.lockup img{width:96px;height:96px}.lockup h1{font-size:100px}.tagline{font-size:42px;line-height:1.5;max-width:850px;text-align:center}.footer{left:72px;right:72px;bottom:52px;flex-direction:column;gap:10px;align-items:flex-start;font-size:26px}
'''
    # One 60-point carrier preserves identity: its work pose is the actual epoch-loss series.
    def flat(y, x0=140, x1=1780):
        return ' '.join(f'{x0+(x1-x0)*i/59:.2f},{y:.2f}' for i in range(60))
    if vertical:
        plot = ' '.join(f'{95+870*i/59:.2f},{700+(max(losses)-value)/(max(losses)-min(losses))*220:.2f}' for i,value in enumerate(losses))
        poses=[flat(1060,72,1008),flat(1430,72,1008),plot,flat(1450,72,1008),flat(1450,72,1008),flat(1250,72,1008),flat(1110,240,840)]
    else:
        plot = ' '.join(f'{140+565*i/59:.2f},{560+(max(losses)-value)/(max(losses)-min(losses))*265:.2f}' for i,value in enumerate(losses))
        poses=[flat(640),flat(850),plot,flat(650),flat(845),flat(775),flat(655,470,1450)]
    motion = ["const tl=gsap.timeline({paused:true});tl.from('#film-brand',{opacity:0,y:10,duration:.4,ease:'power3.out'},.1);"]
    for index,(name,_) in enumerate(scenes):
        at=starts[index]
        elements=f'#{name} .enter'
        if index:
            previous=scenes[index-1][0]
            # This is the scene transition itself, not a pre-transition exit.
            motion.append(f"tl.to('#{previous} .canvas',{{x:-{width},duration:.6,ease:'power3.inOut'}},{at});")
            motion.append(f"tl.fromTo('#{name} .canvas',{{x:{width}}},{{x:0,duration:.6,ease:'power3.inOut'}},{at});")
        motion.append(f"tl.from('{elements}',{{y:28,opacity:0,duration:.45,stagger:.07,ease:'power2.out'}},{at+.15});")
        if index:
            motion.append(f"tl.to('#thread-line',{{attr:{{points:{json.dumps(poses[index])}}},duration:.7,ease:'sine.inOut'}},{at});")
    motion.append("tl.from('#thread-line',{strokeDashoffset:2200,duration:1.0,ease:'power2.out'},.25);")
    # Per-frame RMS drives only a bounded visual channel on the persistent line.
    motion.append(f"const audioFrames={json.dumps(audio_data['frames'],separators=(',',':'))};")
    motion.append("for(let frame=0;frame<audioFrames.length;frame++){tl.to('#thread-line',{opacity:.62+.13*audioFrames[frame].rms,duration:1/30,ease:'none'},frame/30);}")
    motion.append("window.__timelines['gradientmine']=tl;")
    content=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width={width},height={height}"><title>GradientMine — verified local evidence</title><script src="assets/gsap.min.js"></script><style>{css}</style></head><body><div id="root" data-composition-id="gradientmine" data-start="0" data-width="{width}" data-height="{height}" data-duration="{duration}"><div id="bg"></div><div id="film-brand"><img src="assets/mark.svg" alt="" /><span>GradientMine</span></div>{''.join(scene_html)}<svg id="thread" viewBox="0 0 {width} {height}" aria-hidden="true" data-layout-ignore><polyline id="thread-line" points="{poses[0]}" stroke-dasharray="2200" /></svg><div class="footer"><span>Recorded local experiment</span><span>One trusted validator · No local payout</span></div><audio id="evidence-audio" src="assets/{audio_name}" data-start="0" data-duration="{duration}" data-track-index="20" data-volume="0.6"></audio></div><script>{''.join(motion)}</script></body></html>'''
    (target / 'index.html').write_text(content)
    if vertical:
        for filename in ('hyperframes.json','package.json'):
            shutil.copy(TOUR / 'composition' / filename,target / filename)
    print(target)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--vertical',action='store_true')
    build(parser.parse_args().vertical)
