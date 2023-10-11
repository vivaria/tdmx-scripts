import os
import json

CUSTOMSONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs")

# Step 1. Read in the existing song data
song_order = []
for root, dirs, files in os.walk(CUSTOMSONG_DIR, topdown=True):
    if "data.json" in files:
        json_path = os.path.join(root, "data.json")
        json_dict = json.load(open(json_path, encoding="utf8"))
        try:
            song_name = json_dict["songName"]["enText"]
        except KeyError:
            song_name = json_dict["songName"]["text"]
        song_order.append([song_name, json_path])

# Step 2. Sort the songs so that they're alphabetical
song_order_sorted = sorted(song_order, key=lambda s: s[0].lower())

# Step 3. Modify each of the 1800+ songs so that the `order` field represents
# alphabetical order
for i, (song_name, json_path) in enumerate(song_order_sorted):
    # Read the metadata file
    with open(json_path, "r", encoding="utf8") as infile:
        json_dict = json.load(infile)
    # Change the order to match the alphabetical order
    json_dict['order'] = i
    # Write the modified data ack to the file
    with open(json_path, "w", encoding="utf8") as outfile:
        # Get the JSON data to be written, as a string
        str_to_write = json.dumps(json_dict, indent="\t", ensure_ascii=False)
        # Account for the fact that some keys are "key:value" while others are
        # "key: value"
        str_to_write = str_to_write.replace(': ', ':')
        for key in ["songName", "songSubtitle", "songDetail",
                    "text", "font", "jpText", "jpFont",
                    "enText", "enFont", "krText", "krFont"]:
            str_to_write = str_to_write.replace(f'"{key}":', f'"{key}": ')
        # Account for the nonstandard tab indentation used by the existing
        # files
        str_to_write = str_to_write.replace("\t", "\t\t")
        str_to_write = str_to_write.replace("\t\t\t\t", "\t\t\t")
        str_to_write = "\t" + str_to_write[:-1] + "\t}"
        # Write the modified JSON string to the file
        outfile.write(str_to_write)
