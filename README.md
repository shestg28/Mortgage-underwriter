# Speckit — Resume Comparison Dashboard (Minimal)

This project is a minimal implementation of the requested Resume Comparison Dashboard.

Features:
- User registration and login (in-memory, no database)
- Upload a PDF resume
- Enter College, Degree, Skills
- Backend extracts text from PDF (no OCR) using `pdf-parse`
- Compares resume text with entered values and returns match percentage, matching/missing skills, and education/degree matches

Tech stack:
- Node.js + Express
- React (via CDN) for a simple frontend
- Tailwind CSS (CDN)

Run locally:

1. Install dependencies

```bash
npm install
```

2. Start server

```bash
npm start
```

3. Open http://localhost:3000 in a browser

Notes & limits:
- Users and sessions are stored in memory; restarting the server clears them.
- PDF text extraction uses `pdf-parse` and relies on embedded text inside PDFs (no OCR).
- File uploads are limited to 10 MB and validated to be PDFs.
- This implementation is intentionally simple and meant as a starting point. For production use add secure password hashing, persistent storage, CSRF protection, and proper input sanitization.
# Speckit — Simple PDF Uploader (Frontend-only)

This is a minimal, single-page frontend demo implementing the Speckit guidelines: simple, clean, responsive UI with input validation and error handling.

Files:
- [index.html](index.html) — main page
- [styles.css](styles.css) — styles
- [app.js](app.js) — JavaScript logic

How to run:
1. Open `index.html` in a modern browser (double-click or serve via a static server).

Notes:
- This is frontend-only. There is no backend or persistence besides `localStorage` for the demo login state.
- Mock credentials: username `user@example.com`, password `password123`.
- PDF validation checks the file MIME type or `.pdf` extension and limits files to 10 MB.
- Error messages are shown inline; invalid inputs are handled gracefully.

Next steps you might ask for:
- Add a backend endpoint to accept uploads.
- Replace mock auth with a secure login system.
- Add unit tests or E2E tests.
