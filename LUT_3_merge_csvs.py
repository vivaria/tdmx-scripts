import csv
import os

import numpy as np


luts = {}
for root, dirs, files in os.walk("soulgauge_LUTs", topdown=True):
    for file in files:
        # Fetch data from csv file
        arr = np.loadtxt(os.path.join(root, file), delimiter=",", dtype=int)
        file = file.replace("byte1213", "good")
        file = file.replace("byte1617", "ok")
        file = file.replace("byte2021", "bad")
        if "bad" in file:
            arr -= 765
        luts[file] = arr[:, 1]

headers = list(luts.keys())
data = np.vstack(list(luts.values())).T
list_data = list(list(d) for d in data)

with open(f'merged.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(headers)
    for list_d in list_data:
        csv_writer.writerow(list_d)
test = None

