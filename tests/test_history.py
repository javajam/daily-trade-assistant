from datetime import datetime, timezone

from dta_bot.history import parse_yahoo_chart
from dta_bot.timeframes import normalize


def test_parse_yahoo_chart_skips_null_bars():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1_000, 1_900, 2_800],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0, None, 11.0],
                                "high": [10.5, 10.6, 11.5],
                                "low": [9.5, 9.8, 10.8],
                                "close": [10.2, 10.4, 11.2],
                                "volume": [100, 200, 300],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }
    bars = parse_yahoo_chart(payload)
    assert len(bars) == 2
    assert bars[0].timestamp == datetime.fromtimestamp(1_000, tz=timezone.utc)
    assert bars[0].close == 10.2
    assert bars[1].open == 11.0
    assert bars[1].volume == 300


def test_normalize_matches_yahoo_keys():
    assert normalize("15m") == "15Min"
    assert normalize("1h") == "1Hour"
