# Code Explanation — `log_rotation/rotation.py` (line by line)

What the file does in one sentence: format every log record as **one-line JSON**,
write it to a **rotating file chain** (`app.log` → `app.log.1` → … → `app.log.10`)
**and** to the **console**, using unix-epoch timestamps.

The file has five parts, explained line by line below:

1. [Imports](#1-imports)
2. [Path constants](#2-path-constants)
3. [`JsonFormatter`](#3-jsonformatter)
4. [`configure_logging`](#4-configure_logging)
5. [Module-level script](#5-module-level-script)

---

## 1. Imports

```python
import json - for the output format
```

```python
import logging - helps us to import the standard logging frameworks
```

```python
import pathlib - helps to build the root directories in particular ones
```

```python
import sys - this help us to import the standard streams 
stdin - reading input
stdout - writing normal output
stderr - writing error messages
```

```python
from logging.handlers import RotatingFileHandler - this helps to import the standard size-based rotation triggers
```

---

## 2. Path constants

```python
BASE_DIR = pathlib.Path(__file__).resolve().parent - saying that the current file is the root directory

LOG_DIR = BASE_DIR / "logs" - for logs name the folder as logs

LOG_DIR.mkdir(exist_ok=True) - if it not exists create the directory

LOG_FILE = LOG_DIR / "app.log" - this a live file of the logs which are going to be created
```

```python
class JsonFormatter(logging.Formatter): - a class that handles the output in json format

def format(self, record):- record everything about one logging event
log_data = {
    "timestamp": record.created, - storing the timestamp as unixtimestamp
    
    "level": record.levelname, - tells us the level of the log msg(info,warning,error)

    "logger": record.name, - name of the logger

    "message": record.getMessage(), - the raw text file
        }
```

```python
        if record.exc_info: - a field where it check the exception errors
            log_data["exception"] = self.formatException(
                record.exc_info
            )
        return json.dumps(log_data) - this helps to convert the dictory format to json format
```

## 4. `configure_logging`

```python
def configure_logging(): -One function that builds and returns the fully wired logger

logger = logging.getLogger("application") - returns the logger name

logger.setLevel(logging.INFO) - ignore the debug and starts from the info mode

if logger.handlers: - prevents the handler to save them twice
    return logger

formatter = JsonFormatter() - a json formatter instance

file_handler = RotatingFileHandler(
        filename=LOG_FILE, - file name like where it should be stored
        maxBytes=2 * 1024, - the max size of the each file and do rotation when it exceeds
        backupCount=10, - that many recorded files are kept
        encoding="utf-8", - we are relaying on byte size
    )

file_handler.setFormatter(formatter) - we are telling t follow the jsong format for the file handler

console_handler = logging.StreamHandler(sys.stdout) - dealing within the terminal using standard outputs

console_handler.setFormatter(formatter) - telling that same json format should follow

logger.addHandler(file_handler) - helps to lands into the file after properly handling it
logger.addHandler(console_handler) - helps to land in the terminal

logger.propagate = False - avoid reaching the root handler so it prevents the msg from printing twice

return logger - starts the logging
```

## 5. Module-level script

```python
logger = configure_logging() - entry point of the code 

logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")

"these three lines are more printing statements for testing"

for i in range(100):
    logger.info(
        "Testing centralized logging - message number %s",i,
    )
The volume generator: 100 more records. Two deliberate details

```