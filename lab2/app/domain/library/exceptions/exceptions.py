class LibraryDomainException(Exception):
    """Базовое исключение библиотеки."""


class DomainInvariantViolation(LibraryDomainException):
    """Нарушен инвариант предметной области."""


class InvalidValueObject(LibraryDomainException):
    """Некорректное значение Value Object."""