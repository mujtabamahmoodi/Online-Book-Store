from decimal import Decimal

from .models import Book


class Cart:
    """Session-based shopping cart."""

    SESSION_KEY = "bookstore_cart"

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(self.SESSION_KEY, {})

    def save(self):
        # Session data must stay JSON-serializable.
        for item in self.cart.values():
            item["price"] = str(item["price"])
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def add(
        self,
        book: Book,
        quantity: int = 1,
        override_quantity: bool = False,
        unit_price=None,
    ):
        book_id = str(book.id)
        resolved_price = unit_price if unit_price is not None else book.current_price

        if book_id not in self.cart:
            self.cart[book_id] = {"quantity": 0, "price": str(resolved_price)}
        else:
            self.cart[book_id]["price"] = str(resolved_price)

        if override_quantity:
            self.cart[book_id]["quantity"] = quantity
        else:
            self.cart[book_id]["quantity"] += quantity
        self.save()

    def remove(self, book: Book):
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        self.session[self.SESSION_KEY] = {}
        self.session.modified = True

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def __iter__(self):
        book_ids = self.cart.keys()
        books = Book.objects.filter(id__in=book_ids)
        books_map = {str(book.id): book for book in books}

        for book_id, item in self.cart.items():
            if book_id not in books_map:
                continue
            data = item.copy()
            data["book"] = books_map[book_id]
            data["price"] = Decimal(str(data["price"]))
            data["total_price"] = data["price"] * data["quantity"]
            yield data

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )
