import os
import json
import csv
import unicodedata
import re

import pandas
import pygsheets

# FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is
# deprecated and will change in a future version. Call
# result.infer_objects(copy=False) instead. To opt-in to the future behavior,
# set `pd.set_option('future.no_silent_downcasting', True)`
#   df = df.fillna(nan)
pandas.set_option('future.no_silent_downcasting', True)

CUSTOMSONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")
SHEET_NAME = 'taiko-metadata'
CSV_FILENAME = 'metadata.csv'

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


def find_datajson_folders(root_dir):
    datajson_dirs = {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        if "data.json" not in files:
            continue
        json_path = os.path.join(root, "data.json")
        with open(json_path, encoding="utf-8-sig") as f:
            try:
                json_dict = json.load(f)
                song_id = json_dict['id']
                datajson_dirs[song_id] = root
            except Exception:  # noqa, e.g. if data.json is empty
                print(f"  - WARNING: Cannot read {json_path}")
    return datajson_dirs


def load_metadata_from_gsheet(sheet_name):
    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open(sheet_name)
    wks = sh.sheet1
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
#                             Processing functions                            #
###############################################################################


def order_func(item):
    def strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')
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


###############################################################################
#                              Writing functions                              #
###############################################################################


def write_csv(csv_list):
    with open(CSV_FILENAME, 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(csv_list)


def write_jsons(jsons, paths):
    for song_id, song_json in jsons.items():
        if song_id in paths:
            path = paths[song_id]
        else:
            print(f"WARNING: Song '{song_id}' present in spreadsheet, but "
                  f"missing on disk.")
            continue
        str_to_write = json.dumps(song_json, indent="\t",
                                  ensure_ascii=False)
        with open(os.path.join(path, "data.json"), "w", encoding="utf-8-sig") \
                as outfile:
            outfile.write(str_to_write)


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
    # TODO: Reconcile differences between spreadsheet and on-disk files:
    #   - Unseen data.jsons -> Import into `metadata_dicts`
    #   - Unseen songs, no data.jsons -> Warn of failed conversion?

    # Update metadata fields
    metadata_dicts = update_order(metadata_dicts)  # Expects nested dicts
    # TODO: Reimplement old features:
    #   1. Updating volume bytes using values from spreadsheet column
    #   2. Updating IDs using values from spreadsheet column
    #   3. gunzipping converted files
    #   4. Fixing score values based on note counts (slow)
    #   5. Computing the starMax field if not already present

    # Write the metadata
    write_csv(jsons_to_csv(metadata_dicts))        # Sanity check
    write_jsons(metadata_dicts, song_paths)        # Expects nested dicts
    write_metadata_to_gsheet(metadata_dicts, SHEET_NAME)


if __name__ == "__main__":
    print()
    main()
