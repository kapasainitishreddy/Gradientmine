"""Real-browser regression checks for the public Bounty Studio and Judge Tour.

No private keys, no wallets, no remote mutation, no backend deployment.
Run: python -m scripts.studio_browser_qa --out .local/studio-qa
"""
from __future__ import annotations
import argparse
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

class QuietHTTP(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,default=Path(".local/studio-qa"))
    args=ap.parse_args()
    target=args.out.resolve()
    target.mkdir(parents=True,exist_ok=True)
    handler=functools.partial(QuietHTTP,directory=str(ROOT/"web"))
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    origin="http://127.0.0.1:"+str(server.server_port)
    cases=[]
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            context=browser.new_context(viewport={"width":1440,"height":900},accept_downloads=True,reduced_motion="reduce")
            page=context.new_page()
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(origin+"/bounty.html",wait_until="networkidle")
            assert page.locator("#sample").is_visible()
            assert page.locator("#download").is_disabled()
            page.get_by_role("button",name="Load illustrative example").click()
            assert page.locator("#download").is_disabled(), "Must not auto-attest model rights"
            page.locator("#rights").check()
            page.locator("#download").wait_for(state="visible")
            assert page.locator("#download").is_enabled()
            assert "Passes the numeric target ONLY" in page.locator("#candidate-feedback").inner_text()
            with page.expect_download() as dl:
                page.locator("#download").click()
            downloaded=dl.value
            assert downloaded.suggested_filename.endswith(".json")
            destination=target/"sample-bounty-blueprint.json"
            downloaded.save_as(destination)
            policy=json.loads(destination.read_text())
            assert policy["status"]=="UNFUNDED_DESIGN_DRAFT"
            assert policy["economics"]["funds_escrowed"] is False
            assert policy["economics"]["settlement_signature"] is None
            assert policy["objective"]["minimum_delta_proposed"]==8
            assert policy["economics"]["hypothetical_total_owner_budget_sol"]==2.2
            cases.append("draft export, consent and honest illustrative fee")
            page.locator("#target").fill("82")
            assert page.locator("#download").is_disabled()
            assert "Target must improve" in page.locator("#issues").inner_text()
            page.locator("#metric").select_option("latency")
            page.locator("#baseline").fill("400")
            page.locator("#target").fill("200")
            page.locator("#candidateResult").fill("190")
            assert page.locator("#download").is_enabled()
            assert "Passes the numeric target ONLY" in page.locator("#candidate-feedback").inner_text()
            page.locator("#candidateResult").fill("300")
            assert "Misses the frozen target" in page.locator("#candidate-feedback").inner_text()
            cases.append("higher/lower metric arithmetic and invalid thresholds")
            page.locator("#name").fill('Sample bounty <img src=x onerror="alert(1)">')
            assert page.locator('img[onerror]').count()==0
            cases.append("DOM text injection remains inert")
            page.screenshot(path=str(target/"bounty-desktop.png"),full_page=True)

            page.goto(origin+"/judge.html",wait_until="networkidle")
            page.wait_for_function("() => document.querySelector('#evidence-status').textContent.includes('Loaded actual recorded local job')",timeout=15000)
            page.locator('[data-step="3"]').click()
            assert page.locator('[data-panel="3"]').is_visible()
            assert page.locator("#tour-baseline").inner_text()=="84.72%"
            assert page.locator("#tour-selected").inner_text()=="95.28%"
            assert page.locator("#tour-delta").inner_text()=="+10.56 pp"
            assert page.locator("#tour-lower-bound").inner_text()=="+6.11 pp"
            page.locator('[data-step="2"]').click()
            assert page.locator(".evidence-worker").count()==3
            assert "disclosed negative control" in page.locator("#tour-workers").inner_text()
            page.locator('[data-step="4"]').click()
            assert "No finalized funded Devnet" in page.locator('[data-panel="4"]').inner_text()
            page.screenshot(path=str(target/"judge-desktop.png"),full_page=True)
            cases.append("six-step judge evidence comes from recorded-run.json, no payout invented")

            page.route("**/assets/recorded-run.json",lambda route:route.fulfill(status=503,body="not available"))
            page.goto(origin+"/judge.html",wait_until="domcontentloaded")
            page.wait_for_function("() => document.querySelector('#evidence-status').textContent.includes('could not be loaded')",timeout=15000)
            assert page.locator("#tour-baseline").inner_text()=="—"
            cases.append("judge route fails closed if evidence is unavailable")
            page.unroute("**/assets/recorded-run.json")
            context.close()
            browser.close()
            for width in (390,360):
                mobile=p.chromium.launch(headless=True)
                ctx=mobile.new_context(viewport={"width":width,"height":844},is_mobile=True,has_touch=True,reduced_motion="reduce")
                tab=ctx.new_page()
                for filename in ("bounty.html","judge.html"):
                    tab.goto(origin+"/"+filename,wait_until="networkidle")
                    info=tab.evaluate("() => ({body:document.documentElement.scrollWidth,visible:document.documentElement.clientWidth})")
                    assert info["body"]<=info["visible"]+1,(filename,width,info)
                    tab.screenshot(path=str(target/(filename.replace(".html","")+"-"+str(width)+".png")),full_page=True)
                ctx.close()
                mobile.close()
            cases.append("390px and 360px mobile layouts without page-level overflow")
            if errors:
                raise AssertionError("Browser JS errors: "+repr(errors))
    finally:
        server.shutdown()
        server.server_close()
    result={"status":"passed","checks":cases,"browser_errors":errors,"source_mode":"local public read-only assets"}
    (target/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
