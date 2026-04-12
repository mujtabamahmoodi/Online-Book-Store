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

## Language Support

- Switch language from the header dropdown (`English` / `فارسی`).
- Persian uses RTL layout automatically.
- Translation files are in `locale/fa/LC_MESSAGES/`.

## Free Deployment Recommendation

For this SQLite-based app, **PythonAnywhere free tier** is the best fit among common beginner platforms because it supports typical Django deployment via WSGI and simple static file mapping from the dashboard.

As of **April 12, 2026**, PythonAnywhere's free account is still available, with notable limits documented by PythonAnywhere (for example: 1 web app, restricted outbound internet access, and reduced resource quotas). Always re-check their latest pricing/features page before launch.

### PythonAnywhere Deploy Steps (Free)

1. Push this project to GitHub.
2. Create a free PythonAnywhere account.
3. Open a Bash console and clone your repo.
4. Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

5. Run migrations:

```bash
python manage.py migrate
```

6. In the Web tab, create a web app and configure the WSGI file to point to this project (follow the official guide linked above).
7. In the Web tab, map static files URL `/static/` to your project static directory and run:

```bash
python manage.py collectstatic
```

8. Set environment variables (`DJANGO_SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS=<your-pythonanywhere-domain>`), reload the app.

## Production Notes

- Set `DEBUG=0` in production.
- Use a strong `DJANGO_SECRET_KEY`.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` correctly.
- Run `python manage.py check --deploy` before going live.

## Useful Commands

```bash
python manage.py test
python manage.py makemigrations
python manage.py migrate
python manage.py seed_books
```
