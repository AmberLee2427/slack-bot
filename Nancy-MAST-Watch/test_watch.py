from astropy.table import Table

import watch


class FakeClient:
    def __init__(self, rows):
        self.table = Table(rows=rows)
        self.calls = []

    def query_criteria(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("offset", 0) > 0:
            return Table()
        return self.table

    def get_unique_product_list(self, observations):
        rows = []
        for row in observations:
            dataset = str(row["fileSetName"])
            rows.extend([
                {
                    "dataset": dataset,
                    "filename": dataset + "_cal.asdf",
                    "dataURI": "mast:Roman/" + dataset + "_cal.asdf",
                    "filters": row["optical_element"] if "optical_element" in observations.colnames else None,
                },
                {
                    "dataset": dataset,
                    "filename": dataset + "_uncal.asdf",
                    "dataURI": "mast:Roman/" + dataset + "_uncal.asdf",
                    "filters": row["optical_element"] if "optical_element" in observations.colnames else None,
                },
            ])
        return Table(rows=rows)

    def filter_products(self, products, file_suffix):
        assert file_suffix == "_cal"
        return Table(rows=[
            row for row in products
            if str(row["filename"]).endswith("_cal.asdf")
            and not str(row["filename"]).endswith("_uncal.asdf")
        ])


def test_discovers_ice_program(monkeypatch):
    monkeypatch.delenv("ICE_MAST_PROGRAM", raising=False)
    client = FakeClient(
        [
            {
                "program": 1201,
                "program_category": "COM",
                "program_title": "Ice Characterization",
                "fileSetName": "r0120101001001001001_0001_wfi01_f062",
                "target_ra": 294.34,
                "target_dec": 46.378,
            },
            {
                "program": 1139,
                "program_category": "COM",
                "program_title": "Touchstone field alignment",
                "fileSetName": "r0113901001001001001_0001_wfi01_f062",
                "target_ra": 294.34,
                "target_dec": 46.378,
            },
        ]
    )
    program, rows = watch.discover(client)
    assert program == 1201
    assert len(rows) == 1
    assert client.calls[0]["program_category"] == "COM"
    assert "coordinates" not in client.calls[0]


def test_poll_writes_state_and_single_event(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "ROOT", tmp_path)
    monkeypatch.setattr(watch, "DEFAULT_ENV", tmp_path / ".env")
    monkeypatch.setenv("ICE_MAST_PROGRAM", "1201")
    monkeypatch.setenv("ICE_MAST_STATE", "state/mast-watch.json")
    monkeypatch.setenv("ICE_MAST_EVENT_DIR", "events")
    rows = [
        {
            "program": 1201,
            "program_category": "COM",
            "program_title": "Ice Characterization",
            "fileSetName": "r0120101001001001001_0001_wfi01_f062",
            "optical_element": "F062",
        }
    ]

    first = watch.execute("poll", client=FakeClient(rows))
    second = watch.execute("poll", client=FakeClient(rows))

    assert first["status"] == "new_data"
    assert first["new_count"] == 1
    assert second["status"] == "clear"
    assert second["new_count"] == 0
    assert len(list((tmp_path / "events").glob("*.json"))) == 1
    assert first["new_datasets"][0]["filename"].endswith("_cal.asdf")


def test_version_one_state_migrates_without_alerting(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "ROOT", tmp_path)
    monkeypatch.setattr(watch, "DEFAULT_ENV", tmp_path / ".env")
    monkeypatch.setenv("ICE_MAST_PROGRAM", "1201")
    monkeypatch.setenv("ICE_MAST_STATE", "state/mast-watch.json")
    monkeypatch.setenv("ICE_MAST_EVENT_DIR", "events")
    state = tmp_path / "state/mast-watch.json"
    state.parent.mkdir()
    state.write_text('{"version": 1, "program": 1201, "seen": ["old-dataset"]}')
    rows = [{
        "program": 1201,
        "program_category": "COM",
        "program_title": "Ice Characterization",
        "fileSetName": "r0120101001001001001_0001_wfi01_f062",
        "optical_element": "F062",
    }]
    report = watch.execute("poll", client=FakeClient(rows))
    assert report["status"] == "migrated"
    assert report["new_count"] == 0
    assert not list((tmp_path / "events").glob("*.json"))
    assert watch.load_state(state)["version"] == 2
