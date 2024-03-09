import os
import json

from murmurhash2 import murmurhash2

__tdmx_dir__ = os.path.join("C:\\", "TaikoTDM")
__custom_dir__ = os.path.join(__tdmx_dir__, "customSongs")
__takotako_save__ = os.path.join(__tdmx_dir__, "TakoTako", "saves",
                                 "save.json")

GENRES = {
    0: "Pops",
    1: "Anime",
    2: "Vocaloid",
    3: "Variety",
    4: "Asian",
    5: "Classical",
    6: "Game Music",
    7: "Namco Original",
}


def read_json(json_filepath):
    for e_str in ["utf-8", "utf-8-sig"]:
        try:
            with open(json_filepath, encoding=e_str) as fp:
                return json.load(fp)
        except json.decoder.JSONDecodeError:
            pass


def load_data_jsons(root_dir):
    jsons = {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        if "data.json" not in files:
            continue
        json_path = os.path.join(root, "data.json")
        json_dict = read_json(json_path)
        jsons[json_dict['id']] = json_dict
    return {k: jsons[k] for k in sorted(jsons.keys())}


def songid_to_uid(song_id):
    if str(song_id).isdigit():
        return str(song_id)
    else:
        return str(murmurhash2(song_id.encode("utf-8"), 0xc58f1a7a)
                   & 0xFFFF_FFF)


def load_takotako_save_json_with_songids(song_ids):
    # Read jsons from files
    takotako_scores = read_json(__takotako_save__)
    # Covert TakoTako's UIDs into their corresponding song IDs
    ids = {songid_to_uid(song_id): song_id for song_id in song_ids}
    for score_key, score_dict in takotako_scores.items():
        new_score_dict = {}
        for unique_id, song_dict in score_dict.items():
            if unique_id in ids.keys():
                new_score_dict[ids[unique_id]] = song_dict
        takotako_scores[score_key] = new_score_dict
    # Split dict of dict into two dicts
    return takotako_scores['m'], takotako_scores['r']
