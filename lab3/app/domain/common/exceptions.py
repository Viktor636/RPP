class DomainError(Exception):
    pass


class DomainInvariantViolation(DomainError):
    pass


class InvalidValueObject(DomainError):
    pass


class TransitionNotAllowed(DomainError):
    def __init__(self, state: str, event: str) -> None:
        self.state = state
        self.event = event
        super().__init__(f"Переход '{event}' недопустим из состояния '{state}'")


class EntityNotFound(DomainError):
    pass