import glob
import re
import os
import sys
import subprocess

msg = """
To use this script, make sure that you:

  - Download and install Python.
  - Save this file in the main folder with all of the fumen folders.
  - Put tja2fumen.exe in the main folder with all of the fumen folders.
"""
print(msg)
CUSTOM_SONG_DIR = os.getcwd()
print(f"Looking for tja2fumen.exe in {CUSTOM_SONG_DIR}")
tja2fumen_exes = glob.glob(os.path.join(CUSTOM_SONG_DIR, "tja2fumen*.exe"))
if not tja2fumen_exes:
    print("Could not find tja2fumen.exe in files.")
    input("Press Enter to continue...")
    sys.exit(1)
tja2fumen = tja2fumen_exes[0]
print(f"Using {tja2fumen}...")
print(f"\nLooking for .bin files in {CUSTOM_SONG_DIR}")
processed_files = []
for root, dirs, files in os.walk(CUSTOM_SONG_DIR, topdown=True):
    for file_name in files:
        match = re.match(r"^(.+)_([ehmnx])(_\d)?\.bin$", file_name)
        if match:
            filepath = os.path.join(root, file_name)
            if filepath not in processed_files:
                command = f'{tja2fumen} "{filepath}"'
                print(f'Running {command}')
                print(subprocess.check_output(command, shell=True).decode('utf-8'))
                processed_files.append(filepath)
input("Press Enter to continue...")