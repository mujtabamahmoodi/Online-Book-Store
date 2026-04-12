from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    name_fa = models.CharField(max_length=80, blank=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        lang = get_language() or "en"
        if lang.startswith("fa") and self.name_fa:
            return self.name_fa
        return self.name


class Book(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="books",
    )
    title = models.CharField(max_length=200)
    title_fa = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    author = models.CharField(max_length=120)
    author_fa = models.CharField(max_length=120, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    description = models.TextField()
    description_fa = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    cover_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "title"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    @property
    def display_title(self) -> str:
        lang = get_language() or "en"
        if lang.startswith("fa") and self.title_fa:
            return self.title_fa
        return self.title

    @property
    def display_author(self) -> str:
        lang = get_language() or "en"
        if lang.startswith("fa") and self.author_fa:
            return self.author_fa
        return self.author

    @property
    def display_description(self) -> str:
        lang = get_language() or "en"
        if lang.startswith("fa") and self.description_fa:
            return self.description_fa
        return self.description

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def get_active_discount(self, at=None):
        if at is None and hasattr(self, "_discount_resolved"):
            return self._active_discount_cache

        check_time = at or timezone.now()
        discount = (
            self.discounts.filter(
                is_active=True,
                starts_at__lte=check_time,
                ends_at__gte=check_time,
            )
            .order_by("-percentage", "-starts_at")
            .first()
        )

        if at is None:
            self._active_discount_cache = discount
            self._discount_resolved = True

        return discount

    @property
    def active_discount(self):
        return self.get_active_discount()

    @property
    def has_active_discount(self) -> bool:
        return self.active_discount is not None

    @property
    def current_price(self) -> Decimal:
        discount = self.active_discount
        if not discount:
            return self.price

        multiplier = (Decimal("100.00") - discount.percentage) / Decimal("100.00")
        discounted = (self.price * multiplier).quantize(Decimal("0.01"))
        return max(discounted, Decimal("0.01"))

    def get_absolute_url(self) -> str:
        return reverse("book_detail", kwargs={"slug": self.slug})


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PAID = "paid", _("Paid")
        SHIPPED = "shipped", _("Shipped")
        COMPLETED = "completed", _("Completed")
        CANCELED = "canceled", _("Canceled")

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.full_name}"

    def recalculate_total(self) -> None:
        total = sum((item.subtotal for item in self.items.all()), Decimal("0.00"))
        self.total_price = total
        self.save(update_fields=["total_price"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("order", "book")

    def __str__(self) -> str:
        return f"{self.quantity} x {self.book.title}"

    @property
    def subtotal(self) -> Decimal:
        return self.price_at_purchase * self.quantity


class BookDiscount(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="discounts")
    name = models.CharField(max_length=120)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("99.99"))],
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.percentage}% off) - {self.book.title}"

    @property
    def is_current(self) -> bool:
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError(_("Discount end time must be later than start time."))
