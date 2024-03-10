import os
import json
import csv
import unicodedata
import shutil
import gzip
import struct
import re
import math
from pathlib import Path

import pandas
import pygsheets
from tja2fumen.parsers import parse_fumen

DEBUG = False
CUSTOMSONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")
UM_SONG_DIR = os.path.join("D:\\", "games", "TaikoTDM", "CustomSongSources",
                           "UM5")
CSV_FILENAME = 'metadata.csv'

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
    'date': str,
    'debut': str,
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


def load_songs(root_dir):
    jsons, song_dirs = {}, {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # check for presence of a fumen song file, and extract the ID from it
        song_id = None
        for file_name in files:
            match = re.match(r"^song_(.+)\.bin$", file_name)
            if match:
                song_id = match.group(1)
                break
        # if song isn't found, then skip this folder
        if song_id is None:
            continue

        print(f"Processing {song_id}...")

        # keep track of song directories
        song_dirs[song_id] = root

        # handle data.json files
        # case 1: no data.json file -> instantiate one from csv headers
        if "data.json" not in files:
            print(f"  - WARNING: {song_id} is missing data.json")
            jsons[song_id] = unflatten_dict(DEFAULT_CSV_VALUES.copy())
            jsons[song_id]["id"] = song_id
            continue

        # case 2: data.json exists, try to load
        json_path = os.path.join(root, "data.json")
        with open(json_path, encoding="utf-8-sig") as f:
            # case 2a: data.json can be loaded
            try:
                json_dict = json.load(f)
            # case 2b: data.json can't be loaded, so instatiate from csv
            except Exception:  # noqa, e.g. if data.json is empty
                print(f"  - WARNING: {song_id} has empty data.json")
                jsons[song_id] = unflatten_dict(DEFAULT_CSV_VALUES.copy())
                jsons[song_id]["id"] = song_id
                continue

        # sanity check: ensure song_{id}.bin matches 'id': {id}
        # assert song_id == json_dict['id']

        # Flatten for metadata correction
        json_dict = flatten_dict(json_dict)

        # add any missing default values
        for key, value in DEFAULT_CSV_VALUES.items():
            if key not in json_dict.keys():
                if key == 'starMax':
                    json_dict['starMax'] = max(
                        json_dict['starEasy'],
                        json_dict['starNormal'],
                        json_dict['starHard'],
                        json_dict['starMania'],
                        json_dict['starUra']
                    )
                else:
                    json_dict[key] = value

        # remove any extraneous song metadata fields
        song_fields = [k for k in json_dict.keys()
                       if (k.startswith("song") and "_" in k)]
        for field in song_fields:
            parent, child = field.split("_")
            if child.startswith("en"):
                field_alt = f"{parent}_{child[2:]}"
                if field_alt in json_dict and json_dict[field_alt]:
                    continue
                else:
                    print(f"  - Replacing {field_alt} with {field} "
                          f"({json_dict[field]})...")
                    json_dict[field_alt] = json_dict[field]
            if any(child.startswith(ln) for ln in ["en", "jp", "kr"]):
                print(f"  - Ignoring {field}: '{json_dict[field]}'...")
                del json_dict[field]

        json_dict = unflatten_dict(json_dict)

        # store the loaded data.json file
        jsons[song_id] = json_dict

    # sort the songs by ID
    jsons = {k: jsons[k] for k in sorted(jsons.keys())}
    song_dirs = {k: song_dirs[k] for k in sorted(song_dirs.keys())}

    return song_dirs, jsons


def write_jsons(jsons, paths):
    for song_id, path in paths.items():
        str_to_write = json.dumps(jsons[song_id], indent="\t",
                                  ensure_ascii=False)
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8-sig") \
                as outfile:
            outfile.write(str_to_write)


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
                print(f"  - WARNING: {json_dict['id']} is missing key '{key}'")
                json_dict[key] = default_value

        json_dict = unflatten_dict(json_dict)
        jsons[json_dict['id']] = json_dict
    jsons = {k: jsons[k] for k in sorted(jsons.keys())}
    return jsons


def order_func(item):
    return [
        item['genreNo'],
        (10 - item['starMax']),
        strip_accents(item['songName']['text']).upper()
    ]


def update_order(jsons):
    ordered_jsons = {}
    ordered_json_list = sorted([j for j in jsons.values()],
                               key=order_func)
    for new_order, json_file in enumerate(ordered_json_list):
        json_file['order'] = new_order
        ordered_jsons[json_file['id']] = json_file
    return ordered_jsons


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def readStruct(file, format, seek=None):
    if seek:
        file.seek(seek)
    return struct.unpack(">" + format,
                         file.read(struct.calcsize(">" + format)))


def update_volume(jsons, paths, volumes=None):
    for song_id, json_dict in jsons.items():
        if volumes and song_id in volumes:
            VOLUME_TO_WRITE = volumes[song_id]
            test = None
        else:
            VOLUME_TO_WRITE = json_dict['volume']
        if VOLUME_TO_WRITE == 0:
            VOLUME_TO_WRITE = 1.0

        # Get song filename
        par_dir = paths[song_id]
        song_path = os.path.join(par_dir, f"song_{song_id}.bin")
        assert os.path.isfile(song_path)

        # Handle gzipped files
        is_gzipped = json_dict["areFilesGZipped"]
        if is_gzipped:
            # backup original song
            song_path_gzip = song_path + ".gzip"
            shutil.move(song_path, song_path_gzip)
            # unzip song
            with gzip.open(song_path_gzip, 'rb') as f_in:
                with open(song_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        if not DEBUG:
            with open(song_path, mode="rb") as fp:
                volume_float_before = readStruct(fp, "f", seek=0x217)[0]
            with open(song_path, mode="rb+") as fp:
                if volume_float_before != VOLUME_TO_WRITE:
                    byte_string = struct.pack(">f", VOLUME_TO_WRITE)
                    fp.seek(0x217)
                    fp.write(byte_string)
                    print(f"Writing {VOLUME_TO_WRITE} for {song_id}.")
                else:
                    print(f"Volume for {song_id} is: {volume_float_before}")
            with open(song_path, mode="rb") as fp:
                volume_float_after = readStruct(fp, "f", seek=0x217)[0]
            if volume_float_before != volume_float_after:
                print(f"Changed volume from {volume_float_before} to "
                      f"{volume_float_after} for {song_id}.")

        json_dict['volume'] = VOLUME_TO_WRITE

        # Rezip song
        if is_gzipped:
            # unzip song
            with open(song_path, 'rb') as f_in:
                with gzip.open(song_path_gzip, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            shutil.move(song_path_gzip, song_path)

    return jsons


def fetch_volume(jsons, paths):
    volumes = {}
    for song_id, json_dict in jsons.items():
        # Get song filename
        par_dir = paths[song_id]
        song_path = os.path.join(par_dir, f"song_{song_id}.bin")
        assert os.path.isfile(song_path)

        # Handle gzipped files
        is_gzipped = json_dict["areFilesGZipped"]
        if is_gzipped:
            # backup original song
            song_path_gzip = song_path + ".gzip"
            shutil.move(song_path, song_path_gzip)
            # unzip song
            with gzip.open(song_path_gzip, 'rb') as f_in:
                with open(song_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        with open(song_path, mode="rb") as fp:
            volumes[song_id] = readStruct(fp, "f", seek=0x217)[0]

        # Rezip song
        if is_gzipped:
            # unzip song
            with open(song_path, 'rb') as f_in:
                with gzip.open(song_path_gzip, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            shutil.move(song_path_gzip, song_path)

    return volumes


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


def validate_score(jsons, paths):
    for song_id, path in paths.items():
        print(f"\nProcessing {song_id}...")
        json_dict = jsons[song_id]
        if json_dict['areFilesGZipped']:
            for file in os.listdir(path):
                if file.endswith(".bin"):
                    gunzip_file(path, file)
            json_dict['areFilesGZipped'] = False
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
            fname_fumen = f"{song_id}_{diff_suffix}.bin"
            fumen = parse_fumen(os.path.join(path, fname_fumen))
            n_notes, n_hits, n_drumrolls = count_notes(fumen, dur)
            # fetch info from data.json
            good_points_json = json_dict[f'shinuti{diff_name}']
            top_score_json_estimated = ((good_points_json * n_notes)
                                        + (n_hits * 100) + (n_drumrolls * 100))
            # estimate a new value for the points per good
            good_points_estimated = ((1000000 - ((n_hits + n_drumrolls) * 100))
                                     / n_notes)
            good_points_estimated_rounded = math.ceil(good_points_estimated
                                                      / 10.0) * 10
            top_score_estimated = ((good_points_estimated_rounded * n_notes)
                                   + (n_hits * 100) + (n_drumrolls * 100))

            if abs(top_score_estimated - top_score_json_estimated):
                print(f"{song_id} - {json_dict['songName']['text']} ({diff_name}):\n"
                      f" - Estimate: {good_points_estimated_rounded} | "
                      f"Actual: {good_points_json} | "
                      f"Diff: {abs(good_points_estimated_rounded - good_points_json)}\n"
                      f" - Estimate: {top_score_estimated} | "
                      f"Actual: {top_score_json_estimated} | "
                      f"Diff: {abs(top_score_estimated - top_score_json_estimated)}\n"
                      f" - Notes: {n_notes} | "
                      f"Hits: {n_hits} | "
                      f"Drumrolls: {n_drumrolls}")
            json_dict[f'score{diff_name}'] = top_score_estimated
            json_dict[f'shinuti{diff_name}'] = good_points_estimated_rounded

    return jsons


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


def update_ids(paths, jsons):
    for song_id, data_json in jsons.copy().items():
        song_id_new = data_json['id-new']
        if song_id_new.strip():
            # update the metadata to be written to data.json/CSV files
            data_json['id'] = song_id_new
            data_json['songFileName'] = f"song_{song_id_new}"
            data_json['id-new'] = ''
            jsons[song_id_new] = data_json
            del jsons[song_id]
            # get the old path of the song and change it to the new id
            song_path = paths[song_id]
            root_dir = os.path.split(song_path)[0]
            song_path_new = os.path.join(root_dir, song_id_new)
            # rename all files in the folder
            for fname in os.listdir(song_path):
                if song_id in fname:
                    new_fname = fname.replace(song_id, song_id_new)
                    shutil.move(os.path.join(song_path, fname),
                                os.path.join(song_path, new_fname))
            # rename the folder itself
            if song_path != song_path_new:
                os.rename(song_path, song_path_new)
            paths[song_id_new] = song_path_new
            del paths[song_id]
            # fixup TakoTako's conversion.json (if it exists)
            conversion_path = os.path.join(root_dir, "conversion.json")
            if os.path.isfile(conversion_path):
                with open(os.path.join(root_dir, "conversion.json"),
                          encoding="utf-16") as f:
                    conversion_json = json.load(f)
                    conversion_json['i'][0]['f'] = f".\\{song_id_new}"
                str_to_write = json.dumps(conversion_json, indent="\t",
                                          ensure_ascii=False)
                with open(conversion_path, "w", encoding="utf-8-sig") as f:
                    f.write(str_to_write)

    return paths, jsons


def load_metadata_from_gsheet(sheet_name):
    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open(sheet_name)
    wks = sh.sheet1
    df = wks.get_as_df()
    return [df.keys().tolist()] + df.values.tolist()


def write_metadata_to_gsheet(metadata, sheet_name):
    flattened_jsons = {sid: flatten_dict(json_dict)
                       for sid, json_dict in metadata.items()}
    sorted_jsons = {sid: {key: type_func(json_dict[key])
                          for key, type_func in CSV_HEADERS.items()}
                    for sid, json_dict in flattened_jsons.items()}
    df_out = pandas.DataFrame.from_dict(sorted_jsons)

    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open(sheet_name)
    wks = sh.sheet1
    wks.set_dataframe(df_out.transpose(), (1, 1))


def main():
    # fetch existing songs + metadata within the custom song dir
    print(f"\nLoading songs from {CUSTOMSONG_DIR}...")
    input_paths, input_jsons = load_songs(CUSTOMSONG_DIR)

    # print(f"\nLoading songs from {UM_SONG_DIR}...")
    # um_input_paths, um_input_jsons = load_songs(UM_SONG_DIR)

    # print("\nFetching volume values from UM5 songs...")
    # volumes = fetch_volume(um_input_jsons, um_input_paths)

    # fetch existing csv file and convert it to jsons
    SHEET_NAME = 'taiko-metadata'
    print(f"\nReading in metadata from '{SHEET_NAME}'...")
    input_csv = load_metadata_from_gsheet(SHEET_NAME)
    input_csv_as_jsons = csv_to_jsons(input_csv)

    # copy the metadata from the csv where possible.
    # if song doesn't exist in csv, then copy the data.json contents as-is.
    # this functions as a way of importing new songs into the csv,
    # and ensures that the csv acts as the single source of truth
    # (i.e. make sure you're editing the csv, NOT the data.json files)
    print(f"\nMerging metadata sources...")
    merged_jsons = {}
    for song_id, data_json in input_jsons.items():
        if song_id in input_csv_as_jsons.keys():
            merged_jsons[song_id] = input_csv_as_jsons[song_id]
        else:
            print(f"  - New song ID encountered: {song_id} "
                  f"({data_json['songName']})")
            merged_jsons[song_id] = data_json

    # if "id-new" column is non-zero, then rename the song to the new ID
    input_paths, merged_jsons = update_ids(input_paths, merged_jsons)

    # # fetch data taken from wikiwiki
    # counter = 0
    # ids = [i[0] for i in read_csv("ids.csv")]
    # for i in ids:
    #     i = i.lower()
    #     if i not in merged_jsons.keys() and f"xb1_{i}" not in merged_jsons.keys():
    #         print(i)
    #         counter += 1
    # print(counter)
    # breakpoint()

    print(f"\nCorrecting bad shinuti score values...")
    # merged_jsons = validate_score(merged_jsons, input_paths)

    # modify the 'order' field of the jsons
    print(f"\nUpdating order field...")
    ordered_jsons = update_order(merged_jsons)

    # update the volume byte of each song according to field
    print(f"\nUpdating volume...")
    # ordered_jsons = update_volume(ordered_jsons, input_paths, volumes)

    # wrute the merge list of jsons to gsheet
    write_metadata_to_gsheet(ordered_jsons, SHEET_NAME)

    # write the merged list of jsons to files
    print(f"\nWriting new data.json files...")
    output_csv = jsons_to_csv(ordered_jsons)
    output_jsons = csv_to_jsons(output_csv)
    write_jsons(output_jsons, input_paths)


if __name__ == "__main__":
    main()
