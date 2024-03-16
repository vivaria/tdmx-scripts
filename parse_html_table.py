import sys
import unicodedata
import re

import pandas as pd
import pygsheets


tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                    if unicodedata.category(chr(i)).startswith('P'))


def split_subtitles(value):
    value = value.split("  ")[0]         # Remove subtitles
    value = re.sub(r'\*\d+', '', value)  # Remove footnote asterisks
    return value


def normalize_titles(value):
    value = value.replace("ペ", "ぺ")
    value = value.replace("（", "(")
    value = value.replace("）", ")")
    value = value.replace("1", "一")
    value = value.replace("－", "-")
    value = value.replace("／", "/")
    value = value.replace("♢", "◇")
    value = value.replace("Ⅰ", "I")
    value = value.replace("Ⅱ", "II")
    value = value.replace("Ⅲ", "III")
    value = value.replace("Ⅳ", "IV")
    value = value.replace("Ⅷ", "VIII")
    value = value.replace("Ⅸ", "IX")
    value = value.replace("Ⅹ", "X")
    value = value.replace("(裏)", "")
    value = value.replace("「", "")
    value = value.replace("」", "")
    value = value.replace("♥", "♡")
    value = value.replace("★", "☆")
    # value = value.split("(")[0]
    # value = value.split("～")[0]
    value = ''.join(value.split())       # Remove whitespace
    value = value.translate(tbl)         # Remove symbols
    value = value.lower()
    return value


gc = pygsheets.authorize(service_file='credentials.json')
sh = gc.open('wikiwiki.jp/taiko-fumen metadata tables')


url = "http://wikiwiki.jp/taiko-fumen/%E5%8F%8E%E9%8C%B2%E6%9B%B2/%E5%88%9D%E5%87%BA%E9%A0%86/%E6%99%82%E7%B3%BB%E5%88%97%E9%A0%86"
df_list = pd.read_html(url)
df_date_1 = df_list[1]
# wks = sh[0]
# wks.set_dataframe(df_date_1, (1, 1))

url = "https://wikiwiki.jp/taiko-fumen/%E5%8F%8E%E9%8C%B2%E6%9B%B2/%E5%88%9D%E5%87%BA%E9%A0%86/%E6%96%B0%E7%AD%90%E4%BD%93%E4%BB%A5%E9%99%8D/%E6%99%82%E7%B3%BB%E5%88%97%E9%A0%86"
df_list = pd.read_html(url)
df_date_2 = df_list[1]
df_date_3 = df_list[2]
# wks = sh[1]
# wks.set_dataframe(df_date_2, (1, 1))

url = "https://wikiwiki.jp/taiko-fumen/%E5%8F%8E%E9%8C%B2%E6%9B%B2/%E5%88%9D%E5%87%BA%E9%A0%86/%E6%96%B0%E7%AD%90%E4%BD%932%E4%BB%A5%E9%99%8D/%E6%99%82%E7%B3%BB%E5%88%97%E9%A0%86"
df_list = pd.read_html(url)
df_date_4 = df_list[1]
# wks = sh[2]
# wks.set_dataframe(df_date_3, (1, 1))

df_date = pd.concat([df_date_1, df_date_2, df_date_3, df_date_4])
df_date_filtered = df_date[df_date.nunique(axis=1).ne(1)]
df_date_dropped = df_date_filtered.drop(df_date_filtered.columns[0:1], axis=1)
df_date_dropped = df_date_dropped.drop(df_date_filtered.columns[2:3], axis=1)
df_date_dropped = df_date_dropped.drop(df_date_filtered.columns[4:], axis=1)

url = "https://wikiwiki.jp/taiko-fumen/%E5%8F%8E%E9%8C%B2%E6%9B%B2/%E6%9B%B2ID%E3%81%BE%E3%81%A8%E3%82%81"
df_list = pd.read_html(url)
df_id_1 = df_list[1]
df_id_2 = df_list[2]
df_id_3 = df_list[3]
df_id = pd.concat([df_id_1, df_id_2, df_id_3])
df_id_filtered = df_id[df_id.nunique(axis=1).ne(1)]
df_id_dropped = df_id_filtered.drop(df_id_filtered.columns[2:5], axis=1)

# wks = sh[3]
# wks.set_dataframe(df_id, (1, 1))

# wks = sh[4]
# wks.set_dataframe(df_date_dropped, (1, 1))

# wks = sh[5]
# wks.set_dataframe(df_id_dropped, (1, 1))

# drop subtitles
df_date_dropped['曲名'] = df_date_dropped['曲名'].apply(split_subtitles)
df_id_dropped['曲名'] = df_id_dropped['曲名'].apply(split_subtitles)
df_date_dropped['曲名c'] = df_date_dropped['曲名'].apply(normalize_titles)
df_id_dropped['曲名c'] = df_id_dropped['曲名'].apply(normalize_titles)

df_merged = pd.merge(df_date_dropped, df_id_dropped, on='曲名c', how='outer')
df_merged['曲名_y'].fillna(df_merged['曲名_x'], inplace=True)
df_merged = df_merged.drop(columns=['曲名_x', '曲名c'])
df_merged = df_merged[df_merged.columns.tolist()[::-1]]
wks = sh[0]
wks.set_dataframe(df_merged, (1, 1))

breakpoint()