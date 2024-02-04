import gzip
import os
from pathlib import Path
import shutil
import subprocess

KEYS = {
    "song": "794A7A4E5651764C42484C625857364269476B337450414C46536665466D5746",
    "fumen": "51795670785570353734733644547466445348384A4564367834645769357138"
}
FUMEN_HEADER_BYTES = b'\x81-*+'


def decrypt_file(root, fname, filetype):
    fpath = os.path.join(root, fname)
    tmp_fpath = os.path.join(root, "temp")
    with open(fpath, "rb") as file:
        first_16_bytes = file.read(16).hex().upper()

    command = (f"openssl aes-256-cbc -d -in {fpath} -out {tmp_fpath} "
               f"-K {KEYS[filetype]} -iv {first_16_bytes}")
    try:
        subprocess.check_output(command, shell=True)
        with open(tmp_fpath, "rb") as file:
            bytestring = file.read()
            decrypted = any(b in bytestring for b in [b"UTF", b'.bin'])
        if decrypted:
            print(f"Successfully decrypted {fname}")
            with open(tmp_fpath, "rb") as file:
                bytestring = file.read()
            if b"@UTF" in bytestring and not bytestring.startswith(b"@UTF"):
                with open(fpath, "wb") as file:
                    file.write(bytestring[16:])
            shutil.move(fpath, fpath + ".bak")
            shutil.move(tmp_fpath, fpath)
        else:
            os.remove(tmp_fpath)
    except subprocess.CalledProcessError:
        print(f"{fname} either already decrypted or invalid")


def gunzip_file(root, fname):
    fpath = os.path.join(root, fname)
    tmp_fpath = os.path.join(root, "temp.bin")
    try:
        with open(fpath, 'rb') as f_in:
            bytestring = f_in.read()
        decompressed_bytestring = gzip.decompress(bytestring[16:])
        with open(tmp_fpath, 'wb') as f_out:
            f_out.write(decompressed_bytestring)
        shutil.move(fpath, fpath + ".bak")
        shutil.move(tmp_fpath, fpath)
    except Exception as e:
        print(e)
        return
    print(f"Succesffuly gunzipped {fname}")


CUSTOM_SONG_DIR = os.path.join("C:\\", "TaikoTDM", "customSongs", "bin")
for root, dirs, files in os.walk(CUSTOM_SONG_DIR, topdown=True):
    song_id = Path(root).name
    if "xb1" not in song_id:
        continue
    for fname in files:
        if not fname.endswith(".bin") or "xb1" not in fname:
            continue
        print(f"\nAttempting to decrypt {fname}")
        if "song" in fname:
            decrypt_file(root, fname, filetype="song")
        else:
            decrypt_file(root, fname, filetype="fumen")
            print(f"Attempting to gunzip {fname}")
            gunzip_file(root, fname)
