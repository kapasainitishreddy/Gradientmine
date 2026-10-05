"""Capture only verified public product panels; never inspect identities or sessions."""
from __future__ import annotations
import contextlib
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from scripts.public_evidence import checked_artifacts

ROOT = Path(__file__).resolve().parents[2]
TOUR = ROOT / 'submission/tour'
ASSETS = TOUR / 'composition/assets'


def main():
    record_path = ROOT / 'web/assets/recorded-run.json'
    record = json.loads(record_path.read_text())
    job = record['job']
    blobs = checked_artifacts(job, lambda sha: (ROOT / 'web/assets/artifacts' / f'{sha}.json').read_bytes())
    winner = job['winner']
    winning = next(s for s in job['submissions'] if s['id'] == winner['submission_id'])
    assert job['mode'] == 'local' and job['state'] == 'EVALUATED'
    assert not any(job.get(k) for k in ('funding_signature', 'settlement_signature', 'refund_signature'))
    ASSETS.mkdir(parents=True, exist_ok=True)
    losses = None
    for path in (ROOT / '.local/final-verification').glob('worker-*/manifest.json'):
        manifest = json.loads(path.read_text())
        if manifest['payload']['artifact_sha256'] == winner['artifact_sha256']:
            losses = json.loads((path.parent / 'losses.json').read_text())
            log = (path.parent / 'worker.log').read_text()
            (ASSETS / 'worker-log.txt').write_text(log)
            (ASSETS / 'losses.json').write_text(json.dumps(losses))
            assert abs(losses[0] - winning['worker_metrics']['first_loss']) < 1e-9
            assert abs(losses[-1] - winning['worker_metrics']['last_loss']) < 1e-9
    if losses is None:
        preserved = json.loads((TOUR / 'evidence-manifest.json').read_text())
        assert preserved['job_id'] == job['id'] and preserved['artifact_sha256'] == winner['artifact_sha256']
        loss_bytes = (TOUR / 'evidence/losses.json').read_bytes()
        assert hashlib.sha256(loss_bytes).hexdigest() == preserved['epoch_losses_sha256']
        losses = json.loads(loss_bytes)
        assert abs(losses[0] - winning['worker_metrics']['first_loss']) < 1e-9
        assert abs(losses[-1] - winning['worker_metrics']['last_loss']) < 1e-9
        shutil.copy(TOUR / 'evidence/losses.json', ASSETS / 'losses.json')
        log_bytes = (TOUR / 'evidence/worker-log.txt').read_bytes()
        assert hashlib.sha256(log_bytes).hexdigest() == preserved['worker_log_sha256']
        shutil.copy(TOUR / 'evidence/worker-log.txt', ASSETS / 'worker-log.txt')
    assert losses is not None, 'Actual winning worker epoch losses are required'
    manifest = {
        'classification': 'Recorded local experiment',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'brag_commit': 'cb89b9f44309b0bf4e3cb89e685fadf80c7999ed',
        'cli_version': '0.8.134', 'current_ci': 'pending; no successful current CI claim',
        'recorded_run_sha256': hashlib.sha256(record_path.read_bytes()).hexdigest(),
        'job_id': job['id'], 'policy_sha256': job['policy_sha256'],
        'validator': job['policy']['validator'],
        **{key: winner[key] for key in ('artifact_sha256', 'model_sha256', 'receipt_sha256')},
        'manifest_sha256': winning['manifest_sha256'],
        'baseline_accuracy': job['baseline_accuracy'], 'candidate_accuracy': winner['candidate_accuracy'],
        'delta': winner['delta'], 'heldout_examples': winner['n'],
        'worker_metrics': winning['worker_metrics'], 'winning_worker_epochs': len(losses),
        'epoch_losses_sha256': hashlib.sha256((ASSETS / 'losses.json').read_bytes()).hexdigest(),
        'worker_log_sha256': hashlib.sha256((ASSETS / 'worker-log.txt').read_bytes()).hexdigest(),
        'chain_signatures': {'funding': job['funding_signature'], 'settlement': job['settlement_signature'],
                             'registration': winning['registration_signature']},
        'checked_artifacts': sorted(blobs), 'disclosure': record['disclosure'],
        'verification': 'checked_artifacts passed: exact hashes, worker/validator signatures, provenance, model merge and deterministic eligible winner',
    }
    (TOUR / 'evidence-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copy(ROOT / 'web/assets/mark.svg', ASSETS / 'mark.svg')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1',
                               '--directory', str(ROOT / 'web')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(.3)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
            page = browser.new_page(viewport={'width': 1600, 'height': 1200}, device_scale_factor=1)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{port}')
            page.get_by_text('Recorded local experiment', exact=False).wait_for()
            assert page.locator('#detail h2').inner_text() == job['title']
            page.locator('#detail .audit').screenshot(path=str(ASSETS / 'policy.png'))
            page.locator('#detail .table-wrap').screenshot(path=str(ASSETS / 'workers.png'))
            page.locator('#detail .metric-band').screenshot(path=str(ASSETS / 'metrics.png'))
            page.locator('#detail .lineage').screenshot(path=str(ASSETS / 'lineage.png'))
            winning_row = page.locator('#detail tr.winner')
            winning_row.get_by_role('button', name='Receipt', exact=True).click()
            page.get_by_text('SHA-256 matches · Ed25519 signature verified against the expected signer.', exact=True).wait_for()
            assert page.locator('#evidence-hash').inner_text() == winner['receipt_sha256']
            page.locator('#evidence-title').click()
            box = page.locator('#evidence-dialog').bounding_box()
            hash_box = page.locator('#evidence-hash').bounding_box()
            page.screenshot(path=str(ASSETS / 'receipt.png'), clip={
                'x': box['x'], 'y': box['y'], 'width': box['width'],
                'height': hash_box['y'] + hash_box['height'] - box['y'] + 28,
            })
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            server.wait(timeout=5)
        if server.poll() is None:
            server.kill()
    print(json.dumps({'status': 'passed', 'job_id': job['id'], 'checked_artifacts': len(blobs),
                      'capture_source': manifest['source_commit'], 'epoch_losses': len(losses)}, indent=2))


if __name__ == '__main__':
    main()
