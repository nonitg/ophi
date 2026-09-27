"""Frame-to-frame change of a clip, to spot jank (spikes) or dead holds. Usage: python3 tools/motion-check.py clip.mp4"""
import subprocess, sys
import numpy as np

W, H = 320, 180
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
for i in range(0, len(d), 6):
    seg = d[i:i + 6]
    print(f"{i:4d} " + " ".join(f"{x:5.2f}" for x in seg) + "  " + "#" * int(seg.max() * 4))
spikes = [i for i in range(1, len(d) - 1) if d[i] > 3 * max(0.3, (d[i - 1] + d[i + 1]) / 2)]
print("spikes (frame after):", spikes)
