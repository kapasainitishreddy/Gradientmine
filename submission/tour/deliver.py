"""Bake the strongest settled poster into frame zero and verify final local films."""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOUR = ROOT / 'submission/tour'


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_entries',
                          'stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration,size',
                          '-of', 'json', str(path)], text=True).stdout)


def audio_hash(path):
    packet_bytes = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a',
                        '-c', 'copy', '-f', 'adts', '-']).stdout
    return hashlib.sha256(packet_bytes).hexdigest()


def main():
    report = {}
    for name, duration, width, height, time in [('landscape', 22, 1920, 1080, 11.8),
                                              ('vertical', 20, 1080, 1920, 11.4)]:
        folder = ROOT / '.local/tour' / name
        video, original, poster = folder / 'brag.mp4', folder / 'brag-unbaked.mp4', folder / 'brag.jpg'
        if not original.exists():
            shutil.copy(video, original)
        before = probe(original)
        run(['ffmpeg', '-y', '-v', 'error', '-ss', str(time), '-i', str(original),
             '-frames:v', '1', '-q:v', '3', str(poster)])
        baked = folder / 'brag-poster.mp4'
        run(['ffmpeg', '-y', '-v', 'error', '-i', str(original), '-i', str(poster),
             '-filter_complex', "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]", '-map', '[v]',
             '-map', '0:a?', '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-preset', 'slow',
             '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(baked)])
        after = probe(baked)
        assert before['format']['duration'] == after['format']['duration'] == f'{duration:.6f}'
        for metadata in (before, after):
            stream = metadata['streams'][0]
            assert (stream['width'], stream['height'], stream['r_frame_rate'], int(stream['nb_frames'])) == (width, height, '30/1', duration * 30)
        assert audio_hash(original) == audio_hash(baked), 'Poster bake must preserve the AAC packet stream'
        result = run(['ffmpeg', '-v', 'info', '-i', str(baked), '-i', str(poster), '-filter_complex',
                      '[0:v]trim=end_frame=1,setpts=PTS-STARTPTS[v];[v][1:v]ssim',
                      '-frames:v', '1', '-f', 'null', '-'], text=True)
        ssim = float(re.search(r'All:([\d.]+)', result.stderr).group(1))
        assert ssim > .99, ssim
        run(['ffmpeg', '-v', 'error', '-i', str(baked), '-f', 'null', '-'])
        baked.replace(video)
        run(['ffmpeg', '-y', '-v', 'error', '-i', str(video), '-vf',
             f'fps=1,scale={270 if name == "vertical" else 480}:-1,tile=5x5',
             '-frames:v', '1', str(folder / 'review.jpg')])
        report[name] = {'file': str(video.relative_to(ROOT)), 'poster': str(poster.relative_to(ROOT)),
                        'sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
                        'poster_time_seconds': time, 'poster_frame_zero_ssim': ssim,
                        'audio_packets_preserved': True, 'full_decode': 'passed', 'ffprobe': after}
    assert (ROOT / report['landscape']['poster']).stat().st_size <= 200_000
    shutil.copy(ROOT / report['landscape']['poster'], TOUR / 'poster.jpg')
    (ROOT / '.local/tour/delivery.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
