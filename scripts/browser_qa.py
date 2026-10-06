"""Real Chromium UI exercise. Test-only wallet signs real Ed25519 messages to the live API."""

from __future__ import annotations
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import httpx
from playwright.sync_api import sync_playwright

# This wallet exists only in the browser test harness, never in shipped application assets.
TEST_WALLET = r"""
window.addEventListener('wallet-standard:app-ready',async event=>{
 const keys=await crypto.subtle.generateKey('Ed25519',true,['sign','verify']);
 const publicKey=new Uint8Array(await crypto.subtle.exportKey('raw',keys.publicKey));
 const alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
 let n=0n, out=''; for(const b of publicKey)n=n*256n+BigInt(b);
 while(n){out=alphabet[Number(n%58n)]+out;n/=58n;}
 for(const b of publicKey){if(b!==0)break;out='1'+out;}
 const account={address:out,publicKey,chains:['solana:devnet'],features:['solana:signMessage','solana:signTransaction']};
 event.detail.register({version:'1.0.0',name:'QA ephemeral wallet',icon:'',accounts:[account],chains:['solana:devnet'],features:{
  'standard:connect':{version:'1.0.0',connect:async()=>({accounts:[account]})},
  'solana:signMessage':{version:'1.0.0',signMessage:async(...inputs)=>Promise.all(inputs.map(async i=>({signedMessage:i.message,signature:new Uint8Array(await crypto.subtle.sign('Ed25519',keys.privateKey,i.message)),signatureType:'ed25519'})))}
 }});
});
"""


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("evidence/browser"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gm-browser-") as private:
        local_port = port()
        origin = f"http://127.0.0.1:{local_port}"
        env = {**os.environ, "GM_ORIGIN": origin, "GM_MODE": "local", "GM_DATA_DIR": private}
        log = (args.out / "server.log").open("w")
        server = subprocess.Popen(
            [sys.executable, "-m", "gradientmine.cli", "serve", "--port", str(local_port)],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(200):
                try:
                    if httpx.get(origin + "/health", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.1)
            else:
                raise RuntimeError("QA server did not start")
            checks = []
            with sync_playwright() as p:
                executable = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium")
                browser = p.chromium.launch(
                    headless=True, **({"executable_path": executable} if executable else {})
                )
                ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
                ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.add_init_script(TEST_WALLET)
                page.goto(origin)
                page.get_by_text("Live local server", exact=False).wait_for()
                page.wait_for_function("document.documentElement.dataset.motion === 'reduced'")
                checks.append("Reduced-motion preference disables Motion enhancement without disabling the product")
                assert page.locator("html").get_attribute("data-theme") == "void"
                page.get_by_role("button", name="Change color theme", exact=True).click()
                assert page.locator("html").get_attribute("data-theme") == "aurora"
                assert page.locator("#theme-label").inner_text() == "Aurora"
                assert page.evaluate("localStorage.getItem('gradientmine-theme')") == "aurora"
                assert page.locator('meta[name="theme-color"]').get_attribute("content") == "#06131a"
                page.reload()
                page.get_by_text("Live local server", exact=False).wait_for()
                assert page.locator("html").get_attribute("data-theme") == "aurora"
                page.get_by_role("button", name="Change color theme", exact=True).click()
                assert page.locator("html").get_attribute("data-theme") == "paper"
                page.get_by_role("button", name="Change color theme", exact=True).click()
                assert page.locator("html").get_attribute("data-theme") == "void"
                checks.append("Theme control cycles Void/Aurora/Paper, persists safely, and updates browser theme color")
                page.get_by_role("button", name="Connect wallet", exact=True).click()
                page.get_by_role("button", name="QA ephemeral wallet", exact=True).click()
                page.get_by_role("button", name="Disconnect", exact=False).wait_for()
                checks.append("Real Wallet Standard auth with test-only Ed25519 signer and live nonce API")
                page.locator("#create-button").click()
                page.get_by_label("Experiment name").fill("Browser-verified bounty")
                page.locator("input[name=understand]").check()
                page.get_by_role("button", name="Create bounty", exact=True).click()
                page.get_by_role("heading", name="Browser-verified bounty", exact=True).wait_for()
                assert page.locator("#detail").get_by_text("No monetary reward", exact=True).count() == 1
                checks.append(
                    "Authenticated bounty creation against persistent HTTP API, explicitly local with zero funds"
                )
                page.locator("#create-button").focus()
                page.keyboard.press("Enter")
                for _ in range(18):
                    page.keyboard.press("Tab")
                    assert page.evaluate("document.activeElement.closest('#create-dialog') !== null")
                page.keyboard.press("Escape")
                assert page.locator("#create-button").evaluate("el => el === document.activeElement")
                checks.append("Keyboard focus stays in native modal dialogs; Escape restores the invoking control")
                page.get_by_role("button", name="Inspect immutable policy").click()
                page.get_by_text("SHA-256 matches the referenced exact bytes.", exact=True).wait_for()
                page.locator("#evidence-dialog .close").click()
                checks.append("Browser SHA-256 integrity check against actual policy bytes")
                # Untrusted server text is deliberately hostile, never executable HTML or a shell argument.
                attack = '<img src=x onerror="window.__gm_xss=1">'
                malicious_id = "$(printf unsafe);'"

                def hostile_detail(route):
                    response = route.fetch()
                    value = response.json()
                    value["title"] = attack
                    value["id"] = malicious_id
                    value["events"].append({"created": 0, "kind": attack, "message": attack})
                    route.fulfill(response=response, json=value)

                page.route("**/api/jobs/*", hostile_detail)
                page.reload()
                page.get_by_role("heading", name=attack, exact=True).wait_for()
                assert page.locator("#detail img").count() == 0
                assert page.evaluate("window.__gm_xss === undefined")
                assert "--job '$(printf unsafe);'\\''" in page.locator("#worker-command").inner_text()
                page.unroute("**/api/jobs/*", hostile_detail)
                page.reload()
                page.get_by_role("heading", name="Browser-verified bounty", exact=True).wait_for()
                checks.append("Hostile bounty/event strings render as text; copied worker arguments use shell-safe quoting")
                held_refresh = []

                def delayed_refresh(route):
                    if not held_refresh:
                        held_refresh.append(route)
                    else:
                        route.continue_()

                page.route("**/api/jobs/*", delayed_refresh)
                page.get_by_role("button", name="Refresh", exact=True).click()
                page.wait_for_timeout(100)
                assert held_refresh
                page.get_by_role("button", name="Refresh", exact=True).click()
                page.wait_for_timeout(100)
                response = held_refresh[0].fetch()
                stale = response.json()
                stale["title"] = "Stale response must not replace the current bounty"
                held_refresh[0].fulfill(response=response, json=stale)
                page.wait_for_timeout(100)
                assert page.get_by_role("heading", name="Browser-verified bounty", exact=True).count() == 1
                page.unroute("**/api/jobs/*", delayed_refresh)
                checks.append("An older delayed refresh cannot replace a more recent bounty selection or state")
                page.screenshot(path=str(args.out / "live-desktop.png"), full_page=True)
                for width, height in [(390, 844), (360, 800)]:
                    page.set_viewport_size({"width": width, "height": height})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                        f"Horizontal page overflow at {width}"
                    )
                page.screenshot(path=str(args.out / "live-mobile.png"), full_page=True)
                checks.append("360px and 390px mobile layouts without horizontal page overflow")
                # Same built assets, real recorded results. Only API absence is simulated, not data or scores.
                await_config = "**/api/config"
                page.route(
                    await_config,
                    lambda route: route.fulfill(status=404, content_type="application/json", body="{}"),
                )
                page.reload()
                page.get_by_text("Recorded local experiment", exact=False).wait_for()
                page.get_by_text("ASSURANCE CONTRACT", exact=True).wait_for()
                page.get_by_text("GRADIENTMINE ARENA", exact=True).wait_for()
                page.get_by_text("ARTIFACT FIREWALL", exact=True).wait_for()
                page.get_by_text("MODEL PASSPORT", exact=True).wait_for()
                assert page.get_by_text("95.28%", exact=True).count() >= 1
                assert page.get_by_text("+10.56 pp", exact=True).count() >= 1
                assert page.get_by_role("button", name="Download JSON", exact=True).count() == 1
                checks.append("Research-driven assurance contract, arena, artifact firewall and downloadable model passport render from recorded evidence")
                assert page.locator("#wallet-button").is_disabled()
                assert page.locator("#create-button").is_disabled()
                page.get_by_role("button", name="Receipt", exact=True).first.click()
                page.get_by_text(
                    "SHA-256 matches · Ed25519 signature verified against the expected signer.", exact=True
                ).wait_for()
                page.locator("#evidence-dialog .close").click()
                run = json.loads((Path(__file__).resolve().parents[1] / "web/assets/recorded-run.json").read_text())
                validator = run["job"]["policy"]["validator"]
                full_validator = page.get_by_role("button", name=f"Show full validator address: {validator}", exact=True)
                full_validator.click()
                assert full_validator.inner_text() == validator
                full_validator.click()
                page.get_by_role("button", name="Copy full validator address", exact=True).click()
                page.get_by_text("Copied to clipboard.", exact=True).wait_for()
                assert page.evaluate("navigator.clipboard.readText()") == validator
                checks.append("Named validator and model hashes offer keyboard-operable full-value access and copy controls")
                # A slow, closed inspector must never overwrite a newer evidence selection.
                parent_hash = run["job"]["policy"]["parent_sha256"]
                model_hash = run["job"]["winner"]["model_sha256"]
                held = []
                pattern = f"**/artifacts/{parent_hash}.json"
                page.route(pattern, lambda route: held.append(route))
                page.get_by_role("button", name="Inspect parent", exact=True).click()
                page.wait_for_timeout(100)
                assert held
                page.keyboard.press("Escape")
                page.get_by_role("button", name="Inspect model", exact=True).click()
                page.get_by_text("SHA-256 matches the referenced exact bytes.", exact=True).wait_for()
                model_json = page.locator("#evidence-json").inner_text()
                parent_bytes = (Path(__file__).resolve().parents[1] / f"web/assets/artifacts/{parent_hash}.json").read_bytes()
                held[0].fulfill(status=200, content_type="application/json", body=parent_bytes)
                page.wait_for_timeout(100)
                assert page.locator("#evidence-hash").inner_text() == model_hash
                assert page.locator("#evidence-json").inner_text() == model_json, "Closed evidence request overwrote the current model"
                page.unroute(pattern)
                page.keyboard.press("Escape")
                checks.append("A delayed artifact response cannot replace the contents or download of a newer evidence dialog")
                page.screenshot(path=str(args.out / "recorded-mobile.png"), full_page=True)
                page.set_viewport_size({"width": 1440, "height": 1050})
                page.screenshot(path=str(args.out / "recorded-desktop.png"), full_page=True)
                checks.append(
                    "Recorded evidence clearly read-only; exact artifact hash and expected-validator Ed25519 signature verified"
                )
                page.get_by_label("Filter bounties").select_option("open")
                page.get_by_text("No matching bounties.").wait_for()
                page.get_by_label("Filter bounties").select_option("all")
                checks.append("Bounty filter and accessible native dialogs function")
                assert not errors, errors
                checks.append("No browser JavaScript exceptions")
                browser.close()
            result = {
                "status": "passed",
                "checks": checks,
                "wallet_disclosure": "Test-only ephemeral signer; no claim of a real Phantom extension test or Devnet payment.",
                "browser": "Playwright Chromium: no attached local interactive-browser tool available.",
                "screenshots": [
                    "live-desktop.png",
                    "live-mobile.png",
                    "recorded-desktop.png",
                    "recorded-mobile.png",
                ],
            }
            (args.out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result, indent=2))
        finally:
            server.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                server.wait(timeout=5)
            if server.poll() is None:
                server.kill()
            log.close()


if __name__ == "__main__":
    main()
