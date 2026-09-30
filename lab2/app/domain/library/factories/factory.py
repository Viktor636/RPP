from uuid import UUID

from ..entities.models import Book
from ..value_objects.values import BookId, CopyId


class BookFactory:

    @staticmethod
    def from_state(data: dict) -> Book:
        copies = {
            CopyId(UUID(copy_id))
            for copy_id in data["copies"]
        }

        borrowed_copies = {
            CopyId(UUID(copy_id))
            for copy_id in data["borrowed_copies"]
        }

        return Book(
            book_id=BookId(UUID(data["id"])),
            title=data["title"],
            copies=copies,
            borrowed_copies=borrowed_copies,
        )