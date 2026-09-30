class ParkingDomainException(Exception):
    """Базовое исключение парковки."""


class DomainInvariantViolation(ParkingDomainException):
    """Нарушен инвариант парковки."""


class InvalidValueObject(ParkingDomainException):
    """Некорректный Value Object."""