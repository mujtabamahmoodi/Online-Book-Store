from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .models import Book, BookDiscount, Category, Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "email", "address", "city", "postal_code", "country"]
        widgets = {
            "address": forms.TextInput(attrs={"placeholder": _("Street and house number")}),
            "postal_code": forms.TextInput(attrs={"placeholder": "1001"}),
        }


class CartUpdateForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class AdminBookCreateForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "category",
            "title",
            "title_fa",
            "author",
            "author_fa",
            "isbn",
            "description",
            "description_fa",
            "price",
            "stock",
            "cover_image",
            "cover_url",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "description_fa": forms.Textarea(attrs={"rows": 3}),
        }

    def save(self, commit=True):
        book = super().save(commit=False)
        base_slug = slugify(book.title)[:200] or "book"
        slug = base_slug
        counter = 2
        while Book.objects.filter(slug=slug).exclude(pk=book.pk).exists():
            slug = f"{base_slug}-{counter}"[:220]
            counter += 1
        book.slug = slug
        if commit:
            book.save()
        return book


class AdminDiscountCreateForm(forms.ModelForm):
    class Meta:
        model = BookDiscount
        fields = ["book", "name", "percentage", "starts_at", "ends_at", "is_active"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["book"].queryset = Book.objects.order_by("title")

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            raise forms.ValidationError(_("End time must be later than start time."))
        return cleaned_data


class AdminCategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "name_fa"]
