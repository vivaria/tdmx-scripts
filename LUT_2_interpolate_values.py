import os

import numpy as np
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt


for root, dirs, files in os.walk("raw-csv-files-byte1213", topdown=True):
    for file in files:
        # Fetch data from csv file
        arr = np.loadtxt(os.path.join(root, file), delimiter=",", dtype=int)
        # Remove outliers from array by ensuring soul gauge byte value is always monotonically increasing
        vals = []
        # for i, val in enumerate(arr):
        #     if i+1 in [1, len(arr)]:
        #         vals.append(val)
        #         continue
        #     val1 = vals[-1][1]
        #     val2 = val[1]
        #     val3 = arr[i+1][1]
        #     if val2 < val1:
        #         pass
        #     elif val2 >= val3:
        #         pass
        #     else:
        #         vals.append(val)
        # arr = vals
        # Remove duplicate values
        arr = np.array(list({val[0]: val[1] for val in arr}.items()))
        # Add points at (0, 0) and (2000, 765) to make upper/lower bound behave nicer
        arr = np.vstack([[0, 1020], arr, [2500, 0]])
        # Plot sequence of values
        x = arr[:, 0]
        y = arr[:, 1]
        xx = np.linspace(1, 2500, 2500).astype(int)
        yy = PchipInterpolator(x, y)(xx).round().astype(int)
        plt.plot(xx, yy, '-', label=file)
        plt.plot(x, y, 'o')

        arr_lut = np.vstack([xx, yy]).T
        np.savetxt(os.path.join("LUTs", file), arr_lut, fmt='%i', delimiter=",")

    plt.legend()
    plt.show()
    test = None
