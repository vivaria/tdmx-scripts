import os
import json

# Create ID: NAME dict
CUSTOM_SONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")
ids = {}
tjas = []
for root, dirs, files in os.walk(CUSTOM_SONG_DIR, topdown=True):
    if "data.json" in files:
        json_path = os.path.join(root, "data.json")
        json_dict = json.load(open(json_path, encoding="utf-8-sig"))
        song_id = json_dict['id']
        try:
            song_name = json_dict["songName"]["enText"]
            if not song_name:
                raise KeyError
        except KeyError:
            song_name = json_dict["songName"]["text"]
        ids[song_id] = song_name
        if song_id.isdigit():
            tjas.append([song_name, song_id])

XB1 = [
    'castle',
    'clsca',
    'cna4',
    'doomn',
    'eva',
    'fgod',
    'kekka2',
    'kim4ra',
    'mikuik',
    'ninjas',
    'noshou',
    'railgn',
    'rot',
    'stg0',
    'struck',
    'sweep1',
    'thbad',
    'thchil',
    'tkmdst',
    'udtmgl',
    'weare0',
    'yorukk',
]

# Parse dojo data into new json
DOJO_DIR = os.path.join("C:\\", "TaikoTDM", "BepInEx", "data", "DaniDojo")
json_dict_new = {}
unknown_ids = []
known_ids = []
for root, dirs, files in os.walk(DOJO_DIR, topdown=True):
    for file in files:
        if not file.endswith('.json'):
            continue
        json_path = os.path.join(root, file)
        json_dict = json.load(open(json_path, encoding="utf8"))
        dan_name = json_dict['danSeriesTitle']
        if dan_name == "Testing":
            continue
        json_dict_new[dan_name] = {}
        for course in json_dict['courses']:
            course_name = course['title']
            json_dict_new[dan_name][course_name] = []
            for song in course['aryOdaiSong']:
                song_id = song['songNo']
                try:
                    song_name = ids[song_id]
                except KeyError:
                    if song_id in XB1:
                        song_name = 'XB1'
                    else:
                        song_name = 'Unknown'
                        unknown_ids.append(song_id)
                if song_name == 'Unknown':
                    known_ids.append([song_id, song_name, dan_name, course_name])
                else:
                    known_ids.append([song_id, song_name])
                json_dict_new[dan_name][course_name].append({
                    'song_id': song_id,
                    'song_name': song_name
                })

for course_name, course in json_dict_new.items():
    with open(f'danidojo_jsons/{course_name}.json', 'w', encoding='utf8') as json_file:
        json.dump(course, json_file, ensure_ascii=False, indent=2)

print("\nDan-i Dojo Songs")
for song in sorted(known_ids):
    print(song)

print("\nTJA songs")
for song in sorted(tjas):
    print(song)




