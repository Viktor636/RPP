from datetime import date, datetime

from app.route_builder import build_routes


def flight(number, origin, destination, depart, arrive, price=100):
    return {
        "carrier": "TEST",
        "flight_number": number,
        "origin": origin,
        "destination": destination,
        "departure_at": datetime.fromisoformat(depart),
        "arrival_at": datetime.fromisoformat(arrive),
        "price": price,
    }


def test_direct_route_is_returned():
    flights = [flight("T1", "OVB", "SVO", "2026-10-26T08:00:00", "2026-10-26T11:00:00", 9000)]
    routes = build_routes(flights, "OVB", "SVO", date(2026, 10, 26))
    assert len(routes) == 1
    assert routes[0]["stops"] == 0
    assert routes[0]["total_price"] == 9000


def test_connection_must_be_between_one_and_six_hours():
    flights = [
        flight("T1", "OVB", "KZN", "2026-10-26T08:00:00", "2026-10-26T10:00:00", 5000),
        flight("T2", "KZN", "SVO", "2026-10-26T11:00:00", "2026-10-26T13:00:00", 4000),
        flight("T3", "OVB", "SVO", "2026-10-26T07:00:00", "2026-10-26T10:00:00", 12000),
    ]
    routes = build_routes(flights, "OVB", "SVO", date(2026, 10, 26))
    assert any(route["stops"] == 1 and route["total_price"] == 9000 for route in routes)


def test_route_cannot_repeat_airport():
    flights = [
        flight("T1", "OVB", "KZN", "2026-10-26T06:00:00", "2026-10-26T08:00:00", 1000),
        flight("T2", "KZN", "OVB", "2026-10-26T09:00:00", "2026-10-26T11:00:00", 1000),
        flight("T3", "OVB", "SVO", "2026-10-26T12:00:00", "2026-10-26T15:00:00", 1000),
    ]
    routes = build_routes(flights, "OVB", "SVO", date(2026, 10, 26))
    assert all("OVB" not in [f["destination"] for f in route["flights"][:-1] ] for route in routes)
