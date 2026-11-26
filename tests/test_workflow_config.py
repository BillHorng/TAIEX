from pathlib import Path


def test_market_schedule_avoids_top_of_hour_and_maps_nominal_slots() -> None:
    workflow = Path(".github/workflows/track-market.yml").read_text(encoding="utf-8")
    expected = {
        "7 1 * * 1-5": "09:00",
        "7 3 * * 1-5": "11:00",
        "7 5 * * 1-5": "13:00",
        "7 7 * * 1-5": "15:00",
    }
    for cron, slot in expected.items():
        assert f'cron: "{cron}"' in workflow
        if cron == "7 7 * * 1-5":
            assert f'"{cron}"|"17 8 * * 1-5") slot="{slot}"' in workflow
        else:
            assert f'"{cron}") slot="{slot}"' in workflow
    assert 'cron: "17 8 * * 1-5"' in workflow
    assert "run-status.json" in workflow
