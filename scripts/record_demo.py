"""Record a genuine 165-second read-only browser demo, then burn accessible captions.

Requires Chromium, Playwright and FFmpeg. Uses only allowlisted public recorded evidence;
never starts a marketplace API, installs a wallet, or fabricates a transaction.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from gradientmine.crypto import digest, safe_json
from scripts.public_evidence import checked_artifacts

ROOT = Path(__file__).resolve().parents[1]
VERIFY = "SHA-256 matches · Ed25519 signature verified against the expected signer."


class QuietServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".local/submission-videos/demo")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Choose an empty output directory to preserve existing footage")
    out.mkdir(parents=True, exist_ok=True)
    record_path = ROOT / "web/assets/recorded-run.json"
    run = safe_json(record_path.read_bytes(), limit=2_000_000)
    job = run["job"]
    assert run["mode"] == job["mode"] == "local" and job["state"] == "EVALUATED"
    assert not job["funding_signature"] and not job["settlement_signature"]
    artifacts = checked_artifacts(job, lambda sha: (ROOT / f"web/assets/artifacts/{sha}.json").read_bytes())
    assert set(artifacts) == set(run["artifacts"])
    winner = next(sub for sub in job["submissions"] if sub["id"] == job["winner"]["submission_id"])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    handler = functools.partial(QuietServer, directory=str(ROOT / "web"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    checks, errors, writes = [], [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=shutil.which("chromium"))
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(out / "original"),
                record_video_size={"width": 1920, "height": 1080},
                locale="en-US", timezone_id="UTC", reduced_motion="reduce",
            )
            context.grant_permissions(["clipboard-read", "clipboard-write"], origin=origin)
            created = time.monotonic()
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: writes.append(request.url) if request.method != "GET" else None)
            page.goto(origin, wait_until="networkidle")
            page.get_by_text("Recorded local experiment", exact=False).wait_for()
            assert page.locator("#wallet-button").is_disabled()
            assert page.locator("#create-button").is_disabled()
            page.evaluate("document.documentElement.style.zoom = '1.15'")
            started = time.monotonic()
            trim_start = started - created

            def at(seconds, action, description):
                remaining = seconds - (time.monotonic() - started)
                if remaining > 0:
                    page.wait_for_timeout(remaining * 1000)
                action()
                page.screenshot(path=str(out / f"scene-{int(seconds):03}.png"))
                checks.append({"seconds": seconds, "action": description})
                print(f"{seconds:03}s: {description}", flush=True)

            def scroll(selector):
                page.locator(selector).evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
                page.wait_for_timeout(800)

            def close():
                page.locator("#evidence-dialog .close").click()

            def policy():
                page.get_by_role("button", name="Inspect immutable policy", exact=True).click()
                page.get_by_text("SHA-256 matches the referenced exact bytes.", exact=True).wait_for()

            def copy_policy():
                page.locator("#copy-evidence").click()
                assert page.evaluate("navigator.clipboard.readText()") == job["policy_sha256"]

            def receipt():
                row = page.locator("tr.winner")
                row.get_by_role("button", name="Receipt", exact=True).click()
                page.get_by_text(VERIFY, exact=True).wait_for()
                assert page.locator("#evidence-hash").inner_text() == winner["receipt_sha256"]

            def download():
                with page.expect_download() as pending:
                    page.locator("#download-evidence").click()
                target = out / "downloaded-winning-adapter.json"
                pending.value.save_as(target)
                assert digest(target.read_bytes()) == winner["artifact_sha256"]

            at(0, lambda: None, "Real recorded local overview; wallet and creation disabled")
            at(15, policy, "Open and SHA-256 verify immutable policy; full hash visible")
            at(23, copy_policy, "Copy the exact full policy commitment")
            at(34, lambda: page.locator("#evidence-json").evaluate("el => el.scrollTop = 350"),
               "Read named validator, parent and deadline in actual policy JSON")
            at(45, lambda: (close(), scroll(".outcome")), "Read one-host / three-process recorded disclosure")
            at(56, lambda: scroll(".table-wrap"), "Read actual candidate results and disclosed negative control")
            at(67, lambda: page.locator("tr.winner").get_by_role("button", name="Manifest", exact=True).click(),
               "Inspect original worker-signed manifest and real optimization recipe")
            page.get_by_text(VERIFY, exact=True).wait_for()
            at(75, close, "Return to actual completed candidates; no live training chronology claimed")
            at(80, lambda: scroll(".metric-band"), "Read 84.72% parent, 95.28% winner and +10.56 pp / 360 examples")
            at(91, receipt, "Verify winning receipt hash and expected-validator Ed25519 signature")
            at(103, lambda: page.locator("#evidence-json").evaluate("el => el.scrollTop = 580"),
               "Inspect signed approximate paired-bootstrap eligibility report")
            at(115, lambda: (close(), scroll(".outcome")), "Eligible winner is not paid; no blockchain funds moved")
            at(127, lambda: scroll("#trust"), "Read evaluator trust, reconstructible benchmark and test-fund limits")
            at(139, lambda: page.get_by_text("How candidates become eligible", exact=True).click(),
               "Read eligibility correction and statistical limits in actual app")
            at(145, lambda: scroll(".lineage"), "Inspect real parent-to-winner relationship; zero earlier rounds")
            at(151, lambda: page.locator("tr.winner").get_by_role("button", name="Adapter", exact=True).click(),
               "Inspect the winning numeric adapter")
            page.get_by_text("SHA-256 matches the referenced exact bytes.", exact=True).wait_for()
            at(156, download, "Download exact winning adapter and independently verify SHA-256")
            at(160, lambda: (close(), scroll(".metric-band")), "Final hold on actual result; local, not paid")
            at(166, lambda: None, "End continuous original screen capture")
            assert not errors, errors
            assert not writes, writes
            video = page.video
            context.close()
            original = Path(video.path())
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    caption_file = ROOT / "submission/demo-captions.srt"
    shutil.copyfile(caption_file, out / "demo-captions.srt")
    destination = out / "demo.mp4"
    subtitle_filter = (
        f"subtitles={caption_file}:force_style='FontName=DejaVu Sans,FontSize=12,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=3,"
        "Outline=1,Shadow=0,MarginV=18',fps=30"
    )
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(trim_start),
        "-i", str(original), "-t", "165", "-vf", subtitle_filter,
        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ], check=True)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_name,width,height,r_frame_rate,pix_fmt", "-of", "json", str(destination),
    ], text=True))
    assert 164.9 <= float(probe["format"]["duration"]) <= 165.1
    assert probe["streams"][0]["width"] == 1920 and probe["streams"][0]["height"] == 1080
    report = {
        "format": "gradientmine.demo-recording.v1", "source_commit": commit,
        "job_id": job["id"], "recorded_run_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        "mode": "recorded local; read-only; no blockchain payment", "artifact_count": len(artifacts),
        "artifacts": sorted(artifacts), "winner": job["winner"], "checks": checks,
        "browser_errors": errors, "non_get_requests": writes, "ffprobe": probe,
        "mp4_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "captions_sha256": hashlib.sha256(caption_file.read_bytes()).hexdigest(),
        "audio": "None: accessible caption-led screen recording, no synthesized narration or music",
        "original_webm": str(original.relative_to(out)), "trim_initial_navigation_seconds": trim_start,
        "capture": "Continuous genuine Chromium screen capture; only initial navigation and final buffer trimmed",
        "tool_versions": {
            "chromium": subprocess.check_output([shutil.which("chromium"), "--version"], text=True).strip(),
            "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
        },
    }
    (out / "provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"mp4": str(destination), "sha256": report["mp4_sha256"], "probe": probe}, indent=2))


if __name__ == "__main__":
    main()
