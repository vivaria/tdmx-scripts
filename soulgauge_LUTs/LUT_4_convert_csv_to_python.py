import os
import csv

soul_gauge_dicts = {"good": {}, "ok": {}, "bad": {}}

with open(os.path.join("merged.csv"), newline="", encoding="utf-8") as csv_file:
    for num, line in enumerate(csv.DictReader(csv_file)):
        for key, value in line.items():
            judgment, difficulty = key.split("_")
            difficulty = difficulty.split(".")[0]
            if difficulty not in soul_gauge_dicts[judgment]:
                soul_gauge_dicts[judgment][difficulty] = []
            soul_gauge_dicts[judgment][difficulty].append(value)
