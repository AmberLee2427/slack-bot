import notify


def test_alert_has_analysis_button():
    event = {
        "program": 1201,
        "checked_at": "2026-09-17T00:00:00+00:00",
        "new_count": 1,
        "new_datasets": [{
            "fileSetName": "roman-example",
            "filename": "roman-example_cal.asdf",
        }],
    }
    blocks = notify.alert_blocks(event)
    button = blocks[1]["elements"][0]
    assert button["type"] == "button"
    assert button["url"] == notify.ANALYSIS_URL
    assert button["style"] == "primary"
    assert "roman-example_cal.asdf" in blocks[0]["text"]["text"]
