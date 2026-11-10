import sys
from pathlib import Path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / 'backend'))
from sqlalchemy import text
from config.settings import load_settings
from database.engine import dispose_engine, init_engine, session_scope

def main() -> int:
    settings = load_settings()
    init_engine(settings, echo=False)
    try:
        with session_scope() as session:
            one = session.execute(text('SELECT 1')).scalar()
            version = session.execute(text('SELECT version()')).scalar()
            user = session.execute(text('SELECT current_user')).scalar()
            db = session.execute(text('SELECT current_database()')).scalar()
    finally:
        dispose_engine()
    print(f'OK: SELECT 1 -> {one}')
    print(f"Server: {version.split(',')[0]}")
    print(f'User: {user}')
    print(f'Database: {db}')
    if one != 1:
        print('FAIL: SELECT 1 did not return 1')
        return 1
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
