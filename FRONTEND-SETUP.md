# Testara Frontend Setup

**New React UI to replace Streamlit**

---

## 🎯 **What's New**

You now have **two UIs**:
1. **Landing Page** (`landing/`) — Marketing site at https://testara.dev
2. **Product UI** (`frontend/`) — **NEW** React interface for test generation

---

## 🚀 **Run the Product UI**

### **Step 1: Start Backend**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### **Step 2: Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Open:** http://localhost:8501

---

## ✨ **Features**

### **What Users See:**
1. **Screen Recording Upload** — Drag & drop video files
2. **Test Description** — Plain English input
3. **Generate Button** — Triggers API call
4. **Quality Score** — Grade (A-F), score (0-100), confidence, recommendations
5. **Generated Code** — Syntax-highlighted Swift with copy button

### **Design:**
- ✅ Matches landing page style (Apple-minimal, dark)
- ✅ Glass morphism effects
- ✅ Smooth animations (Framer Motion)
- ✅ Fully responsive
- ✅ Professional dev tool aesthetic

---

## 🔗 **Backend Integration**

Frontend connects to FastAPI backend via:
- **API Proxy:** Configured in `next.config.js`
- **Endpoint:** `POST /api/tests/generate`
- **Expected Backend:** `http://localhost:8000`

---

## 📦 **Tech Stack**

- **Next.js 14** — React framework
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **Framer Motion** — Animations
- **React Syntax Highlighter** — Code display
- **Axios** — HTTP requests

---

## 🐳 **Update Docker (Optional)**

To use React UI instead of Streamlit in Docker:

### **1. Create `Dockerfile.frontend`**
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./

RUN npm run build

EXPOSE 8501

CMD ["npm", "start"]
```

### **2. Update `docker-compose.yml`**
```yaml
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    depends_on:
      - backend
```

---

## 📊 **Comparison: Streamlit vs React**

| Feature | Streamlit (old) | React (new) |
|---------|----------------|-------------|
| Design | Basic | Professional |
| Animations | None | Smooth |
| Responsiveness | Limited | Full |
| Customization | Hard | Easy |
| Performance | Slow | Fast |
| User Experience | Demo-ish | Production-ready |

---

## 🔄 **Migration Path**

### **Phase 1: Test React UI** (Now)
- Run both UIs side-by-side
- Test with pilot users
- Gather feedback

### **Phase 2: Update Docker** (This week)
- Replace Streamlit with React in `docker-compose.yml`
- Update deployment docs

### **Phase 3: Remove Streamlit** (After pilot feedback)
- Delete `ui/app.py`
- Keep only React frontend

---

## 🎨 **Customization**

### **Change Colors:**
Edit `frontend/tailwind.config.ts`:
```typescript
colors: {
  'apple-blue': '#0071E3',  // Change brand color
}
```

### **Modify Layout:**
Edit `frontend/src/app/page.tsx`

### **Add Features:**
1. Create component in `frontend/src/components/`
2. Import in `page.tsx`

---

## 🚢 **Deploy**

### **Development:**
```bash
npm run dev
```

### **Production:**
```bash
npm run build
npm start
```

### **Vercel (Optional):**
```bash
cd frontend
vercel --prod
```

---

**The React UI is ready to replace Streamlit!** 🎉

Next step: Test it with your backend and compare to the old UI.
