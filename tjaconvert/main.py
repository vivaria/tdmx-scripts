import shutil
import subprocess
import os
import json


def fix_song_path(root_dir):
    # Fetch name of TJA and song file
    fname_tja, fname_song, ext_song = None, None, None
    for filename in os.listdir(root_dir):
        if filename.endswith(".tja"):
            fname_tja = filename
        elif filename.endswith(".wav"):
            fname_song = filename
            ext_song = ".wav"
        elif filename.endswith(".ogg"):
            fname_song = filename
            ext_song = ".ogg"
    assert fname_tja is not None
    assert fname_song is not None
    # Change WAVE: field to refer to 'song.ogg'
    path_tja = os.path.join(root_dir, fname_tja)
    tja = []
    encoding = "shift-jis"
    try:
        with open(path_tja, "r", encoding=encoding) as fp:
            lines = fp.readlines()
    except UnicodeDecodeError:
        encoding = "utf-8"
        with open(path_tja, "r", encoding=encoding) as fp:
            lines = fp.readlines()
    for line in lines:
        if line.startswith("WAVE:"):
            tja.append(f"WAVE:song{ext_song}\n")
        elif line.startswith("SCOREDIFF:0"):
            tja.append("SCOREDIFF:1\n")
        else:
            tja.append(line)
    with open(path_tja, "w", encoding=encoding) as fp:
        fp.writelines(tja)
    # Rename song file to 'song.ogg'
    shutil.move(os.path.join(root_dir, fname_song),
                os.path.join(root_dir, f"song{ext_song}"))
    test = None


def convert_tja(root_dir):
    print(f"\n- Converting {root_dir}...")
    fix_song_path(root_dir)
    raw_output = subprocess.Popen(["TJAConvert.exe", root_dir],
                                  stdout=subprocess.PIPE).communicate()[0]
    raw_output = raw_output.split(b"\r\n")
    decoded_output = []
    for output in raw_output:
        encoding = "utf-16" if b"\x00" in output else "utf-8"
        decoded_substring = output.decode(encoding=encoding)
        decoded_output.append(decoded_substring)
    decoded_output = "\n".join(decoded_output)
    gen_dir = [f for f in os.listdir(root_dir) if "[GENERATED]" in f]
    if gen_dir:
        gen_dir = gen_dir[0]
        generate_conversion_json(root_dir, gen_dir)
        gen_dir = os.path.join(root_dir, gen_dir)
    else:
        gen_dir = None
    parts = decoded_output.strip("\r\n").split("\n")
    err_str, *rest = parts[-1].split(":")
    msg = ":".join(rest).strip("\r\n")
    if len(parts) > 1:
        msg = "\n".join(parts[:-1] + [msg])
    return int(err_str), msg, gen_dir


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
