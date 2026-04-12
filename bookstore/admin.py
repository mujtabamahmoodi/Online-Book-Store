from django.contrib import admin

from .models import Book, BookDiscount, Category, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "price", "stock")
    list_filter = ("category",)
    list_editable = ("price", "stock")
    search_fields = ("title", "author", "isbn")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BookDiscount)
class BookDiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "percentage", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("name", "book__title")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "quantity", "price_at_purchase")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email")
    inlines = [OrderItemInline]
