import os
import json
import csv
import unicodedata
import re
from copy import deepcopy
import shutil
import math
import gzip
import subprocess
import struct

import pandas
import pygsheets

from tja2fumen import parse_fumen
import utils as tdmx_utils
import upload_scores_to_gsheet as upload_utils

# FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is
# deprecated and will change in a future version. Call
# result.infer_objects(copy=False) instead. To opt-in to the future behavior,
# set `pd.set_option('future.no_silent_downcasting', True)`
#   df = df.fillna(nan)
pandas.set_option('future.no_silent_downcasting', True)

CUSTOMSONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")
PLAYLIST_DIR = os.path.join("C:\\", "TaikoTDM", "BepInEx", "data",
                            "AdditionalFilterOptions", "CustomPlaylists")
SHEET_NAME = 'taiko-metadata'
CSV_FILENAME = 'metadata.csv'

# Load song data from files
data_jsons = tdmx_utils.load_data_jsons(CUSTOMSONG_DIR)
_, scores = tdmx_utils.load_takotako_save_json_with_songids(data_jsons.keys())

# Convert song data into high score spreadsheet
entries = upload_utils.generate_highscore_spreadsheet(data_jsons, scores)

###############################################################################
#                               Loading functions                             #
###############################################################################


def find_song_folders(root_dir):
    song_dirs = {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        song_id = None
        for file_name in files:
            match = re.match(r"^song_(.+)\.bin$", file_name)
            if match:
                song_id = match.group(1)
                break
        if song_id is not None:
            song_dirs[song_id] = root
    return song_dirs


def convert_tja(root_dir):
    print(f"- Converting {root_dir}...")
    raw_output = subprocess.Popen(["TJAConvert.exe", root_dir],
                                  stdout=subprocess.PIPE).communicate()[0]
    try:
        decoded_output = raw_output.decode("utf-16").strip("\r\n")
    except UnicodeError:
        raw_output = raw_output.split(b"\r\n")
        decoded_output = []
        for output in raw_output:
            for encoding in ["utf-8", "utf-16"]:
                try:
                    decoded_output.append(output.decode(encoding=encoding))
                except UnicodeError:
                    continue
        decoded_output = "".join(decoded_output)
    gen_dir = [f for f in os.listdir(root_dir) if "[GENERATED]" in f]
    if gen_dir:
        gen_dir = gen_dir[0]
        generate_conversion_json(root_dir, gen_dir)
        gen_dir = os.path.join(root_dir, gen_dir)
    else:
        gen_dir = None
    return decoded_output.strip("\r\n"), gen_dir


def generate_conversion_json(root_dir, gen_dir):
    json_dict = {
        "i": [{
            "f": os.path.join(".", gen_dir),
            "a": 1,
            "s": True,
            "v": 2,
            "e": 0
        }]
    }
    with open(os.path.join(root_dir, 'conversion.json'),
              'w', encoding="utf-16-le") as f:
        json.dump(json_dict, f, separators=(',', ':'))


def find_datajson_folders(root_dir):
    datajson_dirs = {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        if any([f.endswith(".tja") for f in files]) and not dirs:
            output, gen_dir = convert_tja(root)
            print(f"  {output}")
            if gen_dir:
                root = gen_dir
        json_path = os.path.join(root, "data.json")
        if not os.path.isfile(json_path):
            continue
        with open(json_path, encoding="utf-8-sig") as f:
            try:
                json_dict = json.load(f)
                song_id = json_dict['id']
                datajson_dirs[song_id] = root
            except Exception:  # noqa, e.g. if data.json is empty
                print(f"  - WARNING: Cannot read {json_path}")
    return datajson_dirs


def load_metadata_from_gsheet(sheet_name, idx=0):
    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open(sheet_name)
    wks = sh[idx]
    df = wks.get_as_df()
    header = [df.keys().tolist()]
    # Google Sheets converts boolean values to "FALSE" and "TRUE", so want
    # to make sure we interpret these strings as boolean values
    BOOLEAN_STR_MAP = {'FALSE': False, 'False': False, 'false': False,
                       'TRUE': True,   'True': True,   'true': True}
    rows = [[value if value not in BOOLEAN_STR_MAP else BOOLEAN_STR_MAP[value]
             for value in row] for row in df.values.tolist()]
    return header + rows


###############################################################################
#                             Formatting functions                            #
###############################################################################

CSV_HEADERS = {
    # Useful fields for personal editing
    'id': str,
    'id-new': str,
    'genreNo': int,
    'favorite': bool,
    'songName_text': str,
    'songDetail_text': str,
    'songSubtitle_text': str,
    # Custom fields I've added
    'starMax': int,
    'combinedTier': float,
    'combinedTierUra': float,
    'clearTier': str,
    'dfcTier': str,
    'clearTierUra': str,
    'dfcTierUra': str,
    'date': str,
    'debut': str,
    'source': str,
    'volume': float,
    'replaygain': float,
    'order': int,
    # Song metadata that I don't usually care too much about
    'starEasy': int,
    'starNormal': int,
    'starHard': int,
    'starMania': int,
    'starUra': int,
    'shinutiEasy': int,
    'shinutiNormal': int,
    'shinutiHard': int,
    'shinutiMania': int,
    'shinutiUra': int,
    'shinutiEasyDuet': int,
    'shinutiNormalDuet': int,
    'shinutiHardDuet': int,
    'shinutiManiaDuet': int,
    'shinutiUraDuet': int,
    'scoreEasy': int,
    'scoreNormal': int,
    'scoreHard': int,
    'scoreMania': int,
    'scoreUra': int,
    'branchEasy': bool,
    'branchNormal': bool,
    'branchHard': bool,
    'branchMania': bool,
    'branchUra': bool,
    # Fonts
    'songName_font': int,
    'songDetail_font': int,
    'songSubtitle_font': int,
    # File data
    'previewPos': int,
    'fumenOffsetPos': int,
    'tjaFileHash': str,
    'areFilesGZipped': bool,
    'uniqueId': str,
    'songFileName': str,
}
DEFAULT_CSV_VALUES = {key: type_func()
                      for key, type_func in CSV_HEADERS.items()}


def jsons_to_csv(jsons):
    csv_list = [list(CSV_HEADERS.keys())]
    for json_dict in jsons.values():
        json_dict = flatten_dict(json_dict)
        assert len(json_dict.keys()) == len(CSV_HEADERS.keys())
        csv_list.append([json_dict[k] for k in CSV_HEADERS.keys()])
    return csv_list


def csv_to_jsons(csv_list):
    jsons = {}
    keys = csv_list[0]
    for values in csv_list[1:]:
        json_dict = {}
        for k, v in zip(keys, values):
            if CSV_HEADERS[k] == bool:
                json_dict[k] = (v in ["True", True])
            else:
                json_dict[k] = CSV_HEADERS[k](v)

        # make sure data.json dict has all keys from csv
        for key, default_value in DEFAULT_CSV_VALUES.items():
            if key not in json_dict.keys():
                print(f"- WARNING: {json_dict['id']} is missing key '{key}'")
                json_dict[key] = default_value

        json_dict = unflatten_dict(json_dict)
        jsons[json_dict['id']] = json_dict
    jsons = {k: jsons[k] for k in sorted(jsons.keys())}
    return jsons


def flatten_dict(nested_dict):
    flattened_dict = {}
    for outer_key, outer_val in nested_dict.items():
        if isinstance(outer_val, dict):
            for inner_key, inner_val in outer_val.items():
                flattened_dict[f"{outer_key}_{inner_key}"] = inner_val
        else:
            flattened_dict[outer_key] = outer_val

    return flattened_dict


def unflatten_dict(flat_dict):
    nested_dict = {}
    for key, value in flat_dict.items():
        subkeys = key.split("_")
        if len(subkeys) == 1:
            nested_dict[key] = value
        else:
            if subkeys[0] not in nested_dict.keys():
                nested_dict[subkeys[0]] = {}
            nested_dict[subkeys[0]][subkeys[1]] = value

    return nested_dict


###############################################################################
#                          Processing functions (.tja)                        #
###############################################################################


def load_missing_datajson_metadata(root):
    # Load values generated by TakoTako
    json_path = os.path.join(root, "data.json")
    json_dict = flatten_dict(tdmx_utils.read_json(json_path))
    # Add default values if missing
    json_dict = {key: type_func(json_dict[key]) if key in json_dict
                 else type_func()
                 for key, type_func in CSV_HEADERS.items()}
    json_dict = unflatten_dict(json_dict)
    # Fix TakoTako's buggy fumenOffsetPos (`{0, 2000} - offset`)
    old_offset = json_dict['fumenOffsetPos']
    json_dict['fumenOffsetPos'] = 0 if old_offset <= 0 else 2000
    # Set default values for fields with nonzero defaults
    json_dict['volume'] = 1.0
    json_dict['starMax'] = max(
        json_dict['starEasy'],
        json_dict['starNormal'],
        json_dict['starHard'],
        json_dict['starMania'],
        json_dict['starUra']
    )
    json_dict['date'] = '2088-08-08'
    print(f"- Imported {json_dict['songName']['text']} "
          f"({json_dict['songSubtitle']['text']})")
    return json_dict


def gunzip_file(root, fname):
    fpath = os.path.join(root, fname)
    tmp_fpath = os.path.join(root, "temp.bin")
    try:
        with gzip.open(fpath, 'rb') as f_in:
            with open(tmp_fpath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"    Successfully gunzipped {fname}")
        os.remove(fpath)
        shutil.move(tmp_fpath, fpath)
        return True
    except Exception as e:
        print(f"    {fname} couldn't be gunzipped: {e}")
        return False


def gunzip_files(root):
    for file in os.listdir(root):
        if file.endswith(".bin"):
            gunzip_file(root, file)
    return False


def count_notes(fumen, dur):
    n_notes = 0
    n_balloon = 0
    n_drumroll = 0
    for measure in fumen.measures:
        if measure.branches['master'].length:
            branch = measure.branches['master']
        else:
            branch = measure.branches['normal']
        for note in branch.notes:
            if (note.note_type.lower().startswith('don') or
                    note.note_type.lower().startswith('ka')):
                n_notes += 1
            elif note.note_type.lower() == 'balloon':
                if note.hits >= 2 * (note.duration / dur) and note.hits > 15:
                    # print(f"Troll balloon notes identified: {note.hits}")
                    n_balloon += 2 * math.ceil(note.duration / dur)
                else:
                    n_balloon += note.hits
            elif note.note_type.lower() == 'kusudama':
                if note.hits >= 2 * (note.duration / dur) and note.hits > 15:
                    # print(f"Troll kusudama notes identified: {note.hits}")
                    n_balloon += 2 * math.ceil(note.duration / dur)
                else:
                    n_balloon += note.hits
            elif note.note_type.lower() == 'drumroll':
                n_drumroll += math.ceil(note.duration / dur)
            else:
                continue
    return n_notes, n_balloon, n_drumroll


def fix_score(json_dict, song_path):
    difficulites = [("Easy", "e", 150),
                    ("Normal", "n", 125),
                    ("Hard", "h", 100),
                    ("Mania", "m", 80),
                    ("Ura", "x", 80)]
    for (diff_name, diff_suffix, dur) in difficulites:
        if json_dict[f"star{diff_name}"] == 0:
            json_dict[f'score{diff_name}'] = 0
            json_dict[f'shinuti{diff_name}'] = 0
            continue
        # fetch song data from .bin files
        song_id = json_dict['id']
        fname_fumen = f"{song_id}_{diff_suffix}.bin"
        fumen = parse_fumen(os.path.join(song_path, fname_fumen))
        n_notes, n_hits, n_drumrolls = count_notes(fumen, dur)
        # estimate a new value for the points per good
        good_points_estimated = ((1000000 - ((n_hits + n_drumrolls) * 100))
                                 / n_notes)
        good_points_estimated_rounded = math.ceil(good_points_estimated
                                                  / 10.0) * 10
        top_score_estimated = ((good_points_estimated_rounded * n_notes)
                               + (n_hits * 100) + (n_drumrolls * 100))

        json_dict[f'score{diff_name}'] = top_score_estimated
        json_dict[f'shinuti{diff_name}'] = good_points_estimated_rounded

    return json_dict


def update_volume(json_dict, par_dir):
    VOLUME_TO_WRITE = json_dict['volume']
    if VOLUME_TO_WRITE == 0:
        VOLUME_TO_WRITE = 1.0

    song_id = json_dict['id']
    song_path = os.path.join(par_dir, f"song_{song_id}.bin")
    with open(song_path, mode="rb+") as fp:
        byte_string = struct.pack(">f", VOLUME_TO_WRITE)
        fp.seek(0x217)
        fp.write(byte_string)
        print(f"Writing {VOLUME_TO_WRITE} for {song_id}.")


def safe_filename(string):
    return "".join(c for c in string
                   if c.isalpha() or c.isdigit() or c == ' ').rstrip()


def fix_tja_parent_dirname(song_json, song_path):
    is_tja = song_json['tjaFileHash'] != '0'
    if not is_tja or "[GENERATED]" not in song_path:
        return song_path
    gen_dir = os.path.basename(song_path)
    parent_dir = os.path.abspath(os.path.join(song_path, '..'))
    song_name = song_json['songName']['text']
    new_name = safe_filename(song_name)
    new_dir = os.path.join(
        os.path.abspath(os.path.join(parent_dir, '..')),
        new_name
    )
    if new_dir != parent_dir:
        os.rename(parent_dir, new_dir)
    song_path_new = os.path.join(new_dir, gen_dir)
    return song_path_new


###############################################################################
#                          Processing functions (.bin)                        #
###############################################################################

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def order_func(item):
    return [
        item['genreNo'],
        (10 - item['starMax']),
        strip_accents(item['songName']['text']).upper()
    ]


def order_func_2(item):
    song_id = item['id']
    song_id_ura = song_id + "_ura"
    score_omote = (0 if (song_id not in entries
                         or not entries[song_id]['Score'])
                   else entries[song_id]['Score'])
    score_ura = (0 if (song_id_ura not in entries
                       or not entries[song_id_ura]['Score'])
                 else entries[song_id_ura]['Score'])
    if score_omote and not score_ura:
        score_sort = score_omote
        star_sort = item['starMania']
    else:
        score_sort = score_ura
        star_sort = item['starUra']

    has_score = any([score_ura, score_omote])
    sort_value = [
        item['genreNo'],
        not has_score,
        (10 - int(star_sort)),
        (1_000_000 - int(score_sort)),
        item['songName']['text'],
    ]
    return sort_value


def order_func_3(item):
    return [
        (99999999 - int(item['date'].replace('-', ''))),
        item['debut'],
        strip_accents(item['songName']['text']).upper()
    ]


def update_order(jsons):
    ordered_jsons = {}
    ordered_json_list = sorted([j for j in jsons.values()],
                               key=order_func_2)
    for new_order, json_file in enumerate(ordered_json_list):
        json_file['order'] = new_order
        ordered_jsons[json_file['id']] = json_file
    return ordered_jsons


wikiwiki_map = {
    'Extremely Difficult': 20,
    'Difficult': 16,
    'Strong': 12,
    'Moderate': 8,
    'Weak': 3,
    'Misrepresentation': 0,
}

discord_map = {
    'SS': 20,
    'S++': 19,
    'S+': 18,
    'S': 17,
    'A+': 16,
    'A': 13.5,
    'B': 11,
    'C': 8.5,
    'D': 6,
    'E': 3.5,
    'F': 1,
}


def difficult_formula(ww, d):
    clear = -1 if ww not in wikiwiki_map else wikiwiki_map[ww]
    dfc = -1 if d not in discord_map else discord_map[d]
    w_clear, w_dfc = 0.0, 0.0
    if clear >= 0 and dfc >= 0:
        w_clear, w_dfc = 0.5, 0.5
    elif clear >= 0:
        w_clear = 1.0
    elif dfc >= 0:
        w_dfc = 1.0
    return (w_clear * clear) + (w_dfc * dfc)


def compute_difficulty(jsons):
    for song_id, json_dict in jsons.items():
        if json_dict['starMania'] == 10:
            ww = json_dict['clearTier']
            d = json_dict['dfcTier']
            json_dict['combinedTier'] = difficult_formula(ww, d)
        if json_dict['starUra'] == 10:
            ww = json_dict['clearTierUra']
            d = json_dict['dfcTierUra']
            json_dict['combinedTierUra'] = difficult_formula(ww, d)
            # Copy the ura rating into the oni rating if oni != 10
            if json_dict['starMania'] != 10:
                json_dict['combinedTier'] = json_dict['combinedTierUra']

    return jsons


def fix_song_names(jsons):
    for song_id, json_dict in jsons.items():
        json_dict['songFileName'] = f"song_{song_id}"
    return jsons


###############################################################################
#                              Writing functions                              #
###############################################################################


def write_csv(csv_list):
    with open(CSV_FILENAME, 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(csv_list)


def write_jsons(jsons, paths):
    for song_id, song_json in jsons.items():
        json_to_write = deepcopy(song_json)
        if song_id in paths:
            path = paths[song_id]
        else:
            print(f"WARNING: Song '{song_id}' present in spreadsheet, but "
                  f"missing on disk.")
            continue
        if len(song_json['date']) > 4:
            d = f"「{song_json['debut']} - {song_json['date']}」"
            if song_json['songDetail']['text']:
                d += f"{song_json['songDetail']['text']}"
            json_to_write['songDetail']['text'] = d
        str_to_write = json.dumps(json_to_write, indent="\t",
                                  ensure_ascii=False)
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8-sig") \
                as outfile:
            outfile.write(str_to_write)


def write_playlists(song_jsons):
    playlists = {
        'All Songs': lambda j: True
    }
    for order, (playlist_name, cond_func) in enumerate(playlists.items(),
                                                       start=1000):
        songs = []
        for song_id, song_json in song_jsons.items():
            if cond_func(song_id):
                songs.append({
                    "songId": song_json['id'],
                    "genreNo": song_json['genreNo'],
                    "isDlc": True
                })
        playlist_to_write = {
            "playlistName": playlist_name,
            "order": order,
            "songs": songs
        }
        str_to_write = json.dumps(playlist_to_write, indent="\t",
                                  ensure_ascii=False)
        with open(os.path.join(PLAYLIST_DIR, f"{playlist_name}.json"), "w",
                  encoding="utf-8-sig") as outfile:
            outfile.write(str_to_write)


def write_metadata_to_gsheet(metadata, sheet_name):
    flattened_jsons = {sid: flatten_dict(json_dict)
                       for sid, json_dict in metadata.items()}
    sorted_jsons = {sid: {key: type_func(json_dict[key])
                          for key, type_func in CSV_HEADERS.items()}
                    for sid, json_dict in sorted(flattened_jsons.items(),
                                                 key=lambda x: str(x[1]['date']),
                                                 reverse=True)}
    df_out = pandas.DataFrame.from_dict(sorted_jsons)

    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open(sheet_name)
    wks = sh.sheet1
    wks.set_dataframe(df_out.transpose(), (1, 1))


###############################################################################
#                                     Main                                    #
###############################################################################


def main():
    # Fetch metadata from spreadsheet
    metadata_lists = load_metadata_from_gsheet(SHEET_NAME)  # Flattened keys
    metadata_dicts = csv_to_jsons(metadata_lists)           # Nested dicts
    print(f"# of spreadsheet rows loaded:     {len(metadata_dicts)}")

    # Fetch song paths from disk
    song_paths = find_song_folders(CUSTOMSONG_DIR)
    print(f"# of `song_[id].bin` files found: {len(song_paths)}")
    datajson_paths = find_datajson_folders(CUSTOMSONG_DIR)
    print(f"# of `data.json` files found:     {len(datajson_paths)}")

    # Import newly-added songs (e.g. TJAs) and fix them up
    for song_id in set(datajson_paths) - set(metadata_dicts):
        song_path = datajson_paths[song_id]
        song_json = load_missing_datajson_metadata(song_path)
        song_json['areFilesGZipped'] = gunzip_files(song_path)
        song_json = fix_score(song_json, song_path)
        song_path = fix_tja_parent_dirname(song_json, song_path)
        update_volume(song_json, song_path)
        metadata_dicts[song_id] = song_json
        song_paths[song_id] = song_path

    # Update metadata fields
    metadata_dicts = update_order(metadata_dicts)  # Expects nested dicts
    metadata_dicts = compute_difficulty(metadata_dicts)
    metadata_dicts = fix_song_names(metadata_dicts)
    # TODO: Reimplement old features:
    #   1. Updating IDs using values from spreadsheet column
    #   2. Fix overlapping UniqueID values

    # Write the metadata
    write_csv(jsons_to_csv(metadata_dicts))        # Sanity check
    write_jsons(metadata_dicts, song_paths)        # Expects nested dicts
    write_metadata_to_gsheet(metadata_dicts, SHEET_NAME)
    
    print("Metadata uploaded, launching taiko")
    
    # Launch taiko
    subprocess.call(['C:\\TaikoTDM\\Taiko no Tatsujin.exe'])
    
    print("Taiko closed, uploading high scores")
        
    # Once taiko has been closed, run update script
    from upload_scores_to_gsheet import main as upload
    upload()


if __name__ == "__main__":
    print()
    main()
