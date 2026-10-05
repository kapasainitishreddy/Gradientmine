"""Exercise a real non-root image and disposable persistent volume, without public ports."""

import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid


def verify(image):
    name = "gradientmine-qa-" + uuid.uuid4().hex[:12]
    volume = name + "-data"

    def docker(*args):
        result = subprocess.run(["docker", *args], text=True, capture_output=True, check=True)
        return (result.stdout + (result.stderr if args[0] == "logs" else "")).strip()

    def query(code):
        return json.loads(docker("exec", name, "python", "-c", code))

    def start():
        docker("run", "-d", "--name", name, "--read-only", "--tmpfs", "/tmp:size=64m,mode=1777",
               "--security-opt", "no-new-privileges:true", "--cap-drop", "ALL", "--pids-limit", "128",
               "--memory", "2g", "--cpus", "2", "-e", "GM_ORIGIN=http://127.0.0.1:8000",
               "-v", volume + ":/data", image)
        for _ in range(80):
            if docker("inspect", name, "--format", "{{.State.Running}}") != "true":
                raise RuntimeError("Image exited before health: " + docker("logs", name, "--tail", "20"))
            try:
                return query("import json,urllib.request; print(json.dumps(json.load("
                             "urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2))))")
            except subprocess.CalledProcessError:
                time.sleep(0.25)
        raise RuntimeError("Container health did not become ready")

    def remove():
        for args in (("stop", name), ("rm", name)):
            subprocess.run(["docker", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        first = start()
        created = query("""
import json, os
from pathlib import Path
import httpx
from gradientmine.crypto import Identity
from gradientmine.cli import login
assert os.getuid() == 10001
assert not Path('/run/secrets/build_ca').exists()
with httpx.Client(base_url='http://127.0.0.1:8000', timeout=60) as c:
    identity = Identity.create(Path('/data/qa-creator.json'))
    login(c, identity, 'http://127.0.0.1:8000')
    r = c.post('/api/jobs', json={'title':'Container persistence check',
                               'duration_seconds':600,'reward_lamports':0})
    r.raise_for_status()
    assert c.get('/').status_code == 200
    assert c.get('/assets/main.mjs').status_code == 200
    assert c.get('/data/validator.json').status_code == 404
    print(json.dumps(r.json()))
""")
        packages = query("from importlib.metadata import distributions; import json; print(json.dumps("
                         "[{ 'name':d.metadata['Name'],'version':d.version} for d in distributions()]))")
        remove()
        second = start()
        restored = query("import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen("
                         + repr("http://127.0.0.1:8000/api/jobs/" + created["id"]) + ",timeout=10))))")
        assert first["validator"] == second["validator"]
        assert created["policy_sha256"] == restored["policy_sha256"]
        assert created["creator"] == restored["creator"]
        return {"status": "passed", "mode": "local", "public_hosted": False,
                "image_id": docker("image", "inspect", image, "--format", "{{.Id}}"),
                "checks": ["non-root UID 10001 can import and serve restrictive-permission source",
                           "read-only rootfs; durable private volume", "HTTP health, homepage and assets",
                           "authenticated bounty creation", "bounty policy survives container recreation",
                           "same named validator after recreation", "private data path returns 404",
                           "build CA absent from runtime"], "job_id": created["id"],
                "policy_sha256": created["policy_sha256"], "validator": first["validator"],
                "private_keys_exported": False, "packages": packages}
    finally:
        remove()
        subprocess.run(["docker", "volume", "rm", volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", default="gradientmine:verified")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = verify(a.image)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    inventory = sorted(
        package["name"] + "==" + package["version"].removesuffix("+cpu")
        for package in result["packages"] if package["name"].lower() != "gradientmine"
    )
    a.out.with_suffix(".requirements.txt").write_text("\n".join(inventory) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "packages"}, indent=2))


if __name__ == "__main__":
    main()
