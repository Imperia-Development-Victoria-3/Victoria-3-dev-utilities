import time
import os
import re
from collections import defaultdict

class LogMonitor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.last_checked = None
        self.error_counts = defaultdict(int)
        self.current_error = ""
        self.timestamps = set()

    def update_last_checked(self):
        self.last_checked = os.path.getmtime(self.filepath)

    def file_modified(self):
        return os.path.getmtime(self.filepath) > (self.last_checked or 0)

    def read_errors(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8-sig') as file:
                tmp_timestamps = set()

                for line in file:
                    timestamp = self.get_timestamp(line)
                    if timestamp:
                        if timestamp.group(0) not in self.timestamps:
                            tmp_timestamps.add(timestamp.group(0))
                            if self.current_error:
                                self.error_counts[self.current_error.strip()] += 1
                        self.current_error = self.remove_timestamp(line)
                    else:
                        self.current_error += " " + line.strip()

                # Count the last error in the file
                if self.current_error:
                    self.error_counts[self.current_error.strip()] += 1

                self.timestamps |= tmp_timestamps
        except UnicodeDecodeError as e:
            print(f"Error decoding line: {e}")


    @staticmethod
    def get_timestamp(line):
        # Check if the line starts with a timestamp
        return re.match(r'^\[\d{2}:\d{2}:\d{2}\]', line)

    @staticmethod
    def remove_timestamp(line):
        # Remove the timestamp from the line
        return re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\[.*?\]: ', '', line)

    def display_error_counts(self):
        # Sort the errors by count in descending order
        sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)
        with open('error_counts.txt', 'w') as file:
            for error, count in sorted_errors:
                output = f'{error}: {count}\n'
                # print(output)
                file.write(output)

    def monitor(self):
        while True:
            if self.file_modified():
                self.read_errors()
                self.update_last_checked()
                self.display_error_counts()
            time.sleep(0.2)  # Check every second

if __name__ == "__main__":
    log_monitor = LogMonitor('C:\\Users\\hidde\\Documents\\Paradox Interactive\\Victoria 3\\logs\\error.log')
    log_monitor.monitor()
