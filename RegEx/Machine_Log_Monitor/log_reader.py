from config import MACHINE_LOG_FILE
class MachineLogReader:
    def __init__(self, file_path=MACHINE_LOG_FILE):
        self.file_path = file_path
        self.file = None
        self.line_number = 0

    def open(self):
        if self.file is None:
            self.file = open(self.file_path, "r", encoding="utf-8")

    def read_next_line(self):
        self.open()
        line = self.file.readline()
        if not line:
            return None

        self.line_number += 1
        line = line.rstrip("\n")
        next_line_position = self.file.tell()
        has_next_line = bool(self.file.readline())
        self.file.seek(next_line_position)

        is_last_line = not has_next_line
        return (self.line_number, line, is_last_line)

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
