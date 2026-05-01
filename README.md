# Auto Test Case Generator (MVP)

A Django web app that converts BRD inputs (PDF + optional images) into structured CSV test cases, lets users review/edit, and generates Selenium or Playwright Python automation code.

## Features
- Upload PDF and optional screenshots
- Extract PDF text
- Generate CSV test cases
- Review/edit CSV in the UI
- Validate uploaded CSV
- Generate automation code (Selenium/Playwright)

## Local Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Apply migrations:
   - `python manage.py migrate`
4. Run the server:
   - `python manage.py runserver`

## Usage Flow
1. Confirm OpenAI integration on the home page.
2. Upload PDF and/or images.
3. Extract PDF text.
4. Generate CSV and edit as needed.
5. Validate CSV upload.
6. Generate code and download it.

## Deployment
See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for a simple Render deployment guide.

## Notes
- Demo deployments can use local storage; files may be wiped on server restarts.
- For production, use object storage for uploads.
