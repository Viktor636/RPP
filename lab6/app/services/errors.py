class NotFound(Exception):
    """Сущность не найдена."""


class TransitionNotAllowed(Exception):
    """Событие недопустимо в текущем состоянии заказа."""


class OrderValidationError(Exception):
    """Нарушено правило оформления заказа."""
