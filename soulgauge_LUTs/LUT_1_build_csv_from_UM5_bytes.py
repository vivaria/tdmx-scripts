import os
import json
import csv

from tja2fumen.parsers import readFumen
from tja2fumen.constants import COURSE_IDS

CUSTOMSONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                              "CustomSongSources", "UM5")

stars_notes_byte = {}
for root, dirs, files in os.walk(CUSTOMSONG_DIR, topdown=True):
    if "Gen2Converts" not in root and "Gen3" not in root:
        continue
    if "data.json" in files:
        json_path = os.path.join(root, "data.json")
        json_dict = json.load(open(json_path, encoding="utf8"))
        name = json_dict['songName']['enText']
        for difficulty in ['Easy', 'Normal', 'Hard', 'Mania', 'Ura']:
            stars = json_dict[f'star{difficulty}']
            if not stars:
                continue
            path = os.path.join(root, f"{json_dict['id']}_{COURSE_IDS[difficulty]}.bin")
            song = readFumen(open(path, "rb"))
            notes = song['totalNotes'][0]
            sgbyte = int(song['headerUnknown'][12])
            sgbyte2 = int(song['headerUnknown'][13])
            sgval = sgbyte + (255 * sgbyte2)
            key = ''
            if difficulty in ['Mania', 'Ura']:
                if 9 <= stars:
                    key = f"Oni-9-10"
                elif stars == 8:
                    key = f"Oni-8"
                elif stars <= 7:
                    key = f"Oni-1-7"
            elif difficulty == 'Hard':
                if 5 <= stars:
                    key = f"Hard-5-8"
                elif stars == 4:
                    key = f"Hard-4"
                elif stars == 3:
                    key = f"Hard-3"
                elif stars <= 2:
                    key = f"Hard-1-2"
            elif difficulty == 'Normal':
                if 5 <= stars:
                    key = f"Normal-5-7"
                elif stars == 4:
                    key = f"Normal-4"
                elif stars == 3:
                    key = f"Normal-3"
                elif stars <= 2:
                    key = f"Normal-1-2"
            elif difficulty == 'Easy':
                if 4 <= stars:
                    key = f"Easy-4-5"
                elif 2 <= stars <= 3:
                    key = f"Easy-2-3"
                elif stars <= 1:
                    key = f"Easy-1"
            else:
                breakpoint()
            if key not in stars_notes_byte.keys():
                stars_notes_byte[key] = []
            stars_notes_byte[key].append([notes, sgbyte, sgbyte2, sgval])
for key, snb_list in stars_notes_byte.items():
    snb_list = sorted(snb_list)
    with open(f'byte1213_{key}.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile)
        for snb in snb_list:
            spamwriter.writerow(snb)
