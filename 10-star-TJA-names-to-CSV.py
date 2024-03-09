import os
import csv

CUSTOMSONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                              "CustomSongSources", "ESE")

names = []
for root, dirs, files in os.walk(CUSTOMSONG_DIR, topdown=True):
    for file in files:
        if any(substring in root for substring in ['Taiko Towers',
                                                   'Dan Dojo']):
            continue
        if file.endswith(".tja"):
            with open(os.path.join(root, file), encoding="utf8") as tja:
                try:
                    lines = tja.readlines()
                except Exception:
                    print(f"`tja.readlines()` failed for {file}.")
                    continue
                title, titleja = '', ''
                for line in lines:
                    if line.startswith("TITLE:"):
                        title = line.split(':')[1].rstrip()
                    elif line.startswith("TITLEJA:"):
                        titleja = line.split(':')[1].rstrip()
                    if title and titleja:
                        break
                for line in lines:
                    if line.startswith("LEVEL:"):
                        stars = int(line.split(':')[1].rstrip())
                        if stars == 10:
                            print(f"Title: {title}")
                            names.append([title])
                            break

names = sorted(names)

with open("output.csv", "w", encoding="utf8", newline="\n") as f:
    writer = csv.writer(f)
    writer.writerows(names)
