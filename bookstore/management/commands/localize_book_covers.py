import mimetypes
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from bookstore.models import Book


class Command(BaseCommand):
    help = "Download remote book cover URLs into local media/book_covers/ storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing local cover_image files as well.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        localized = 0
        skipped = 0

        books = Book.objects.exclude(cover_url="")
        if not overwrite:
            books = books.filter(cover_image="")

        for book in books:
            try:
                filename, content = self._download_cover(book)
            except ValueError as exc:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipped {book.slug}: {exc}"))
                continue
            except (HTTPError, URLError) as exc:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"Skipped {book.slug}: could not download cover ({exc})")
                )
                continue

            book.cover_image.save(filename, ContentFile(content), save=False)
            book.save(update_fields=["cover_image"])
            localized += 1
            self.stdout.write(self.style.SUCCESS(f"Localized {book.slug} -> {book.cover_image.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Localized {localized} cover(s); skipped {skipped} book(s)."
            )
        )

    def _download_cover(self, book):
        if not book.cover_url:
            raise ValueError("missing cover URL")

        request = Request(
            book.cover_url,
            headers={"User-Agent": "OnlineBookStore/1.0"},
        )
        with urlopen(request, timeout=20) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise ValueError(f"URL did not return an image ({content_type})")

            content = response.read()
            if not content:
                raise ValueError("empty image response")

            extension = self._guess_extension(book.cover_url, content_type)
            filename = f"{book.slug}{extension}"
            return filename, content

    def _guess_extension(self, url, content_type):
        guessed_from_type = mimetypes.guess_extension(content_type)
        if guessed_from_type:
            return guessed_from_type

        suffix = Path(urlparse(url).path).suffix.lower()
        if suffix:
            return suffix

        return ".jpg"
