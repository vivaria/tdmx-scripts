import os
import re
import shutil
import json
import unicodedata

INPUT_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                         "CustomSongSources", "UM5")

OUTPUT_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                          "CustomSongSources", "UM5_Sorted")

# Step 1. Read in the existing song data
song_order = []
for root, dirs, files in os.walk(INPUT_DIR, topdown=True):
    if "data.json" in files:
        json_path = os.path.join(root, "data.json")
        json_dict = json.load(open(json_path, encoding="utf-8-sig"))
        try:
            song_name = json_dict["songName"]["enText"]
        except KeyError:
            song_name = json_dict["songName"]["text"]
        song_name_2 = unicodedata.normalize('NFKD', song_name)
        song_name_3 = re.sub(r'[^\w_ -]+', '', song_name).strip()
        max_stars = max(json_dict[f"star{difficulty}"] for difficulty
                        in ['Easy', 'Normal', 'Hard', 'Mania', 'Ura'])
        path_out = os.path.join(OUTPUT_DIR, str(max_stars), song_name_3)
        if not os.path.exists(path_out):
            os.makedirs(path_out, exist_ok=True)
            os.chmod(path_out, 0o777)
        for file in files:
            shutil.copyfile(os.path.join(root, file),
                            os.path.join(path_out, file))
