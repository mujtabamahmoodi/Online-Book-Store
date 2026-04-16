from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import (
    AdminBookCreateForm,
    AdminCategoryCreateForm,
    AdminDiscountCreateForm,
    CheckoutForm,
    SignUpForm,
)
from .models import Book, BookDiscount, Category, Order, OrderItem


def home(request):
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    books = Book.objects.select_related("category").all()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(title_fa__icontains=query)
            | Q(author__icontains=query)
            | Q(author_fa__icontains=query)
            | Q(isbn__icontains=query)
            | Q(description__icontains=query)
            | Q(description_fa__icontains=query)
        )

    if selected_category:
        books = books.filter(category__slug=selected_category)

    paginator = Paginator(books, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "query": query,
        "selected_category": selected_category,
    }
    return render(request, "bookstore/home.html", context)


def book_detail(request, slug):
    book = get_object_or_404(Book.objects.select_related("category"), slug=slug)
    return render(request, "bookstore/book_detail.html", {"book": book})


@login_required
@require_POST
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)

    if book.stock <= 0:
        messages.error(
            request,
            _('"%(title)s" is currently out of stock.') % {"title": book.display_title},
        )
        return redirect("book_detail", slug=book.slug)

    cart = Cart(request)
    current_qty = 0
    for item in cart:
        if item["book"].id == book.id:
            current_qty = item["quantity"]
            break

    if current_qty + quantity > book.stock:
        messages.error(
            request,
            _('Only %(stock)s copies of "%(title)s" are available.')
            % {"stock": book.stock, "title": book.display_title},
        )
        return redirect("book_detail", slug=book.slug)

    cart.add(book=book, quantity=quantity, unit_price=book.current_price)
    messages.success(
        request,
        _('"%(title)s" added to your cart.') % {"title": book.display_title},
    )
    return redirect("cart_detail")


@login_required
@require_POST
def remove_from_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart = Cart(request)
    cart.remove(book)
    messages.info(
        request,
        _('"%(title)s" removed from your cart.') % {"title": book.display_title},
    )
    return redirect("cart_detail")


@login_required
@require_POST
def update_cart(request):
    cart = Cart(request)
    for item in list(cart):
        field_name = f"quantity_{item['book'].id}"
        if field_name in request.POST:
            try:
                requested_qty = int(request.POST[field_name])
            except (TypeError, ValueError):
                requested_qty = item["quantity"]

            if requested_qty > item["book"].stock:
                messages.warning(
                    request,
                    _('Adjusted "%(title)s" to available stock (%(stock)s).')
                    % {
                        "title": item["book"].display_title,
                        "stock": item["book"].stock,
                    },
                )
                requested_qty = item["book"].stock

            if requested_qty <= 0 or item["book"].stock <= 0:
                cart.remove(item["book"])
            elif requested_qty > 0:
                cart.add(
                    item["book"],
                    quantity=requested_qty,
                    override_quantity=True,
                    unit_price=item["book"].current_price,
                )
    messages.success(request, _("Cart updated."))
    return redirect("cart_detail")


@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, "bookstore/cart.html", {"cart": cart})


@login_required
def checkout(request):
    cart = Cart(request)
    cart_items = list(cart)

    if not cart_items:
        messages.info(request, _("Your cart is empty."))
        return redirect("home")

    for item in cart_items:
        if item["quantity"] > item["book"].stock:
            messages.warning(
                request,
                _('Not enough stock for "%(title)s". Please update your cart.')
                % {"title": item["book"].display_title},
            )
            return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()

                for item in cart_items:
                    book = item["book"]
                    qty = item["quantity"]
                    OrderItem.objects.create(
                        order=order,
                        book=book,
                        quantity=qty,
                        price_at_purchase=item["price"],
                    )
                    book.stock -= qty
                    book.save(update_fields=["stock"])

                order.recalculate_total()
                cart.clear()

            messages.success(request, _("Order placed successfully."))
            return redirect("order_success", order_id=order.id)
    else:
        initial_data = {
            "full_name": f"{request.user.first_name} {request.user.last_name}".strip(),
            "email": request.user.email,
        }
        form = CheckoutForm(initial=initial_data)

    return render(
        request,
        "bookstore/checkout.html",
        {"form": form, "cart_items": cart_items, "cart_total": cart.get_total_price()},
    )


@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__book"), id=order_id, user=request.user
    )
    return render(request, "bookstore/order_success.html", {"order": order})


