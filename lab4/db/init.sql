CREATE TABLE IF NOT EXISTS flights (
    id BIGSERIAL PRIMARY KEY,
    carrier VARCHAR(32) NOT NULL,
    flight_number VARCHAR(32) NOT NULL,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    departure_at TIMESTAMP NOT NULL,
    arrival_at TIMESTAMP NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    CHECK (origin <> destination)
);

CREATE INDEX IF NOT EXISTS ix_flights_departure_at ON flights (departure_at);
CREATE INDEX IF NOT EXISTS ix_flights_origin_departure ON flights (origin, departure_at);
