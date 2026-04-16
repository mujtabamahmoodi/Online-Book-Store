# Online Book Store (Django + SQLite)

A complete online bookstore built with:
- Django 6
- SQLite
- HTML, CSS, JavaScript

## Features

- Book catalog with search and category filtering
- Book detail page
- Session-based cart (add, update, remove)
- User authentication (signup/login/logout)
- Checkout flow and order creation
- Order history per user
- Bilingual interface: English and Persian (with RTL layout support)
- Django admin for categories, books, and orders
- Sample seed data command

## Documentation Researched (Internet)

These sources were used to design and structure this project:

- Django official tutorial: https://docs.djangoproject.com/en/6.0/intro/tutorial01/
- Django auth docs: https://docs.djangoproject.com/en/6.0/topics/auth/default/
- Django sessions docs: https://docs.djangoproject.com/en/6.0/topics/http/sessions/
- Django static files docs: https://docs.djangoproject.com/en/6.0/howto/static-files/
- Django deployment checklist: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/
- MDN Local Library tutorial (book-catalog architecture): https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Tutorial_local_library_website
- PythonAnywhere Django deployment guide: https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
- PythonAnywhere pricing/free tier page: https://www.pythonanywhere.com/pricing/

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Seed sample books:

```bash
python manage.py seed_books
```

5. Create admin user (optional):

```bash
python manage.py createsuperuser
```

6. Run server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Add Images in Local Storage

Use this project path for book cover images:

- `media/book_covers/`

Ways to add your own images:

1. Admin Dashboard upload (recommended):
- Open `http://127.0.0.1:8000/` and go to the Admin Dashboard as a staff user.
- In **Add New Book**, use **Cover Upload** and leave **Cover URL** empty.
- Django stores the uploaded file in `media/book_covers/`.

2. Manual file copy:
- Copy image files into `media/book_covers/` (example: `dune.jpg`).
- Link the image to a book from Django shell:

```bash
python manage.py shell -c "from bookstore.models import Book; b=Book.objects.get(slug='dune'); b.cover_image='book_covers/dune.jpg'; b.save(update_fields=['cover_image'])"
```

Notes:
- Local media is served from `/media/` while `DEBUG=True`.
- Files inside `media/book_covers/` can be committed to Git and deployed with the project.

## Language Support

- Switch language from the header dropdown (`English` / `فارسی`).
- Persian uses RTL layout automatically.
- Translation files are in `locale/fa/LC_MESSAGES/`.

## Free Deployment Recommendation

For this SQLite-based app, **PythonAnywhere free tier** is the best fit among common beginner platforms because it supports typical Django deployment via WSGI and simple static file mapping from the dashboard.

As of **April 12, 2026**, PythonAnywhere's free account is still available, with notable limits documented by PythonAnywhere (for example: 1 web app, restricted outbound internet access, and reduced resource quotas). Always re-check their latest pricing/features page before launch.

### PythonAnywhere Deploy Steps (Free)

This repo is now prepared for PythonAnywhere deployment:
- production-safe static files are supported with WhiteNoise
- `seed_books` assigns the repo's local cover files for books that have them
- `media/book_covers/` can be pushed to GitHub and served from PythonAnywhere

1. Push this project to GitHub.
2. Create a free PythonAnywhere account.
3. In PythonAnywhere, open a **Bash** console and clone your repo with HTTPS:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
```

4. Create a virtual environment and install dependencies:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Seed sample books and create an admin account:

```bash
python manage.py seed_books
python manage.py createsuperuser
```

7. Collect static files:

```bash
python manage.py collectstatic
```

8. In the **Web** tab, create a new **Manual configuration** web app using the same Python version as your virtualenv.
9. Set the virtualenv path in the Web tab to:

```bash
/home/YOUR-USERNAME/YOUR-REPO/.venv
```

10. Edit the WSGI file so it points to your project:

```python
import os
import sys

path = '/home/YOUR-USERNAME/YOUR-REPO'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_SECRET_KEY'] = 'REPLACE-WITH-A-LONG-RANDOM-SECRET'
os.environ['DEBUG'] = '0'
os.environ['USE_HTTPS'] = '1'
os.environ['ALLOWED_HOSTS'] = 'YOUR-USERNAME.pythonanywhere.com'
os.environ['CSRF_TRUSTED_ORIGINS'] = 'https://YOUR-USERNAME.pythonanywhere.com'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

11. In the **Static files** section of the Web tab, add these mappings:

- URL: `/static/` -> Directory: `/home/YOUR-USERNAME/YOUR-REPO/staticfiles`
- URL: `/media/` -> Directory: `/home/YOUR-USERNAME/YOUR-REPO/media`

12. Reload the web app from the Web tab.
13. Open `https://YOUR-USERNAME.pythonanywhere.com/`.

## Production Notes

- Set `DEBUG=0` in production.
- Use a strong `DJANGO_SECRET_KEY`.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` correctly.
- Set `USE_HTTPS=1` on PythonAnywhere so secure cookies and HTTPS redirect work.
- Run `python manage.py seed_books` after deployment because `db.sqlite3` is not stored in Git.
- Run `python manage.py check --deploy` before going live.

## Useful Commands

```bash
python manage.py test
python manage.py makemigrations
python manage.py migrate
python manage.py seed_books
python manage.py localize_book_covers
```
