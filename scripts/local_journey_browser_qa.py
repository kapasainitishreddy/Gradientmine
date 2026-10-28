"""Browser proof for the offline, unfunded Bounty Studio evaluation journey."""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "proposal-2026-10-28" / "local-journey"
CHECKS: list[str] = []


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def log_message(self, *_args):
        pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    CHECKS.append(message)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    worktree_clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            options = {"headless": True}
            system_chromium = shutil.which("chromium") or shutil.which("chromium-browser")
            if system_chromium:
                options["executable_path"] = system_chromium
            browser = p.chromium.launch(**options)
            context = browser.new_context(viewport={"width": 1440, "height": 1100}, reduced_motion="reduce")
            page = context.new_page()
            errors: list[str] = []
            external: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: external.append(request.url) if not request.url.startswith(origin) else None)
            page.goto(origin + "/bounty.html", wait_until="networkidle")
            page.get_by_role("button", name="Load illustrative example").click()
            require(not page.locator("#rights").is_checked(), "Example does not self-attest model/data rights")
            page.locator("#rights").check()
            freeze = page.get_by_role("button", name="Freeze this draft for local simulation")
            require(freeze.is_enabled(), "Valid Digits-only draft enables local freeze")
            freeze.focus()
            page.keyboard.press("Enter")
            page.locator("#candidate-admission-card").wait_for(state="visible")
            initial_hash = page.locator("#frozen-policy-hash").inner_text()
            page.locator("#model").fill("changed-after-freeze")
            require(page.locator("#frozen-policy-hash").inner_text() == initial_hash, "Frozen policy hash stays fixed after form edits")
            page.get_by_role("button", name="Load signed synthetic candidate").click()
            candidate_text = page.locator("#candidate-json").input_value()
            candidate = json.loads(candidate_text)
            candidate["artifact"]["A"][0] = [1, 2]
            tampered = json.dumps(candidate, indent=2)
            page.locator("#candidate-json").fill(tampered)
            page.get_by_role("button", name="Check and admit candidate").click()
            page.get_by_role("table", name="Candidate admission checks").wait_for()
            require(page.locator('.local-check-table [data-state="fail"]').count() >= 2, "Invalid shape and substituted bytes are visibly rejected")
            require(page.locator("#evaluate-candidate").is_disabled(), "Rejected candidate cannot enter evaluation")
            page.get_by_role("button", name="Load signed synthetic candidate").click()
            page.get_by_role("button", name="Check and admit candidate").click()
            page.get_by_role("cell", name="PASS", exact=True).first.wait_for()
            require("artifact" in page.locator("#admitted-lineage").inner_text(), "Admission records artifact and baseline lineage")
            require(page.locator("#load-synthetic-candidate").is_disabled(), "Fixture admits at most one candidate despite a larger planning cap")
            frozen_budget=page.locator("#frozen-budget").inner_text().lower()
            require("tie-break" in frozen_budget and "not exercised" in frozen_budget, "Frozen policy discloses that the configured tie-break is not exercised")
            page.get_by_role("button", name="Pause and save checkpoint").click()
            require(page.locator("#resume-local-run").is_visible(), "Interruption saves a resumable checkpoint")
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            require(page.locator("#evaluate-candidate").is_enabled(), "Resume revalidates frozen policy and candidate signature")
            page.get_by_role("button", name="Check and admit candidate").click()
            require(page.locator('.local-check-table [data-state="fail"]').count() == 1, "Duplicate/replayed candidate is rejected after resume")
            page.get_by_role("button", name="Evaluate on synthetic held-out fixture").click()
            page.locator("#receipt-card").wait_for(state="visible")
            require("SYNTHETIC SIGNATURE MATCH" in page.locator("#receipt-status").inner_text(), "Synthetic receipt matches the evaluator key pinned in the frozen policy")
            require("private half is bundled" in page.locator("#receipt-evaluator").inner_text(), "Receipt discloses that the synthetic evaluator key is public demo material")
            require("0.00%" in page.locator("#receipt-scores").inner_text() or "50.00%" in page.locator("#receipt-scores").inner_text(), "Receipt displays an actual synthetic baseline score")
            require("no statistical confidence claim" in page.locator("#receipt-stats").inner_text().lower(), "Receipt states statistical limitation")
            require("no transaction signature" in page.locator("#receipt-settlement").inner_text().lower(), "Receipt labels settlement as unfunded with no signature")
            with page.expect_download() as receipt_download:
                page.get_by_role("button", name="Download synthetic receipt").click()
            download=receipt_download.value
            require(download.suggested_filename=="gradientmine-synthetic-local-receipt.json", "Receipt export uses an explicitly synthetic filename")
            download.save_as("/tmp/gradientmine-synthetic-local-receipt.json")
            exported=json.loads(Path("/tmp/gradientmine-synthetic-local-receipt.json").read_text())
            require(exported["receipt"]["funds_escrowed"] is False and exported["receipt"]["transaction_signature"] is None, "Downloaded receipt preserves unfunded settlement disclosure")
            page.get_by_role("button", name="Simulate lost response").click()
            page.get_by_role("button", name="Reconcile simulation").click()
            require(page.get_by_role("button", name="Reconcile simulation").is_disabled(), "Repeated settlement recovery is disabled after reconciliation")
            recovery = page.locator("#settlement-recovery-status").inner_text().lower()
            require("no transaction was sent" in recovery and "payout count remains 0" in recovery, "Ambiguous response drill reconciles without double payout")
            checkpoint = page.evaluate("localStorage.getItem('gradientmine.local-synthetic-run.v1')")
            saved = json.loads(checkpoint)
            require(saved["settlement_probe"]["payout_count"] == 0 and saved["settlement_probe"]["transaction_signature"] is None, "Settlement recovery checkpoint contains no payment")
            page.screenshot(path=str(EVIDENCE_DIR / "local-journey-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 360, "height": 900})
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            if not page.evaluate("document.documentElement.scrollWidth <= innerWidth"):
                print(json.dumps(page.evaluate("""() => ({iw:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth, offenders:[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,id:e.id,class:e.className,left:Math.round(e.getBoundingClientRect().left),right:Math.round(e.getBoundingClientRect().right),width:Math.round(e.getBoundingClientRect().width),scroll:e.scrollWidth,client:e.clientWidth})).filter(x=>x.right>innerWidth+1||x.left< -1||x.scroll>x.client+20).slice(0,50)})"""), indent=2))
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "360px layout has no horizontal page overflow")
            require("UNFUNDED_SIMULATION_ONLY" in page.locator("#receipt-settlement").inner_text(), "Small-screen receipt retains explicit settlement state")
            page.evaluate("document.documentElement.style.fontSize='200%'")
            require(page.locator("#receipt-settlement").is_visible(), "Receipt remains reachable at 200% text scale")
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "200% text scale does not force horizontal page overflow")
            page.screenshot(path=str(EVIDENCE_DIR / "local-journey-mobile-200pct.png"), full_page=True)
            require(not external, "Offline flow made no external network requests")
            require(not errors, "Browser completed flow without JavaScript exceptions")
            saved_state=page.evaluate("localStorage.getItem('gradientmine.local-synthetic-run.v1')")
            legacy_checkpoint=page.evaluate("""async saved => {
              const local=await import('./assets/local-evaluation.mjs');
              const policy=structuredClone(saved.policy);
              delete policy.local_fixture_candidate_capacity;
              delete policy.policy_sha256;
              policy.policy_sha256=await local.sha256(local.canonicalJSON(policy));
              const submission=await local.createSyntheticSubmission(policy);
              const receipt=await local.evaluateSubmission(submission,policy,[]);
              return {version:1,state:'SYNTHETIC_EVALUATED',policy,submissions:[submission],receipt,settlement_probe:null,cancelled:false};
            }""",json.loads(saved_state))
            legacy_receipt_hash=legacy_checkpoint["receipt"]["receipt_sha256"]
            page.evaluate("state => localStorage.setItem('gradientmine.local-synthetic-run.v1', JSON.stringify(state))",legacy_checkpoint)
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            require(page.locator("#receipt-card").is_visible() and legacy_receipt_hash in page.locator("#receipt-hash").inner_text(), "Legacy v1 evaluated checkpoint resumes with its receipt intact")
            require("legacy frozen cap" in page.locator("#frozen-budget").inner_text().lower(), "Legacy checkpoint is labeled with its original frozen budget")
            page.evaluate("state => localStorage.setItem('gradientmine.local-synthetic-run.v1', state)",saved_state)
            inconsistent_evaluated={**json.loads(saved_state),"state":"INTERRUPTED_CHECKPOINT","resume_state":"SYNTHETIC_EVALUATED","receipt":None}
            page.evaluate("state => localStorage.setItem('gradientmine.local-synthetic-run.v1', JSON.stringify(state))",inconsistent_evaluated)
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            require("state, admitted candidate, receipt, and settlement probe are inconsistent" in page.locator("#local-run-status").inner_text(), "Interrupted evaluated checkpoint without receipt is rejected")
            inconsistent_frozen={**json.loads(saved_state),"state":"INTERRUPTED_CHECKPOINT","resume_state":"FROZEN"}
            page.evaluate("state => localStorage.setItem('gradientmine.local-synthetic-run.v1', JSON.stringify(state))",inconsistent_frozen)
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            require("state, admitted candidate, receipt, and settlement probe are inconsistent" in page.locator("#local-run-status").inner_text(), "Interrupted frozen checkpoint with receipt is rejected")
            tampered_state=json.loads(saved_state)
            tampered_state["policy"]["policy_sha256"]="0"*64
            page.evaluate("state => localStorage.setItem('gradientmine.local-synthetic-run.v1', JSON.stringify(state))",tampered_state)
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Resume saved checkpoint").click()
            require("policy checkpoint hash is invalid" in page.locator("#local-run-status").inner_text(), "Corrupted policy checkpoint is rejected on restore")
            cancel=page.get_by_role("button", name="Cancel this simulation")
            require(cancel.is_visible(), "Invalid saved checkpoint still offers a delete control")
            page.evaluate("""() => { const original=Storage.prototype.removeItem; window.__originalRemoveItem=original; Storage.prototype.removeItem=function(k){if(k==='gradientmine.local-synthetic-run.v1')throw new Error('simulated storage denial');return original.call(this,k)}; }""")
            cancel.click()
            require("could not delete" in page.locator("#local-run-status").inner_text().lower(), "Failed browser storage deletion does not claim success")
            require(page.evaluate("localStorage.getItem('gradientmine.local-synthetic-run.v1')") is not None, "Denied deletion leaves the checkpoint available and undisclaimed")
            page.evaluate("() => { Storage.prototype.removeItem=window.__originalRemoveItem; }")
            page.get_by_role("button", name="Cancel this simulation").click()
            require(page.evaluate("localStorage.getItem('gradientmine.local-synthetic-run.v1')") is None, "Successful cancel deletes the local checkpoint and synthetic receipt")
            page.evaluate("localStorage.setItem('gradientmine.local-synthetic-run.v1','{')")
            page.reload(wait_until="networkidle")
            clear=page.get_by_role("button", name="Delete unreadable checkpoint")
            require(clear.is_visible(), "Unreadable checkpoint exposes a delete control")
            clear.click()
            require(page.evaluate("localStorage.getItem('gradientmine.local-synthetic-run.v1')") is None, "Unreadable checkpoint can be safely discarded")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    report={"status":"passed","source_sha":source_sha,"worktree_clean_before_run":worktree_clean,"checks":CHECKS}
    (EVIDENCE_DIR / "local-journey-browser-qa.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
