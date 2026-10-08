from config import MACHINE_LOG_FILE


class MachineLogReader:
    def __init__(self, file_path=MACHINE_LOG_FILE):
        self.file_path = file_path
        self.file = None
        self.line_number = 0
        self.last_line_position = None

    def open(self):
        if self.file is None:
            self.file = open(self.file_path, "r", encoding="utf-8")

    def read_next_line(self):
        self.open()
        line_position = self.file.tell()
        line = self.file.readline()
        if not line:
            return None

        self.line_number += 1
        self.last_line_position = line_position
        line = line.rstrip("\r\n")

        next_line_position = self.file.tell()
        has_next_line = bool(self.file.readline())
        self.file.seek(next_line_position)
        return self.line_number, line, not has_next_line

    def retry_last_line(self):
        if self.file is not None and self.last_line_position is not None:
            self.file.seek(self.last_line_position)
            self.line_number -= 1
            self.last_line_position = None

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        self.last_line_position = None
