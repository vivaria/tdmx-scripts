import os
import json
import csv
import unicodedata

DEBUG = False
# CUSTOMSONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
#                               "CustomSongSources", "Official BINs")
CUSTOMSONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")
CSV_FILENAME = os.path.join(CUSTOMSONG_DIR, 'taiko_song_database.csv')

DATA_JSON = {
    # General song metadata
    'order': int,
    'date': str,
    'debut': str,
    'id': str,
    'genreNo': int,
    # Song details
    'songName_enText': str,
    'songSubtitle_enText': str,
    'songDetail_enText': str,
    'songName_jpText': str,
    'songSubtitle_jpText': str,
    'songDetail_jpText': str,
    'songName_text': str,
    'songSubtitle_text': str,
    'songDetail_text': str,
    'series': str,
    # an easy way of checking if a song is a TJA convert
    'areFilesGZipped': bool,
    # Difficulty-specific metadata
    'starEasy': int,
    'starNormal': int,
    'starHard': int,
    'starMania': int,
    'starUra': int,
    'starMax': int,
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
    # Timing information
    'previewPos': int,
    'fumenOffsetPos': int,
    # Fonts (rarely need to change this)
    'songName_enFont': int,
    'songSubtitle_enFont': int,
    'songDetail_enFont': int,
    'songName_jpFont': int,
    'songSubtitle_jpFont': int,
    'songDetail_jpFont': int,
    'songName_font': int,
    'songSubtitle_font': int,
    'songDetail_font': int,
    'songName_krFont': int,
    'songSubtitle_krFont': int,
    'songDetail_krFont': int,
    # Korean song metadata (never used by me)
    'songName_krText': str,
    'songDetail_krText': str,
    'songSubtitle_krText': str,
    # TJA conversion-specific fields
    'tjaFileHash': str,
    # TakoTako fields
    'uniqueId': str,
    'songFileName': str,
    # Self-referential field to make debugging easier
    'path': str,
}


def read_csv():
    with open(CSV_FILENAME, 'r', newline='', encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        csv_list = [row for row in reader]
    return csv_list


def write_csv(csv_list):
    with open(CSV_FILENAME, 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(csv_list)


def read_jsons(root_dir):
    jsons = {}
    for root, dirs, files in os.walk(root_dir, topdown=True):
        if "data.json" in files and "uras" not in root:
            json_path = os.path.join(root, "data.json")
            with open(json_path, encoding="utf-8-sig") as f:
                try:
                    json_dict = json.load(f)
                except Exception:  # noqa, e.g. if data.json is empty
                    json_dict = {'id': root.split("\\")[-1]}
            for key, key_type in DATA_JSON.items():
                if "_" in key:
                    outer, inner = key.split("_")
                    tmp_key = inner
                    if outer not in json_dict.keys():
                        json_dict[outer] = {}
                    tmp_json = json_dict[outer]
                else:
                    tmp_key = key
                    tmp_json = json_dict

                if tmp_key not in tmp_json.keys():
                    if key_type == str:
                        tmp_json[tmp_key] = ""
                    elif key_type == int:
                        tmp_json[tmp_key] = 0
                    elif key_type == bool:
                        tmp_json[tmp_key] = False
                    else:
                        raise ValueError("Unknown type")
            json_dict['path'] = json_path
            jsons[json_dict['id']] = json_dict

    jsons = {k: jsons[k] for k in sorted(jsons.keys())}
    return jsons


def write_jsons(jsons):
    for json_dict in jsons.values():
        str_to_write = json.dumps(json_dict, indent="\t", ensure_ascii=False)
        with open(json_dict['path'], "w", encoding="utf-8-sig") as outfile:
            outfile.write(str_to_write)


def flatten_dict(nested_dict):
    flattened_dict = {key: "" for key in DATA_JSON.keys()}
    flattened_dict['tjaFileHash'] = 0
    flattened_dict['areFilesGZipped'] = False

    for outer_key, outer_val in nested_dict.items():
        if isinstance(outer_val, dict):
            for inner_key, inner_val in outer_val.items():
                flattened_dict[f"{outer_key}_{inner_key}"] = inner_val
        else:
            flattened_dict[outer_key] = outer_val

    flattened_dict['starMax'] = max(nested_dict['starHard'],
                                    nested_dict['starMania'],
                                    nested_dict['starUra'])

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
    csv_list = [DATA_JSON.keys()]
    for json_dict in jsons.values():
        json_dict = flatten_dict(json_dict)
        assert len(json_dict.keys()) == len(DATA_JSON.keys())
        csv_list.append(list(json_dict.values()))
    return csv_list


def csv_to_jsons(csv_list):
    jsons = {}
    keys = csv_list[0]
    for values in csv_list[1:]:
        json_dict = {}
        for k, v in zip(keys, values):
            if DATA_JSON[k] == bool:
                json_dict[k] = (v in ["True", True])
            else:
                json_dict[k] = DATA_JSON[k](v)
        json_dict = unflatten_dict(json_dict)
        jsons[json_dict['id']] = json_dict
    jsons = {k: jsons[k] for k in sorted(jsons.keys())}
    return jsons


def sort_series_then_title(item):
    prefix = '1' if item['series'] else '2'
    return (
        prefix +
        item['series'] +
        strip_accents(item['songName']['enText']).upper()
    )


def update_order(jsons):
    ordered_jsons = {}
    ordered_json_list = sorted([j for j in jsons.values()],
                               key=sort_series_then_title)
    for i, j in enumerate(ordered_json_list):
        if i != j['order']:
            print(f"Order changed ({j['order']} -> {i}): "
                  f"{j['songName']['enText']}")
        j['order'] = i
        ordered_jsons[j['id']] = j
    return ordered_jsons


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def main():
    # fetch existing data.json files within the custom song dir
    print(f"\nLoading jsons from {CUSTOMSONG_DIR}...")
    input_jsons = read_jsons(CUSTOMSONG_DIR)

    # fetch existing csv file and convert it to jsons
    print(f"\nReading in csv file {CSV_FILENAME}...")
    input_csv = read_csv()
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
            merged_jsons[song_id] = data_json

    # modify the 'order' field of the jsons
    print(f"\nUpdating order field...")
    ordered_jsons = update_order(merged_jsons)

    # write the merged list of jsons to csv (but only if there are new entries)
    print(f"\nWriting new {CSV_FILENAME} file...")
    output_csv = jsons_to_csv(ordered_jsons)
    if not DEBUG:
        write_csv(output_csv)

    # write the merged list of jsons to files
    print(f"\nWriting new data.json files...")
    output_jsons = csv_to_jsons(output_csv)
    if not DEBUG:
        assert len(output_jsons) == len(input_jsons)
        write_jsons(output_jsons)


if __name__ == "__main__":
    main()
