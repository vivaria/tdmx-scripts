import os
import shutil

CUSTOM_SONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                               "CustomSongSources", "XB1")
for root, dirs, files in os.walk(CUSTOM_SONG_DIR, topdown=True):
    for dir_name in dirs:
        filename = f"song_{dir_name}.bin"
        shutil.move(os.path.join(root, filename),
                    os.path.join(root, dir_name, filename))
