import os
import json
from subprocess import run

from tja2fumen.main import main
from tja2fumen.writers import writeFumen
from tja2fumen.constants import COURSE_IDS

CUSTOMSONG_DIR = os.path.join("D:\\", "games", "TaikoTDM",
                              "CustomSongs", "tja")


# Fetch metadata generated by
song_ids = {}
song_paths = {}
song_gzipped = {}
for root, dirs, files in os.walk(CUSTOMSONG_DIR, topdown=True):
    for file in files:
        if "data.json" in files:
            json_path = os.path.join(root, "data.json")
            json_dict = json.load(open(json_path, encoding="utf8"))
            song_name = root.split("\\")[-2]
            id = json_dict["id"]
            gzipped = json_dict["areFilesGZipped"]
            song_ids[song_name] = id
            song_paths[song_name] = root.split("\\")[-1]
            song_gzipped[song_name] = gzipped

for root, dirs, files in os.walk(CUSTOMSONG_DIR, topdown=True):
    for file in files:
        if any(substring in root for substring in ['Taiko Towers', 'Dan Dojo']):
            continue
        if file.endswith(".tja"):
            try:
                _, convertedTJAs = main(fnameTJA=os.path.join(root, file))
                for course, song in convertedTJAs.items():
                    songName = root.split("\\")[-1]
                    outputName = song_ids[songName] + f"_{COURSE_IDS[course]}.bin"
                    outputPath = os.path.join(root, song_paths[songName])
                    os.makedirs(outputPath, exist_ok=True)
                    os.chmod(outputPath, 0o777)
                    outputFilepath = os.path.join(outputPath, outputName)
                    outputFile = open(outputFilepath, "wb")
                    writeFumen(outputFile, song)
                    if song_gzipped[songName]:
                        run(["gzip", outputFilepath])
                        os.rename(outputFilepath + ".gz", os.path.join(outputPath, outputName))
                print(f"Success: {file}")
            except NotImplementedError:
                print(f"Failure: {file} due to NotImplementedError.")
            except KeyError:
                print(f"Failure: {file} due to tja2bin.exe failure.")
            except Exception as e:
                raise e
