import json
import os
import sys
import time
import math
from datetime import datetime
from typing import cast, Any

import serial.serialutil
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt

class TOOL:
    """
    Class for various utility functions.
    """

    def find_json_files(self, folder):
        """
        Recursively finds all JSON files in the specified folder and its subfolders.
        Useful only for testing purposes to easily load configuration files without hardcoding paths.
        """

        json_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.relpath(os.path.join(root, file), "./"))
        return json_files
    
    def export_result_to_csv(self, data_string: str, extra_name: str = None, result_output_path = None):
        """
        Exports the provided data string to a CSV file named with a timestamp
        and optionally an extra string in the filename.

        Filename formats:
        - Without extra_name: "csv-{timestamp}.csv"
        - With extra_name:    "csv-{timestamp}-{extra_name}.csv"

        Parameters
        ----------
        data_string : str
            The data (e.g., comma-separated values) to write to the CSV file.
        extra_name : str, optional
            Additional string appended to the filename, e.g., "_Current".
            If None, no extra string is appended.
        """
        # Generate a time-based string here
        stamp = self.TimeStamp()

        # Construct filename depending on whether extra_name is provided
        if extra_name:
            filename = f"csv-{stamp}-{extra_name}.csv"
        else:
            filename = f"csv-{stamp}.csv"

        # Write the data to the file
        with open(os.path.join(result_output_path,filename), 'w') as f:
            f.write(data_string)

        print(f"CSV exported to {filename}")

    def TimeStamp(self):
        # Generate a time-based string here
        now = datetime.now()

        # Create a timestamp like "HH_MM_SS-DD_MM_YYYY"
        day = now.strftime("%d_%m_%Y")
        current_time = now.strftime("%H_%M_%S")
        Timestamp = f"{current_time}-{day}"
        return Timestamp
    

    def plot_values(self, data_string: str):
        """
        Plots a comma-separated string of numeric data.
        """
        data_formatted = [float(i) for i in data_string.split(",")]
        plt.plot(data_formatted)
        plt.ylabel('current')
        plt.show()



# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    tool = TOOL()
    tool.find_pyvisa_devices()
    
