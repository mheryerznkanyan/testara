# Settings & Device Configuration Guide

**Configure your simulator preferences for test execution** ⚙️

---

## 🎯 **What's New**

Multi-page SaaS interface with:
- ✅ **Settings page** for device configuration
- ✅ **Navigation bar** with tabs
- ✅ **Device selection** (iPhone models)
- ✅ **iOS version selection**
- ✅ **Persistent settings** (localStorage)
- ✅ **Visual settings indicator**

---

## 🚀 **How to Use**

### **1. Access Settings**

**Option A:** Click **Settings** in navigation bar  
**Option B:** Click **Configure** link on main page

### **2. Choose Your Device**

Select from available iPhone simulators:
- iPhone 15 Pro Max
- iPhone 15 Pro
- iPhone 15
- iPhone 14 Pro
- iPhone 14
- iPhone 13
- iPhone SE (3rd generation)

**Your selection:** iPhone 17 Pro (if available on your machine)

### **3. Select iOS Version**

Available versions:
- iOS 17.2
- iOS 17.1
- iOS 17.0
- iOS 16.4
- iOS 16.0
- iOS 15.0

### **4. Set App Name**

Enter the name of your app (used in test context).  
Default: `YourApp`

### **5. Save Settings**

Click **Save Settings** button.  
Settings persist across sessions.

---

## 📱 **Finding Your Simulators**

To see which simulators are installed:

```bash
xcrun simctl list devices available
```

**Output example:**
```
-- iOS 17.0 --
    iPhone 15 Pro (ABC-123-...)
    iPhone 15 (DEF-456-...)
-- iOS 17.2 --
    iPhone 17 Pro (GHI-789-...)
```

---

## 💾 **Settings Storage**

Settings are stored in **browser localStorage**:
- Persist across page refreshes
- Separate for each browser
- Not synced across devices

**Storage key:** `testara_settings`

**Format:**
```json
{
  "device": "iPhone 15 Pro",
  "iosVersion": "17.0",
  "appName": "YourApp"
}
```

---

## 🎨 **UI Overview**

### **Navigation Bar**
```
┌────────────────────────────────────────┐
│ ⚡ Testara  [Generate] [Settings] About│
└────────────────────────────────────────┘
```

### **Settings Indicator (Main Page)**
```
┌────────────────────────────────────────┐
│ 📱 iPhone 15 Pro • iOS 17.0  Configure│
└────────────────────────────────────────┘
```

### **Settings Page**
```
Settings
Configure simulator and test execution preferences

┌─────────────────────────┐
│ Simulator Device        │
│ [iPhone 15 Pro ▼]      │
└─────────────────────────┘

┌─────────────────────────┐
│ iOS Version             │
│ [iOS 17.0 ▼]           │
└─────────────────────────┘

┌─────────────────────────┐
│ App Name                │
│ [YourApp]              │
└─────────────────────────┘

[Save Settings]
```

---

## 🔄 **How Settings Are Applied**

**Test Generation:**
1. User enters test description
2. Clicks "Generate Test"
3. Backend generates test code
4. ✅ Settings NOT used here (only description)

**Test Execution:**
1. User clicks "Run in Simulator"
2. Frontend reads settings from localStorage
3. Sends to backend:
   ```json
   {
     "test_code": "...",
     "app_name": "YourApp",
     "device": "iPhone 15 Pro",
     "ios_version": "17.0"
   }
   ```
4. Backend uses these values to:
   - Find matching simulator
   - Boot the device
   - Run test
   - Record video

---

## 🐛 **Troubleshooting**

### **Issue: Device not found**

**Error message:**
```
Simulator 'iPhone 17 Pro (17.0)' not found
```

**Solution:**
1. Run: `xcrun simctl list devices available`
2. Find your actual device name
3. Go to Settings → Select exact name from list
4. Save and try again

### **Issue: Settings not saving**

**Check:**
- Browser localStorage is enabled
- Not in private/incognito mode
- Click "Save Settings" button
- Look for "✓ Saved!" confirmation

### **Issue: Settings not applying**

**Verify:**
1. Go to Settings page
2. Confirm values are saved
3. Return to Generate page
4. Check settings indicator (top of page)
5. Should show your configured device

---

## 📋 **Default Settings**

If no settings are saved, defaults are:
- **Device:** iPhone 15 Pro
- **iOS Version:** 17.0
- **App Name:** YourApp

---

## 🔧 **For Your iPhone 17 Pro**

Since you have iPhone 17 Pro:

**Step-by-step:**
1. Open Terminal
2. Run: `xcrun simctl list devices available`
3. Find line with "iPhone 17 Pro" and note iOS version
4. Go to Testara → Settings
5. If "iPhone 17 Pro" not in dropdown:
   - We need to add it to the list
   - For now, use closest match (iPhone 15 Pro Max)
6. Select iOS version that matches
7. Save settings

**To add iPhone 17 Pro to dropdown:**
Edit `frontend/src/app/settings/page.tsx`:
```typescript
const AVAILABLE_DEVICES = [
  'iPhone 17 Pro',  // Add this line
  'iPhone 15 Pro Max',
  // ...
]
```

---

## 🎯 **Pro Tips**

1. **Match your simulator exactly**  
   Use `xcrun simctl list` to get exact name

2. **Test with multiple devices**  
   Change settings → Run test → See different results

3. **Keep app name consistent**  
   Use actual app bundle name for best results

4. **Check settings before running**  
   Visual indicator shows current config

---

## 🚀 **What's Next**

**Future improvements:**
- Auto-detect available simulators
- Device dropdown populated from `xcrun simctl list`
- Support for custom simulator UDIDs
- Multiple device configurations (profiles)
- Remote device testing

---

**Your settings are ready!** Configure your iPhone 17 Pro and start testing. 🎉
