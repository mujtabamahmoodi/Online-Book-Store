from django.core.management.base import BaseCommand
from django.utils.text import slugify

from bookstore.models import Book, Category


BOOKS = [
    {
        "category": "Classic Literature",
        "category_fa": "ادبیات کلاسیک",
        "title": "Pride and Prejudice",
        "title_fa": "غرور و تعصب",
        "author": "Jane Austen",
        "author_fa": "جین آستن",
        "isbn": "9780141439518",
        "description": "A timeless romance and social satire set in 19th-century England.",
        "description_fa": "داستانی عاشقانه و طنزی اجتماعی از انگلستان قرن نوزدهم.",
        "price": "8.99",
        "stock": 12,
        "cover_url": "https://images.unsplash.com/photo-1455885666463-9b0ce5f7db7f?auto=format&fit=crop&w=800&q=80",
    },
    {
        "category": "Science Fiction",
        "category_fa": "علمی تخیلی",
        "title": "Dune",
        "title_fa": "تل‌ماسه",
        "author": "Frank Herbert",
        "author_fa": "فرانک هربرت",
        "isbn": "9780441172719",
        "description": "An epic science-fiction story of politics, prophecy, and survival on Arrakis.",
        "description_fa": "روایتی حماسی از سیاست، پیشگویی و بقا در سیاره آراکیس.",
        "price": "12.50",
        "stock": 15,
        "cover_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80",
    },
    {
        "category": "Self Development",
        "category_fa": "خودسازی",
        "title": "Atomic Habits",
        "title_fa": "عادت‌های اتمی",
        "author": "James Clear",
        "author_fa": "جیمز کلیر",
        "isbn": "9780735211292",
        "description": "Practical strategies for building good habits and breaking bad ones.",
        "description_fa": "راهبردهای کاربردی برای ساخت عادت‌های خوب و ترک عادت‌های بد.",
        "price": "14.25",
        "stock": 20,
        "cover_url": "https://images.unsplash.com/photo-1528740561666-dc2479dc08ab?auto=format&fit=crop&w=800&q=80",
    },
    {
        "category": "Business",
        "category_fa": "کسب‌وکار",
        "title": "The Lean Startup",
        "title_fa": "استارتاپ ناب",
        "author": "Eric Ries",
        "author_fa": "اریک ریس",
        "isbn": "9780307887894",
        "description": "A modern framework for building startups through rapid experimentation.",
        "description_fa": "چارچوبی مدرن برای ساخت استارتاپ با آزمایش‌های سریع.",
        "price": "13.40",
        "stock": 11,
        "cover_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=800&q=80",
    },
    {
        "category": "Technology",
        "category_fa": "فناوری",
        "title": "Clean Code",
        "title_fa": "کدنویسی تمیز",
        "author": "Robert C. Martin",
        "author_fa": "رابرت سی. مارتین",
        "isbn": "9780132350884",
        "description": "A practical handbook of software craftsmanship and maintainable code.",
        "description_fa": "راهنمایی کاربردی برای مهارت نرم‌افزاری و کدهای قابل نگهداری.",
        "price": "18.00",
        "stock": 9,
        "cover_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&q=80",
    },
    {
        "category": "History",
        "category_fa": "تاریخ",
        "title": "Sapiens",
        "title_fa": "انسان خردمند",
        "author": "Yuval Noah Harari",
        "author_fa": "یووال نوح هراری",
        "isbn": "9780062316097",
        "description": "A brief history of humankind from prehistoric times to today.",
        "description_fa": "تاریخچه‌ای کوتاه از انسان از دوران باستان تا امروز.",
        "price": "16.75",
        "stock": 14,
        "cover_url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=800&q=80",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample book categories and products."

    def handle(self, *args, **options):
        created_books = 0
        for entry in BOOKS:
            category_name = entry["category"]
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    "slug": slugify(category_name),
                    "name_fa": entry.get("category_fa", ""),
                },
            )
            if entry.get("category_fa") and not category.name_fa:
                category.name_fa = entry["category_fa"]
                category.save(update_fields=["name_fa"])

            defaults = {
                "category": category,
                "author": entry["author"],
                "author_fa": entry.get("author_fa", ""),
                "isbn": entry["isbn"],
                "description": entry["description"],
                "description_fa": entry.get("description_fa", ""),
                "price": entry["price"],
                "stock": entry["stock"],
                "cover_url": entry["cover_url"],
                "title_fa": entry.get("title_fa", ""),
            }
            book, created = Book.objects.get_or_create(
                slug=slugify(entry["title"]),
                defaults={"title": entry["title"], **defaults},
            )
            if created:
                created_books += 1
            else:
                updated_fields = []
                if entry.get("title_fa") and not book.title_fa:
                    book.title_fa = entry["title_fa"]
                    updated_fields.append("title_fa")
                if entry.get("author_fa") and not book.author_fa:
                    book.author_fa = entry["author_fa"]
                    updated_fields.append("author_fa")
                if entry.get("description_fa") and not book.description_fa:
                    book.description_fa = entry["description_fa"]
                    updated_fields.append("description_fa")
                if updated_fields:
                    book.save(update_fields=updated_fields)

        self.stdout.write(
            self.style.SUCCESS(f"Seed complete. Added {created_books} new books.")
        )