@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__book")
        .order_by("-created_at")
    )
    return render(request, "bookstore/order_history.html", {"orders": orders})


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            customer_group, created = Group.objects.get_or_create(name="customer")
            user.groups.add(customer_group)
            login(request, user)
            messages.success(request, _("Welcome! Your account has been created."))
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "bookstore/signup.html", {"form": form})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, _("Main admin access is required for this page."))
        return redirect("home")

    category_form = AdminCategoryCreateForm(prefix="category")
    book_form = AdminBookCreateForm(prefix="book")
    discount_form = AdminDiscountCreateForm(prefix="discount")

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "update_order_status":
            order_id = request.POST.get("order_id")
            status = request.POST.get("status")
            order = get_object_or_404(Order, id=order_id)
            allowed_statuses = {choice[0] for choice in Order.Status.choices}
            if status in allowed_statuses:
                order.status = status
                order.save(update_fields=["status"])
                messages.success(
                    request,
                    _("Order #%(order_id)s status updated.")
                    % {"order_id": order.id},
                )
            else:
                messages.error(request, _("Invalid order status selected."))
            return redirect("admin_dashboard")

        if action == "create_book":
            book_form = AdminBookCreateForm(request.POST, request.FILES, prefix="book")
            if book_form.is_valid():
                new_book = book_form.save()
                messages.success(
                    request,
                    _("Book '%(title)s' added successfully.")
                    % {"title": new_book.display_title},
                )
                return redirect("admin_dashboard")
            messages.error(request, _("Please fix the book form errors and try again."))

        if action == "create_category":
            category_form = AdminCategoryCreateForm(request.POST, prefix="category")
            if category_form.is_valid():
                category = category_form.save(commit=False)
                base_slug = slugify(category.name)[:90] or "category"
                slug = base_slug
                counter = 2
                while Category.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"[:100]
                    counter += 1
                category.slug = slug
                category.save()
                messages.success(
                    request,
                    _("Category '%(name)s' created.") % {"name": category.name},
                )
                return redirect("admin_dashboard")
            messages.error(request, _("Please fix the category form errors and try again."))

        if action == "update_book":
            book_id = request.POST.get("book_id")
            book = get_object_or_404(Book, id=book_id)
            raw_stock = request.POST.get("stock", "").strip()
            raw_price = request.POST.get("price", "").strip()

            try:
                stock = int(raw_stock)
                if stock < 0:
                    raise ValueError
            except ValueError:
                messages.error(
                    request,
                    _("Invalid stock value for '%(title)s'.")
                    % {"title": book.display_title},
                )
                return redirect("admin_dashboard")

            try:
                price = Decimal(raw_price)
                if price <= Decimal("0"):
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                messages.error(
                    request,
                    _("Invalid price value for '%(title)s'.")
                    % {"title": book.display_title},
                )
                return redirect("admin_dashboard")

            book.stock = stock
            book.price = price
            book.save(update_fields=["stock", "price"])
            messages.success(
                request,
                _("Updated inventory for '%(title)s'.") % {"title": book.display_title},
            )
            return redirect("admin_dashboard")

        if action == "create_discount":
            discount_form = AdminDiscountCreateForm(request.POST, prefix="discount")
            if discount_form.is_valid():
                discount = discount_form.save()
                messages.success(
                    request,
                    _(
                        "Discount '%(name)s' added for '%(book)s' (%(percentage)s%% off)."
                    )
                    % {
                        "name": discount.name,
                        "book": discount.book.display_title,
                        "percentage": discount.percentage,
                    },
                )
                return redirect("admin_dashboard")
            messages.error(request, _("Please fix discount form errors and try again."))

        if action == "toggle_discount":
            discount_id = request.POST.get("discount_id")
            discount = get_object_or_404(BookDiscount, id=discount_id)
            discount.is_active = not discount.is_active
            discount.save(update_fields=["is_active"])
            state = _("enabled") if discount.is_active else _("disabled")
            messages.success(
                request,
                _("Discount '%(name)s' %(state)s.")
                % {"name": discount.name, "state": state},
            )
            return redirect("admin_dashboard")

    orders = (
        Order.objects.select_related("user")
        .prefetch_related("items__book")
        .order_by("-created_at")[:12]
    )
    book_query = request.GET.get("book_q", "").strip()
    books = Book.objects.select_related("category").order_by("stock", "title")
    if book_query:
        books = books.filter(
            Q(title__icontains=book_query)
            | Q(title_fa__icontains=book_query)
            | Q(author__icontains=book_query)
            | Q(author_fa__icontains=book_query)
            | Q(isbn__icontains=book_query)
        )
    books = books[:50]

    low_stock_books = Book.objects.filter(stock__lte=5).order_by("stock", "title")[:8]
    discounts = BookDiscount.objects.select_related("book").order_by("-starts_at")[:15]

    total_revenue = (
        Order.objects.exclude(status=Order.Status.CANCELED).aggregate(
            total=Sum("total_price")
        )["total"]
        or Decimal("0.00")
    )
    total_revenue = total_revenue.quantize(Decimal("0.01"))

    context = {
        "total_books": Book.objects.count(),
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "total_users": Group.objects.get_or_create(name="customer")[0].user_set.count(),
        "active_discounts": BookDiscount.objects.filter(
            is_active=True,
            starts_at__lte=timezone.now(),
            ends_at__gte=timezone.now(),
        ).count(),
        "total_revenue": total_revenue,
        "orders": orders,
        "books": books,
        "low_stock_books": low_stock_books,
        "discounts": discounts,
        "book_query": book_query,
        "category_form": category_form,
        "book_form": book_form,
        "discount_form": discount_form,
        "order_status_choices": Order.Status.choices,
    }
    return render(request, "bookstore/admin_dashboard.html", context)
