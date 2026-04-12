from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("book/<slug:slug>/", views.book_detail, name="book_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:book_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:book_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/", views.update_cart, name="update_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_history, name="order_history"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),
    path("signup/", views.signup, name="signup"),
]
