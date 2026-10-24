import sys
from pathlib import Path

_server_dir = Path(__file__).resolve().parent
_project_dir = _server_dir.parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)