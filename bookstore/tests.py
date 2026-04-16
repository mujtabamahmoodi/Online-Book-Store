import shutil
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from .models import Book, BookDiscount, Category, Order, OrderItem


class BookstoreViewsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fiction", name_fa="داستانی", slug="fiction")
        self.book = Book.objects.create(
            category=self.category,
            title="Test Book",
            title_fa="کتاب آزمایشی",
            slug="test-book",
            author="Test Author",
            author_fa="نویسنده آزمایشی",
            isbn="1234567890123",
            description="A test book.",
            description_fa="یک کتاب آزمایشی.",
            price="10.00",
            stock=10,
        )
        self.user = User.objects.create_user("reader", "reader@example.com", "password123")
        self.staff_user = User.objects.create_user(
            "manager",
            "manager@example.com",
            "password123",
            is_staff=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Reader User",
            email="reader@example.com",
            address="Street 1",
            city="Kabul",
            postal_code="1001",
            country="Afghanistan",
            status=Order.Status.PENDING,
            total_price="20.00",
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Online Book Store")

    def test_localized_book_properties_in_persian(self):
        with override("fa"):
            self.assertEqual(self.category.display_name, "داستانی")
            self.assertEqual(self.book.display_title, "کتاب آزمایشی")
            self.assertEqual(self.book.display_author, "نویسنده آزمایشی")
            self.assertEqual(self.book.display_description, "یک کتاب آزمایشی.")

    def test_add_to_cart_requires_login(self):
        response = self.client.post(reverse("add_to_cart", args=[self.book.id]), {"quantity": 2})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_add_to_cart_for_authenticated_simple_user(self):
        self.client.login(username="reader", password="password123")
        response = self.client.post(reverse("add_to_cart", args=[self.book.id]), {"quantity": 2})
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get("bookstore_cart", {})
        self.assertEqual(cart[str(self.book.id)]["quantity"], 2)

    def test_checkout_creates_order_for_authenticated_user(self):
        self.client.login(username="reader", password="password123")
        initial_orders = Order.objects.count()
        self.client.post(reverse("add_to_cart", args=[self.book.id]), {"quantity": 1})
        response = self.client.post(
            reverse("checkout"),
            {
                "full_name": "Reader User",
                "email": "reader@example.com",
                "address": "Street 1",
                "city": "Kabul",
                "postal_code": "1001",
                "country": "Afghanistan",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), initial_orders + 1)

    def test_update_cart_after_iteration_does_not_store_decimal_in_session(self):
        self.client.login(username="reader", password="password123")
        self.client.post(reverse("add_to_cart", args=[self.book.id]), {"quantity": 1})
        self.client.get(reverse("cart_detail"))
        response = self.client.post(
            reverse("update_cart"),
            {f"quantity_{self.book.id}": 2},
        )
        self.assertEqual(response.status_code, 302)

        session_cart = self.client.session.get("bookstore_cart", {})
        self.assertEqual(session_cart[str(self.book.id)]["quantity"], 2)
        self.assertIsInstance(session_cart[str(self.book.id)]["price"], str)

    def test_signup_creates_simple_user_role(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "simpleuser",
                "email": "simple@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="simpleuser")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name="customer").exists())
        self.assertTrue(Group.objects.filter(name="customer").exists())

    def test_admin_dashboard_requires_staff(self):
        self.client.login(username="reader", password="password123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_admin_dashboard_access_for_staff(self):
        self.client.login(username="manager", password="password123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Store Control Center")

    def test_admin_can_update_order_status_from_dashboard(self):
        self.client.login(username="manager", password="password123")
        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "update_order_status",
                "order_id": self.order.id,
                "status": Order.Status.SHIPPED,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)

    def test_admin_can_update_book_inventory_from_dashboard(self):
        self.client.login(username="manager", password="password123")
        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "update_book",
                "book_id": self.book.id,
                "stock": 23,
                "price": "15.50",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 23)
        self.assertEqual(str(self.book.price), "15.50")

    def test_admin_can_create_book_from_dashboard(self):
        self.client.login(username="manager", password="password123")
        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "create_book",
                "book-category": self.category.id,
                "book-title": "New Admin Book",
                "book-author": "Admin Author",
                "book-isbn": "9876543210123",
                "book-description": "Added by admin dashboard.",
                "book-price": "19.99",
                "book-stock": 7,
                "book-cover_url": "https://example.com/cover.jpg",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Book.objects.filter(title="New Admin Book").exists())

    def test_admin_can_create_book_with_uploaded_cover(self):
        self.client.login(username="manager", password="password123")
        upload = SimpleUploadedFile(
            "cover.jpg",
            b"fake image bytes",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "create_book",
                "book-category": self.category.id,
                "book-title": "Uploaded Cover Book",
                "book-author": "Admin Author",
                "book-isbn": "1231231231231",
                "book-description": "Book with uploaded cover file.",
                "book-price": "11.99",
                "book-stock": 3,
                "book-cover_image": upload,
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Book.objects.get(title="Uploaded Cover Book")
        self.assertTrue(created.cover_image.name.startswith("book_covers/"))

    def test_admin_can_create_category_from_dashboard(self):
        self.client.login(username="manager", password="password123")
        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "create_category",
                "category-name": "Poetry",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name="Poetry").exists())

    def test_admin_can_create_time_based_discount(self):
        self.client.login(username="manager", password="password123")
        starts_at = (timezone.localtime() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        ends_at = (timezone.localtime() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")

        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "create_discount",
                "discount-book": self.book.id,
                "discount-name": "Weekend Sale",
                "discount-percentage": "20.00",
                "discount-starts_at": starts_at,
                "discount-ends_at": ends_at,
                "discount-is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BookDiscount.objects.filter(name="Weekend Sale").exists())

        refreshed_book = Book.objects.get(id=self.book.id)
        self.assertEqual(str(refreshed_book.current_price), "8.00")

    def test_discounted_price_is_saved_in_order_item(self):
        BookDiscount.objects.create(
            book=self.book,
            name="Flash Sale",
            percentage="25.00",
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=5),
            is_active=True,
        )
        self.client.login(username="reader", password="password123")
        self.client.post(reverse("add_to_cart", args=[self.book.id]), {"quantity": 1})
        self.client.post(
            reverse("checkout"),
            {
                "full_name": "Reader User",
                "email": "reader@example.com",
                "address": "Street 1",
                "city": "Kabul",
                "postal_code": "1001",
                "country": "Afghanistan",
            },
        )

        latest_order = Order.objects.latest("id")
        order_item = OrderItem.objects.get(order=latest_order, book=self.book)
        self.assertEqual(str(order_item.price_at_purchase), "7.50")


class LocalizeBookCoversCommandTests(TestCase):
    def setUp(self):
        self.temp_media = Path.cwd() / "test_media_root"
        self.temp_media.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.temp_media, True)
        self.override_media = override_settings(MEDIA_ROOT=str(self.temp_media))
        self.override_media.enable()
        self.addCleanup(self.override_media.disable)

        self.category = Category.objects.create(name="Technology", slug="technology")
        self.book = Book.objects.create(
            category=self.category,
            title="Clean Code",
            slug="clean-code",
            author="Robert C. Martin",
            description="A handbook of software craftsmanship.",
            price="18.00",
            stock=9,
            cover_url="https://example.com/clean-code.jpg",
        )
        self.invalid_book = Book.objects.create(
            category=self.category,
            title="Broken Cover",
            slug="broken-cover",
            author="Unknown",
            description="This URL does not return an image.",
            price="5.00",
            stock=1,
            cover_url="https://example.com/not-an-image",
        )

    def test_localize_book_covers_downloads_images_and_skips_non_images(self):
        class FakeHeaders:
            def __init__(self, content_type):
                self._content_type = content_type

            def get_content_type(self):
                return self._content_type

        class FakeResponse:
            def __init__(self, content_type, body):
                self.headers = FakeHeaders(content_type)
                self._body = body

            def read(self):
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(request, timeout=20):
            if "not-an-image" in request.full_url:
                return FakeResponse("text/html", b"<html></html>")
            return FakeResponse("image/jpeg", b"fake-jpeg-bytes")

        with patch(
            "bookstore.management.commands.localize_book_covers.urlopen",
            side_effect=fake_urlopen,
        ):
            call_command("localize_book_covers")

        self.book.refresh_from_db()
        self.invalid_book.refresh_from_db()

        self.assertEqual(self.book.cover_image.name, "book_covers/clean-code.jpg")
        self.assertTrue(self.book.cover_image.storage.exists(self.book.cover_image.name))
        self.assertEqual(self.invalid_book.cover_image.name, "")


class SeedBooksCommandTests(TestCase):
    def test_seed_books_assigns_repo_local_cover_images_when_configured(self):
        call_command("seed_books")

        self.assertEqual(
            Book.objects.get(slug="clean-code").cover_image.name,
            "book_covers/clean-code.jpg",
        )
        self.assertEqual(
            Book.objects.get(slug="atomic-habits").cover_image.name,
            "book_covers/atomic-habits.jpg",
        )
