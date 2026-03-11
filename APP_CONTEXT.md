# App Context for Test Generation

**This file is auto-generated when you index your iOS app.**

```bash
docker-compose exec backend python -m rag.cli ingest \
  --app-dir /app/ios-app \
  --persist /app/rag_store
```

The indexing process extracts:
- Screen names
- Navigation patterns  
- Accessibility IDs
- UI elements

---

## Manual Template (if auto-generation doesn't work)

**App Name:** YourApp  
**Type:** [e.g., E-commerce, Social Media, Finance, etc.]  
**Platform:** iOS

---

### Overview

Brief description of what the app does (2-3 sentences).

Example:
- A shopping app where users browse items, add to cart, and checkout
- Users must login to access most features
- Items are organized by categories and have search functionality

---

### Main Features

1. **Authentication**
   - Login with email/password
   - Logout from profile screen
   - **Test Credentials:** test@example.com / password123
   
2. **Item Browsing**
   - List of items on main screen
   - Each item shows: title, price, category, image
   - Items can be filtered by category
   - Search functionality
   
3. **Item Details**
   - Tap item to see full details
   - Can add to favorites
   - View related items
   
4. **Profile**
   - User info display
   - Settings
   - Logout button

---

### User Flows

#### Login Flow
1. Launch app → Login screen
2. Enter email + password
3. Tap login → Items list appears

#### Browse Items Flow
1. After login → Items list screen (default)
2. Scroll through items
3. Tap item → Details screen
4. Back button returns to list

#### Tab Navigation
- **Items tab** (default after login)
- **Profile tab**
- **Settings tab** (if applicable)

---

### Common Test Scenarios

- **Happy path:** Login → Browse items → View details → Logout
- **Error:** Login with invalid credentials → Error message shown
- **Navigation:** Switch between tabs
- **Search:** Enter search term → Filtered results
- **Data validation:** Empty fields → Validation errors

---

### Navigation Patterns

- **Pattern:** TabView, NavigationStack, or custom
- **Entry Screen:** Name of first screen after launch
- **Post-Login Screen:** Name of screen after successful login

---

### Known Accessibility IDs

List important accessibility identifiers from your code:

- `loginButton`
- `emailTextField`
- `passwordTextField`
- `itemCell_0`, `itemCell_1`, etc.
- `profileTab`
- (Add more from your code)

---

### Technical Notes

- **Default Credentials:** test@example.com / password123
- **Data Generation:** Items may be randomly generated
- **Network:** Some tests may require network/mock data
- **State:** App may need fresh install for consistent tests

---

## How to Keep This Updated

1. **Re-index after code changes** (auto-updates this file):
   ```bash
   docker-compose exec backend python -m rag.cli ingest \
     --app-dir /app/ios-app \
     --persist /app/rag_store
   ```

2. **Edit manually** to add:
   - Test credentials
   - Expected behaviors
   - Business logic notes
   - Known data patterns

3. **Restart backend** to reload context:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

---

**This file powers the enrichment service to generate better test descriptions!**
