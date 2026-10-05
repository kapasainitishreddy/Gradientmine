"""Record the real local viewer and source documents for a silent captioned 2:30 pitch.

No wallets, identities, API sessions, invented UI, or generated voice are used. Raw
Chromium footage and final MP4 stay under the ignored .local directory.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import html
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

from playwright.sync_api import sync_playwright

from gradientmine.crypto import digest, safe_json
from scripts.public_evidence import checked_artifacts

ROOT = Path(__file__).resolve().parents[1]
BEATS = [(0, 25), (25, 55), (55, 85), (85, 115), (115, 150)]
MODE = "RECORDED LOCAL EXPERIMENT / READ-ONLY EVIDENCE / NO FUNDS MOVED"


def pitch_sections():
    text = (ROOT / "submission/PITCH.md").read_text()
    sections = re.findall(r"(?ms)^## [0-9][^\n]+\n\n(.*?)(?=^## |\Z)", text)
    if len(sections) != 5:
        raise ValueError("Expected the five exact timed PITCH.md sections")
    return [" ".join(section.replace("“", "").replace("”", "").split()) for section in sections]


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def captions_text():
    import textwrap

    result = []
    for (start, end), section in zip(BEATS, pitch_sections(), strict=True):
        words = section.split()
        chunks, chunk = [], []
        for word in words:
            candidate = textwrap.wrap(
                " ".join([*chunk, word]), width=44, break_long_words=False, break_on_hyphens=False
            )
            if chunk and len(candidate) > 2:
                chunks.append(chunk)
                chunk = []
            chunk.append(word)
        if chunk:
            chunks.append(chunk)
        # Avoid a half-second final word flash; distribute short tails across two readable cues.
        while len(chunks) > 1 and len(chunks[-1]) < 5 and len(chunks[-2]) > 5:
            moved = [chunks[-2][-1], *chunks[-1]]
            if (
                len(textwrap.wrap(" ".join(moved), width=44, break_long_words=False, break_on_hyphens=False))
                > 2
            ):
                break
            chunks[-2].pop()
            chunks[-1] = moved
        consumed = 0
        for chunk in chunks:
            cue_start = start + (end - start) * consumed / len(words)
            consumed += len(chunk)
            cue_end = start + (end - start) * consumed / len(words)
            wrapped = textwrap.wrap(" ".join(chunk), width=44, break_long_words=False, break_on_hyphens=False)
            if len(wrapped) > 2:
                raise ValueError("Caption exceeds two lines")
            result.append(
                f"{len(result) + 1}\n{timestamp(cue_start)} --> {timestamp(cue_end)}\n"
                + "\n".join(wrapped)
                + "\n"
            )
    return "\n".join(result)


def captions_ass(srt):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,32,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,60,60,23,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for cue in srt.strip().split("\n\n"):
        lines = cue.splitlines()
        start, end = lines[1].split(" --> ")
        start, end = [str(int(value[:2])) + value[2:].replace(",", ".")[:-1] for value in (start, end)]
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,," + r"\N".join(lines[2:]))
    return header + "\n".join(events) + "\n"


def excerpt(path, heading):
    text = (ROOT / path).read_text()
    match = re.search(rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise ValueError(f"Missing source section: {path}: {heading}")
    return match[1].strip()


def paragraph(text):
    return "<p>" + html.escape(text).replace("\n", " ") + "</p>"


def document(title, source, body, commit):
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{background:#0a0a0b;color:#eee;font:27px/1.48 Arial,sans-serif;margin:0;padding:52px 90px}}
header{{color:#b7aaff;font-size:20px;letter-spacing:1px}}h1{{font-size:44px;line-height:1.12;margin:25px 0}}
h2{{font-size:29px;margin:22px 0 5px;color:#c7befa}}p{{margin:14px 0}}pre{{font:24px/1.35 monospace;
white-space:pre-wrap;background:#17171a;padding:24px;border-radius:16px}}.source{{color:#999;font-size:19px}}
.columns{{display:grid;grid-template-columns:1fr 1fr;gap:45px}}.logo{{width:160px;height:160px}}
.card{{height:730px;display:flex;flex-direction:column;align-items:center;justify-content:center}}</style>
<header>GRADIENTMINE / REPOSITORY DOCUMENT EXCERPT</header><h1>{html.escape(title)}</h1>
<div class="source">{html.escape(source)} / source {commit[:12]}</div>{body}</html>"""


