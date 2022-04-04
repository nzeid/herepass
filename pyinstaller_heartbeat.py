"""
Copyright (c) 2022 Nader G. Zeid

This file is part of HerePass.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HerePass. If not, see <https://www.gnu.org/licenses/gpl.html>.
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from shutil import rmtree
from threading import Lock, Thread


class Heartbeat:
    def __init__(self):
        working_dir = os.path.realpath(sys._MEIPASS)
        self.pyinstaller_dir = os.path.dirname(working_dir)
        self.heartbeat_file_name = "herepass_heartbeat.txt"
        self.heartbeat_path = os.path.join(working_dir, self.heartbeat_file_name)
        self.heartbeat_file_handle = open(self.heartbeat_path, "xb")
        self.lock = Lock()
        self.keep_beating = True
        self.thread = Thread(target=self.beat)

    def beat(self):
        timestamp_cycle = 0
        cleanup_cycle = 0
        keep_beating = True
        while keep_beating:
            with self.lock:
                keep_beating = self.keep_beating
            # Timestamp:
            if timestamp_cycle % 20:
                timestamp_cycle += 1
            else:
                timestamp_cycle = 1
                self.clock_in()
            # Cleanup:
            if cleanup_cycle % 1200:
                cleanup_cycle += 1
            else:
                cleanup_cycle = 1
                self.clean_up()
            # Pause:
            time.sleep(0.05)

    def clock_in(self):
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        timestamp = timestamp.encode("ascii")
        self.heartbeat_file_handle.seek(0)
        self.heartbeat_file_handle.write(timestamp)
        self.heartbeat_file_handle.truncate()
        self.heartbeat_file_handle.flush()

    def heartbeat_file_is_stale(self, current_file):
        try:
            stat_info = os.stat(current_file)
            current_timestamp = datetime.fromtimestamp(stat_info.st_mtime, timezone.utc)
        except Exception:
            current_timestamp = None
        if current_timestamp:
            diff = datetime.now(timezone.utc) - current_timestamp
            if diff > timedelta(minutes=1):
                return True
        return False

    def clean_up(self):
        for current_dir in os.listdir(self.pyinstaller_dir):
            if current_dir.startswith("_MEI"):
                current_dir = os.path.join(self.pyinstaller_dir, current_dir)
                if os.path.isdir(current_dir):
                    current_file = os.path.join(current_dir, self.heartbeat_file_name)
                    if self.heartbeat_file_is_stale(current_file):
                        try:
                            rmtree(current_dir)
                        except Exception:
                            pass

    def start_beating(self):
        self.thread.start()

    def stop_beating(self):
        with self.lock:
            self.keep_beating = False
        self.thread.join()
        self.heartbeat_file_handle.close()
        self.heartbeat_file_handle = None
        os.remove(self.heartbeat_path)


def start_pyinstaller_heartbeat():
    if hasattr(sys, "_MEIPASS"):
        heartbeat = Heartbeat()
        heartbeat.start_beating()
        return heartbeat
    return None
