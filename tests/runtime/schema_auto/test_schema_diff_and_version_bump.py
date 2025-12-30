from __future__ import annotations

from runtime.schema.schema_diff import diff_normalized, classify_version_bump


def test_diff_detects_field_move_and_bumps_minor():
    before = {
        "sheets": {
            "Position": {
                "sheet_name": "Position",
                "row_start": 2,
                "mapping": {"symbol": "A", "qty": "B"},
                "layout": None,
            }
        }
    }

    after = {
        "sheets": {
            "Position": {
                "sheet_name": "Position",
                "row_start": 2,
                "mapping": {"symbol": "A", "qty": "C"},
                "layout": None,
            }
        }
    }

    report = diff_normalized(before, after)
    bump = classify_version_bump(report)

    assert report.changed is True
    assert any(i.kind == "FIELD_MOVED" and i.key == "qty" for i in report.items)
    assert bump.bump == "minor"


def test_diff_detects_field_removal_and_bumps_major():
    before = {
        "sheets": {
            "Position": {
                "sheet_name": "Position",
                "row_start": 2,
                "mapping": {"symbol": "A", "qty": "B"},
                "layout": None,
            }
        }
    }

    after = {
        "sheets": {
            "Position": {
                "sheet_name": "Position",
                "row_start": 2,
                "mapping": {"symbol": "A"},
                "layout": None,
            }
        }
    }

    report = diff_normalized(before, after)
    bump = classify_version_bump(report)

    assert report.changed is True
    assert any(i.kind == "FIELD_REMOVED" and i.key == "qty" for i in report.items)
    assert bump.bump == "major"
