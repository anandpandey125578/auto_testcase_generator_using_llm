# Render Deployment Guide (Django)

## 1) Prerequisites
- Push this repo to GitHub.
- Create a free Render account.

## 2) Create Render Web Service
1. Go to https://render.com and click New > Web Service.
2. Connect your GitHub repo.
3. Choose the branch to deploy.

## 3) Build and Start Commands
- Build command:
  - `pip install -r requirements.txt`
  - `python manage.py migrate`
  - `python manage.py collectstatic --noinput`
- Start command:
  - `gunicorn autotestgen.wsgi:application`

## 4) Environment Variables
Set these in Render:
- `DJANGO_SECRET_KEY`: A random secret key
- `DJANGO_DEBUG`: `false`
- `DJANGO_ALLOWED_HOSTS`: `<your-render-url>`
- `DJANGO_CSRF_TRUSTED_ORIGINS`: `https://<your-render-url>`
- `OPENAI_MODEL`: `gpt-4o-mini` (or `gpt-4o`)

## 5) Notes
- Free tier instances sleep; uploads are stored on local disk and may be wiped.
- For production, move uploads to S3 or R2.

## 6) Test the App
- Open the Render URL and run the full flow:
  1) Confirm integration
  2) Upload PDF/images
  3) Extract text
  4) Generate CSV
  5) Validate CSV upload
  6) Generate code
