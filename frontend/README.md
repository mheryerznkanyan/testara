# Testara Frontend

Modern React UI for Testara iOS test generation.

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:8501

## 🔧 Backend Connection

The frontend expects the FastAPI backend running on `http://localhost:8000`.

Start the backend first:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## ✨ Features

- **Screen Recording Upload** — Drag & drop video files
- **Test Description Input** — Plain English test descriptions
- **Real-time Generation** — API integration with backend
- **Quality Scoring** — Visual quality report display
- **Syntax Highlighting** — Swift code with proper formatting
- **Copy to Clipboard** — One-click code copy

## 🎨 Design

Matches the landing page design:
- Apple-inspired minimal style
- Dark theme (black background)
- Glass morphism effects
- Smooth Framer Motion animations
- Fully responsive

## 📦 Tech Stack

- **Next.js 14** — React framework
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **Framer Motion** — Animations
- **React Syntax Highlighter** — Code display

## 🔗 API Endpoints

- `POST /api/tests/generate` — Generate test from screen recording + description

## 📱 Port

Runs on port **8501** (same as old Streamlit UI for easy replacement).

## 🚢 Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm start
```

### Docker
Update `docker-compose.yml` to use this frontend instead of Streamlit.

---

**This replaces the Streamlit UI (`ui/app.py`) with a professional React interface.**
