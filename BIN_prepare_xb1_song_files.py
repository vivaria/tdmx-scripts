"""
Python script to decrypt/un-gzip the `.bin` song files included in XB1/TDMX.

Tested to work with files from v1.2.2 (check pins in #xb1_modding). May not
work with newer versions with updated keys.

Prerequisites:
    1. Install Python.
    2. Install a version of OpenSSL, making sure that `openssl` is on the PATH.
       (In other words, make sure you can run `openssl` from the command line.)

Instructions:
    1. Create a new empty folder.
    2. Copy the encrypted `.bin` song files to the new folder:
        - Location: 'TaikoTDM\Taiko no Tatsujin_Data\StreamingAssets\sound'
        - You only need to copy the files that start with 'song_'
    3. Copy all the fumen subfolders to the new folder, too:
        - Location: 'TaikoTDM\Taiko no Tatsujin_Data\StreamingAssets\fumen'
        - You don't need to organize the folders. This script will move each
          'song_' file into each of the fumen subfolders once decrypted.
    4. Put this script in the same folder as the song files/fumen folders.
    5. Make sure the folder looks like this:

        folder/
        │ # Sample folder
        ├─ 87oto/
        │  ├─ 87oto_e.bin
        │  ├─ 87oto_e_1.bin
        │  ├─ 87oto_e_2.bin
        │  ├─ [...]
        │  └─ 87oto_m.bin
        │
        │ # Rest of folders
        ├─ ac7roc/
        ├─ blurb/
        ├─ [...]
        ├─ yukai/
        │
        │ # Song files
        ├─ song_87oto.bin
        ├─ song_ac7roc.bin
        ├─ song_blurb.bin
        ├─ [...]
        ├─ song_yukai.bin
        │
        │ # This script
        └─ decrypt_xb1_bins.py

    6. Run the script
"""

import gzip
import os
import shutil
import subprocess

# Valid for TDMX v1.2.2
KEYS = {
    "song": "794A7A4E5651764C42484C625857364269476B337450414C46536665466D5746",
    "fumen": "51795670785570353734733644547466445348384A4564367834645769357138"
}
EXPECTED_HEADER_BYTES = {
    "song": b"@UTF",
    "fumen": b".bin"
}


def decrypt_file(root, fname, filetype):
    ext = '.'.join(fname.split('.')[1:])
    fpath = os.path.join(root, fname)
    tmp_fpath = os.path.join(root, f"temp.{ext}")
    with open(fpath, "rb") as file:
        iv_bytes = file.read(16).hex().upper()
    command = (f"openssl aes-256-cbc -d -in {fpath} -out {tmp_fpath} "
               f"-K {KEYS[filetype]} -iv {iv_bytes}")
    try:
        subprocess.check_output(command, shell=True)
        with open(tmp_fpath, "rb") as file:
            bytestring = file.read()
        bytestring = bytestring[16:]  # discard iv bytes
        # decrypted songs should start with @UTF marker
        if filetype == "song":
            decrypted = bytestring.startswith(b"@UTF")
        # decrypted fumens should contain the filename starting at byte 10
        else:
            assert filetype == "fumen"
            decrypted = bytestring[10:].startswith(fname.encode())
        if decrypted:
            print(f"  - Successfully decrypted {fname}")
            with open(tmp_fpath, "wb") as file:
                file.write(bytestring)
            os.remove(fpath)
            shutil.move(tmp_fpath, fpath)
            return True
        else:
            print(f"  - Couldn't find expected bytes in decrypted file")
            os.remove(tmp_fpath)
            return False
    except subprocess.CalledProcessError as e:
        print(f"  - {fname} either already decrypted or invalid: {e}")
        return False


def gunzip_file(root, fname):
    fpath = os.path.join(root, fname)
    tmp_fpath = os.path.join(root, "temp.bin")
    try:
        with gzip.open(fpath, 'rb') as f_in:
            with open(tmp_fpath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"  - Succesffuly gunzipped {fname}")
        os.remove(fpath)
        shutil.move(tmp_fpath, fpath)
        return True
    except Exception as e:
        print(f"  - {fname} couldn't be gunzipped: {e}")
        return False


def main():
    SONG_DIR = os.path.join("C:\\", "Users", "joshu", "Desktop", "XB1")
    print(f"Looking for files in {SONG_DIR}... (Expected # of XB1 songs: 77)")
    contents = os.listdir(SONG_DIR)
    folders = [f for f in contents if os.path.isdir(os.path.join(SONG_DIR, f))]
    bins = [b for b in contents if b.endswith(".bin") and b.startswith("song")]
    print(f"Found {len(folders)} fumen folders: {folders}")
    print(f"Found {len(bins)} song bins: {bins}")

    print("\nDecrypting song bins...")
    for song_bin in bins:
        print(f"  - Decrypting {song_bin}...")
        decrypt_file(root=SONG_DIR, fname=song_bin, filetype="song")

    print("\nDecrypting + ungzipping fumen files...")
    for folder_name in folders:
        print(f"  - Decrypting + un-gzipping fumens in {folder_name}...")
        folder_path = os.path.join(SONG_DIR, folder_name)
        for fumen in [f for f in os.listdir(folder_path)
                      if f.endswith(".bin") and not f.startswith("song")]:
            if decrypt_file(root=folder_path, fname=fumen, filetype="fumen"):
                gunzip_file(root=folder_path, fname=fumen)

    print("\nCopying song files to fumen folders...")
    for folder_name in folders:  # Only copy files if its fumen folder exists
        song_name = f"song_{folder_name}.bin"
        src = os.path.join(SONG_DIR, song_name)
        folder_path = os.path.join(SONG_DIR, folder_name)
        dest = os.path.join(folder_path, song_name)
        if not os.path.exists(src):
            print(f"Fumen folder {folder_name} missing song file")
        else:
            shutil.copy(src, dest)


if __name__ == "__main__":
    main()
