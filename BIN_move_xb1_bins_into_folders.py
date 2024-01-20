import os
import shutil
from pathlib import Path

CUSTOM_SONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                               "CustomSongSources", "XB1")
for root, dirs, files in os.walk(CUSTOM_SONG_DIR, topdown=True):
    old_id = Path(root).name
    new_id = f"xb1_{old_id}"
    if f"song_{old_id}.bin" not in files:
        continue
    for fname in files:
        if "xb1" in fname:
            continue
        old_fpath = os.path.join(root, fname)
        new_fpath = os.path.join(root, fname.replace(old_id, new_id))
        shutil.move(old_fpath, new_fpath)
    if "xb1" not in root:
        os.rename(os.path.join(CUSTOM_SONG_DIR, old_id),
                  os.path.join(CUSTOM_SONG_DIR, new_id))