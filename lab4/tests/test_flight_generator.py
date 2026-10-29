from datetime import date

from app.flight_generator import generate_daily_flights


def test_generation_is_repeatable_for_same_seed_and_date():
    arguments = {
        "flight_date": date(2026, 10, 26),
        "count": 5,
        "seed": 20261026,
        "carrier": "OWN",
    }
    assert generate_daily_flights(**arguments) == generate_daily_flights(**arguments)


def test_generated_flight_duration_is_one_to_six_hours():
    flights = generate_daily_flights(
        flight_date=date(2026, 10, 26), count=100, seed=15, carrier="TEST"
    )
    for flight in flights:
        duration_seconds = (flight["arrival_at"] - flight["departure_at"]).total_seconds()
        assert 3600 <= duration_seconds <= 6 * 3600
        assert flight["origin"] != flight["destination"]
        assert flight["departure_at"].date() == date(2026, 10, 26)
