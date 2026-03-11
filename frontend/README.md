# Testara Frontend

Modern React UI for Testara iOS test generation.

---

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:3000**

---

## 🔧 Prerequisites

**Backend must be running first:**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend connects to backend at `http://localhost:8000`

---

## ✨ Features

- **Test Description Input** — Natural language test descriptions
- **Real-time Generation** — Live API integration
- **Syntax Highlighting** — Formatted Swift code display
- **Copy to Clipboard** — One-click code copy
- **Execution Status** — Test run results and logs
- **Video Playback** — View recorded test executions

---

## 🎨 Design

- Apple-inspired minimal interface
- Dark theme with glass morphism
- Smooth Framer Motion animations
- Fully responsive layout
- Professional developer tool aesthetic

---

## 📦 Tech Stack

- **Next.js 14** — React framework (App Router)
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **Framer Motion** — Animations
- **React Syntax Highlighter** — Code formatting

---

## 🔌 API Integration

**Backend endpoint:**
```
POST http://localhost:8000/generate-test-with-rag
```

**Request:**
```json
{
  "description": "Test login with valid credentials"
}
```

**Response:**
```json
{
  "swift_code": "...",
  "test_type": "ui",
  "class_name": "LoginTests"
}
```

---

## 🚢 Deployment

### Development

```bash
npm run dev
```

Runs on: http://localhost:3000

### Production

```bash
npm run build
npm start
```

### Docker

Frontend is included in `docker-compose.yml`:

```bash
docker-compose up frontend
```

---

## 📝 Configuration

**Backend URL** is configured in `next.config.js`:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://backend:8000/:path*'
    }
  ]
}
```

Change `backend:8000` to your backend URL if needed.

---

## 🛠️ Development

### Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Main test generation page
│   │   ├── layout.tsx        # Root layout
│   │   ├── globals.css       # Global styles
│   │   └── settings/         # Settings page
│   ├── components/           # React components
│   └── lib/                  # Utilities
├── public/                   # Static assets
├── package.json
└── next.config.js            # Next.js config
```

### Adding Features

1. Create component in `src/components/`
2. Import in `src/app/page.tsx`
3. Style with Tailwind classes
4. Add animations with Framer Motion

---

Made with ⚡ by Testara
