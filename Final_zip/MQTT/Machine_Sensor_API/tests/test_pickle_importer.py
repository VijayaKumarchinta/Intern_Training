"""Importer hash-skip and row-validation logic — the duplicate-data defense.

The SHA-256 ledger check is what makes re-imports safe; these tests prove the
guard fires before any database work, and that malformed rows are skipped and
counted rather than aborting the file.
"""
import hashlib
import pickle
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.pickle_importer import PickleImporter


@pytest.fixture()
def snapshot(tmp_path):
    """One tiny pickle file in the shape the importer expects."""
    data = {
        "Machine A": [
            {"ST": "TEMP", "TS": 1743157500, "VR": [72.1]},
            {"ST": "PRESS", "TS": 1743157501, "VR": [101.3]},
        ],
        "Machine B": [
            {"ST": "TEMP", "TS": 1743157502, "VR": [55.0]},
        ],
    }
    path = tmp_path / "snapshot.pkl"
    path.write_bytes(pickle.dumps(data))
    return path


def _stub_ledger(monkeypatch, already=False):
    importer = PickleImporter(batch_size=2)
    monkeypatch.setattr(importer, "_is_already_imported", lambda h: already)
    monkeypatch.setattr(importer, "_import_csv", lambda *a, **k: {
        "records_inserted": 3,
        "records_skipped": 0,
    })
    return importer


def test_reimport_of_same_content_is_refused_before_any_work(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.pkl"
    path.write_bytes(pickle.dumps({"M": [{"ST": "T", "TS": 1, "VR": [1.0]}]}))
    importer = _stub_ledger(monkeypatch, already=True)

    calls = []
    monkeypatch.setattr(
        importer, "_convert_to_csv", lambda p: calls.append(p) or "csv"
    )

    with pytest.raises(ValueError, match="already imported"):
        importer.import_file(path)

    assert calls == [], "hash-skip must fire before CSV conversion"


def test_hash_is_content_not_name(tmp_path):
    a = tmp_path / "one.pkl"
    b = tmp_path / "two.pkl"
    payload = pickle.dumps({"M": [{"ST": "T", "TS": 1, "VR": [1.0]}]})
    a.write_bytes(payload)
    b.write_bytes(payload)

    importer = PickleImporter()
    assert importer._get_file_hash(a) == importer._get_file_hash(b)
    assert importer._get_file_hash(a) == hashlib.sha256(payload).hexdigest()


def test_different_content_different_hash(tmp_path):
    a = tmp_path / "a.pkl"
    b = tmp_path / "b.pkl"
    a.write_bytes(pickle.dumps({"M": [{"ST": "T", "TS": 1, "VR": [1.0]}]}))
    b.write_bytes(pickle.dumps({"M": [{"ST": "T", "TS": 2, "VR": [2.0]}]}))

    importer = PickleImporter()
    assert importer._get_file_hash(a) != importer._get_file_hash(b)


def test_missing_file_raises_value_error(tmp_path):
    importer = PickleImporter()
    with pytest.raises(ValueError, match="does not exist"):
        importer.import_file(tmp_path / "nope.pkl")


def test_non_dict_pickle_is_rejected(tmp_path):
    path = tmp_path / "list.pkl"
    path.write_bytes(pickle.dumps([1, 2, 3]))
    importer = PickleImporter()
    with pytest.raises(ValueError, match="must contain a dictionary"):
        importer._convert_to_csv(path)


def test_convert_to_csv_skips_malformed_rows(tmp_path):
    data = {
        "Machine A": [
            {"ST": "TEMP", "TS": 1743157500, "VR": [72.1]},
            {"ST": "", "TS": 1743157500, "VR": [1.0]},
            {"ST": "TEMP", "TS": None, "VR": [1.0]},
            {"ST": "TEMP", "TS": 1743157500, "VR": []},
            {"ST": "TEMP", "TS": "not-a-number", "VR": [1.0]},
            "not even a dict",
        ],
    }
    path = tmp_path / "messy.pkl"
    path.write_bytes(pickle.dumps(data))

    importer = PickleImporter()
    csv_path = importer._convert_to_csv(path)

    import csv as csv_module
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv_module.DictReader(fh))

    assert len(rows) == 1, "only the one well-formed row survives"
    assert rows[0]["machine_name"] == "Machine A"
    assert rows[0]["sensor_tag"] == "TEMP"