def prepare_site(out, commit):
    run = safe_json((ROOT / "web/assets/recorded-run.json").read_bytes(), limit=2_000_000)
    job = run["job"]
    if run["mode"] != "local" or job["mode"] != "local" or job.get("settlement_signature"):
        raise ValueError("This recording only supports explicit recorded local evidence")
    artifacts = checked_artifacts(
        job, lambda sha: (ROOT / "web/assets/artifacts" / f"{sha}.json").read_bytes()
    )
    if set(artifacts) != set(run["artifacts"]):
        raise ValueError("The snapshot allowlist differs from strictly checked artifacts")
    site = out / "site"
    shutil.copytree(ROOT / "web", site)
    docs = site / "presentation-docs"
    docs.mkdir()
    shutil.copyfile(ROOT / "submission/logo.svg", docs / "logo.svg")
    logo = """<div class="card"><img class="logo" src="logo.svg" alt="Original GradientMine logo">
<h1 style="font-size:70px">GradientMine</h1><p>Pay for measurable model improvement.</p>
<p style="font-size:25px;color:#aaa">Captioned presentation · no narrator · owner review and upload pending</p></div>"""
    (docs / "logo.html").write_text(document("", "submission/logo.svg", logo, commit))
    source = (ROOT / "program/src/lib.rs").read_text()
    functions = source[
        source.index("    pub fn can_settle(") : source.index("pub fn validate_terms(")
    ].strip()
    escrow = paragraph(excerpt("submission/PRODUCT.md", "Why blockchain here?"))
    escrow += "<h2>Native Rust implementation — source, not Devnet payment evidence</h2><pre>"
    escrow += html.escape(functions) + "</pre>"
    (docs / "escrow.html").write_text(
        document(
            "Why Solana escrow belongs here", "submission/PRODUCT.md + program/src/lib.rs", escrow, commit
        )
    )
    threat = (ROOT / "docs/THREAT_MODEL.md").read_text()
    risks = [
        line
        for line in threat.splitlines()
        if line.startswith("| ")
        and any(
            key in line
            for key in (
                "Fabricated worker score",
                "Benchmark leakage",
                "Copying work",
                "Artifact availability",
            )
        )
    ]
    trust = paragraph(threat.split("\n\n")[1])
    trust += '<div class="columns">'
    for line in risks:
        fields = [item.strip() for item in line.strip("|").split("|")]
        trust += f"<section><h2>{html.escape(fields[0])}</h2>{paragraph(fields[2])}</section>"
    trust += "</div>"
    (docs / "trust.html").write_text(
        document("Trust and limitations", "docs/THREAT_MODEL.md — exact source excerpts", trust, commit)
    )
    market = '<div class="columns">'
    for title in (
        "Initial customer hypothesis",
        "Business-model hypothesis",
        "Go-to-market hypothesis",
        "Honest traction",
    ):
        market += (
            f"<section><h2>{html.escape(title)}</h2>"
            + paragraph(excerpt("submission/PRODUCT.md", title))
            + "</section>"
        )
    market += "</div>"
    (docs / "market.html").write_text(
        document(
            "Customer validation comes next", "submission/PRODUCT.md — exact source excerpts", market, commit
        )
    )
    return site, run, artifacts


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def capture(out, site, run, commit):
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(site))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    shots, errors = [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, executable_path=os.environ.get("CHROMIUM_PATH") or shutil.which("chromium")
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 900},
                record_video_dir=str(out / "raw"),
                record_video_size={"width": 1920, "height": 900},
                reduced_motion="reduce",
                locale="en-US",
                timezone_id="UTC",
            )
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(origin + "/presentation-docs/logo.html")
            page.wait_for_load_state("networkidle")
            # Video begins with page creation; retain the complete raw recording and trim its setup.
            capture_start = time.monotonic()
            pre_roll = 0.6

            def hold(until):
                remaining = until - (time.monotonic() - capture_start)
                if remaining > 0:
                    page.wait_for_timeout(remaining * 1000)

            def shot(name, source):
                elapsed = time.monotonic() - capture_start
                page.screenshot(path=str(out / "frames" / f"{len(shots):02d}-{name}.png"))
                shots.append({"at_seconds": round(elapsed, 3), "name": name, "source": source})
                print(f"Captured {name} at {elapsed:.1f}s", flush=True)

            (out / "frames").mkdir()
            shot("opening-logo", "submission/logo.svg")
            hold(2)
            page.goto(origin + "/")
            page.get_by_text("Recorded local experiment", exact=False).first.wait_for()
            assert page.get_by_role("button", name="Connect wallet", exact=True).is_disabled()
            assert "not paid" in page.locator("tr.winner").inner_text().lower()
            assert "No blockchain funds moved" in page.locator(".outcome").inner_text()
            page.evaluate("document.body.style.zoom='1.12'")
            shot("product-overview", "web/index.html + strictly checked recorded-run.json")
            hold(25)
            page.get_by_role("button", name="Inspect immutable policy", exact=True).click()
            page.get_by_text("SHA-256 matches the referenced exact bytes.", exact=True).wait_for()
            shot("immutable-policy", run["job"]["policy_sha256"])
            hold(43)
            page.goto(origin + "/presentation-docs/escrow.html")
            shot("escrow-implementation", "submission/PRODUCT.md + program/src/lib.rs")
            hold(55)
            page.goto(origin + "/")
            page.locator("tr.winner").wait_for()
            page.evaluate("document.body.style.zoom='1.12'")
            page.locator(".metric-band").scroll_into_view_if_needed()
            shot("measured-results", "Recorded local experiment: held-out results")
            hold(70)
            page.locator("tr.winner").get_by_role("button", name="Receipt", exact=True).click()
            page.get_by_text(
                "SHA-256 matches · Ed25519 signature verified against the expected signer.", exact=True
            ).wait_for()
            shot("verified-winning-receipt", run["job"]["winner"]["receipt_sha256"])
            hold(85)
            page.keyboard.press("Escape")
            page.locator("#trust").scroll_into_view_if_needed()
            shot("explicit-trust", "web/index.html #trust")
            hold(102)
            page.goto(origin + "/presentation-docs/trust.html")
            shot("threat-model", "docs/THREAT_MODEL.md")
            hold(115)
            page.goto(origin + "/presentation-docs/market.html")
            shot("customer-hypotheses", "submission/PRODUCT.md")
            hold(138)
            page.goto(origin + "/")
            page.locator("tr.winner").wait_for()
            page.evaluate("document.body.style.zoom='1.12'")
            shot("evidence-return", "Recorded local experiment, not paid")
            hold(148)
            page.goto(origin + "/presentation-docs/logo.html")
            shot("closing-logo", "submission/logo.svg")
            hold(150)
            video = page.video
            context.close()
            raw = out / "raw" / "presentation-browser.webm"
            video.save_as(str(raw))
            browser.close()
            if errors:
                raise ValueError("Browser exceptions during capture: " + "; ".join(errors))
    finally:
        server.shutdown()
        server.server_close()
    return raw, shots, pre_roll


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / ".local/submission-videos/presentation")
    parser.add_argument("--write-captions", action="store_true", help="Write exact PITCH.md captions only")
    args = parser.parse_args()
    captions = ROOT / "submission/presentation-captions.srt"
    expected = captions_text()
    if args.write_captions:
        captions.write_text(expected)
        return
    if captions.read_text() != expected:
        raise ValueError("Captions differ from the current exact PITCH.md story; regenerate and review")
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use an empty output directory to preserve previous video evidence")
    out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    site, run, artifacts = prepare_site(out, commit)
    raw, shots, pre_roll = capture(out, site, run, commit)
    # Correct raw setup duration from the observed recording length, rather than assuming transport speed.
    raw_duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(raw),
            ],
            text=True,
        ).strip()
    )
    pre_roll = max(0, raw_duration - 150)
    shutil.copyfile(captions, out / "presentation-captions.srt")
    ass = out / "presentation-captions.ass"
    ass.write_text(captions_ass(expected))
    label = out / "mode-label.txt"
    label.write_text(MODE)
    caption_label = out / "caption-label.txt"
    caption_label.write_text("CAPTIONED PRESENTATION / NO NARRATOR / OWNER REVIEW AND UPLOAD PENDING")
    filters = (
        f"trim=start={pre_roll}:duration=150,setpts=PTS-STARTPTS,fps=30,"
        "pad=1920:1080:0:0:color=0x0a0a0b,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='{label}':"
        "fontcolor=0xc7befa:fontsize=24:x=(w-tw)/2:y=912,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile='{caption_label}':"
        "fontcolor=0xaaaaaa:fontsize=19:x=(w-tw)/2:y=944,"
        f"ass='{ass}'"
    )
    mp4 = out / "presentation.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            str(raw),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-vf",
            filters,
            "-t",
            "150",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-threads",
            "4",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(mp4),
        ],
        check=True,
    )
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels",
                "-of",
                "json",
                str(mp4),
            ],
            text=True,
        )
    )
    if abs(float(probe["format"]["duration"]) - 150) > 0.1:
        raise ValueError("Presentation must last exactly 150 seconds")
    # Decode the entire delivered MP4. Fail if even one frame has a decoding error.
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-xerror",
            "-i",
            str(mp4),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ],
        check=True,
    )
    review = out / "review"
    review.mkdir()
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(mp4),
            "-vf",
            "fps=1,scale=384:216,tile=5x6:padding=2:margin=2",
            "-frames:v",
            "5",
            str(review / "timeline-%02d.png"),
        ],
        check=True,
    )
    for second in (0, 5, 27, 45, 58, 75, 88, 105, 120, 140, 149):
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(second),
                "-i",
                str(mp4),
                "-frames:v",
                "1",
                str(review / f"keyframe-{second:03d}.png"),
            ],
            check=True,
        )
    manifest = {
        "format": "gradientmine.captioned-presentation.v1",
        "source_commit": commit,
        "capture_method": "actual Playwright Chromium browser video, real static viewer and source document excerpts",
        "mode": "recorded-local",
        "job_id": run["job"]["id"],
        "run_sha256": digest(run),
        "artifacts": {sha: digest(raw) for sha, raw in artifacts.items()},
        "duration_seconds": 150,
        "mp4_sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(),
        "raw_duration_seconds": raw_duration,
        "setup_trimmed_seconds": pre_roll,
        "shots": shots,
        "probe": probe,
        "audio": "silent AAC stereo; no narrator, no generated voice, no music",
        "captions_sha256": digest(captions.read_bytes()),
        "recording_script_sha256": digest(Path(__file__).read_bytes()),
        "full_file_decode": "passed; every video and audio frame decoded without errors",
        "review_frames": [str(path.relative_to(out)) for path in sorted(review.glob("*.png"))],
        "upload_status": "owner review and upload pending",
        "browser_exceptions": [],
        "private_data_captured": False,
        "source_files": {
            path: digest((ROOT / path).read_bytes())
            for path in (
                "submission/PITCH.md",
                "submission/RECORDING.md",
                "submission/PRODUCT.md",
                "docs/THREAT_MODEL.md",
                "submission/logo.svg",
                "program/src/lib.rs",
                "web/index.html",
                "web/assets/main.mjs",
                "web/assets/style.css",
            )
        },
    }
    (out / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps({"mp4": str(mp4), "duration": 150, "sha256": manifest["mp4_sha256"]}, indent=2), flush=True
    )


if __name__ == "__main__":
    main()
