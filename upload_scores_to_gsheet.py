#!/usr/bin/env python3

"""
Interfacing with Google Sheets using Python.
"""

# stdlib
import sys

# third party libraries
import pygsheets
import pandas

# personal utility libraries
from utils import (load_takotako_save_json_with_songids, load_data_jsons,
                   GENRES, __custom_dir__)


def generate_highscore_spreadsheet(data_jsons, scores):
    entries = {}
    for song_id, data_json in data_jsons.items():
        if song_id in scores:
            score_dicts = scores[song_id]
        else:
            score_dicts = {}
        genre = GENRES[data_json['genreNo']]
        name = data_json['songName']['text']
        detail = data_json['songDetail']['text']
        subtitle = data_json['songSubtitle']['text']
        base_entry = {
            'SongID': song_id,
            'Genre': genre,
            '*': "",
            '*_': "",
            'Title': name,
            'Detail': detail,
            'Subtitle': subtitle,
            'Crown': "",
            'Score': "",
            'Good': "",
            'OK': "",
            'Bad': "",
            'Drumroll': "",
            'Combo': "",
        }
        for diff, index in [('Mania', 3), ('Ura', 4)]:
            if not data_json[f'star{diff}']:
                continue
            entry = base_entry.copy()
            entry['*'] = int(data_json[f'star{diff}'])
            if data_json[f'star{diff}'] == 10:
                if diff == 'Ura':
                    entry["*_"] = data_json['combinedTierUra']
                else:
                    entry["*_"] = data_json['combinedTier']
                if entry["*_"] == 0.0:
                    entry["*_"] = ""
            if diff == 'Ura':
                entry['Title'] += " (Ura)"
                entry['SongID'] += "_ura"
                song_id += "_ura"
            if (len(score_dicts) <= index or
                    'h' not in score_dicts[index] or
                    's' not in score_dicts[index]['h']):
                entries[entry['SongID']] = entry
                continue
            score_dict = score_dicts[index]
            entry['Crown']    = (score_dict['c'] if 'c' in score_dict else 0)
            entry['Score']    = score_dict['h']['s']
            entry['Good']     = score_dict['h']['e']
            entry['OK']       = score_dict['h']['g']
            entry['Bad']      = (score_dict['h']['b'] if 'b' in score_dict['h']
                                 else 0)
            entry['Drumroll'] = (score_dict['h']['r'] if 'r' in score_dict['h']
                                 else 0)
            entry['Combo']    = score_dict['h']['c']
            entries[song_id] = entry
            # peir
            # print(str(entry).encode('ascii', 'ignore'))
    return entries


def main():
    # Load song data from files
    data_jsons = load_data_jsons(__custom_dir__)
    _, scores = load_takotako_save_json_with_songids(data_jsons.keys())

    # Convert song data into high score spreadsheet
    entries = generate_highscore_spreadsheet(data_jsons, scores)

    def order_func(item):
        return [
            (10 - int(item['*'])),
            (1_000_000 - int(item['Score'] if item['Score'] else 0)),
            (20 - float(item['*_'] if item['*_'] else 0)),
            item['Genre'],
        ]

    sorted_entries = sorted([j for j in entries.values()], key=order_func)
    entries = {json_dict['SongID']: json_dict for json_dict in sorted_entries}

    df = pandas.DataFrame.from_dict(entries)
    df = df.transpose()

    # Upload high score spreadsheet to Google Sheets
    gc = pygsheets.authorize(service_file='credentials.json')
    sh = gc.open('Taiko no Tatsujin Score Tracker')
    wks = sh.sheet1
    print("Loaded sheet...")
    wks.set_dataframe(df, (1, 1))
    print("Uploaded sheet...")


if __name__ == '__main__':
    sys.exit(main())



