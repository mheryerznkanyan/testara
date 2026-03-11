# Test Execution with Video Recording

**New feature: Run tests in iOS Simulator and record video** 🎬

---

## 🎯 **What's New**

You can now:
1. ✅ Generate test code (existing)
2. ✅ **Run test in iOS Simulator** (NEW)
3. ✅ **Record video of execution** (NEW)
4. ✅ **View results with video playback** (NEW)

---

## 🚀 **How to Use**

### **1. Generate Test**
- Enter test description
- Click "Generate Test"
- View generated Swift code

### **2. Run in Simulator**
- Click "Run in Simulator" button
- Wait for execution (takes ~10-15 seconds)
- Test runs in iPhone 15 Pro simulator

### **3. View Results**
- **Pass/Fail status** — Visual indicator
- **Video playback** — Watch the test run
- **Execution details** — Device, iOS version, duration
- **Logs** — Test output
- **Run Again** — Re-execute the test

---

## 🔧 **Requirements**

### **macOS Only**
This feature requires macOS with Xcode installed:
- Xcode 15+
- iOS Simulator
- `xcrun` command-line tools

### **Check Setup**
```bash
# Verify Xcode is installed
xcode-select -p

# List available simulators
xcrun simctl list devices
```

---

## 📹 **Video Recording**

### **How it Works:**
1. Backend boots iPhone 15 Pro simulator
2. Starts video recording via `xcrun simctl io recordVideo`
3. Runs test (currently simulated, needs actual Xcode project)
4. Stops recording
5. Returns video URL to frontend

### **Video Storage:**
- Location: `backend/recordings/`
- Format: MP4
- Naming: `{test_id}.mp4` (UUID)
- Served at: `http://localhost:8000/recordings/{test_id}.mp4`

---

## ⚙️ **Configuration**

### **Default Settings:**
- **Device:** iPhone 15 Pro
- **iOS Version:** 17.0
- **App Name:** YourApp (placeholder)

### **Change Device:**
Edit `frontend/src/app/page.tsx`:
```typescript
body: JSON.stringify({
  test_code: result.swift_code,
  app_name: 'YourApp',
  device: 'iPhone 14',  // Change device
  ios_version: '16.0',   // Change iOS version
})
```

---

## 🏗️ **Current Limitations**

### **1. Simulated Execution**
- Test doesn't actually run yet
- Needs real Xcode project with app
- Currently just boots simulator and records for 5 seconds

### **2. For Production:**
You need to:
1. Have an Xcode project for your app
2. Inject generated test code into test target
3. Run `xcodebuild test -scheme YourApp -destination ...`

### **Implementation Note:**
See `backend/app/services/test_runner.py` → `_execute_test()`:
```python
# TODO: Replace simulation with actual xcodebuild execution
# await asyncio.create_subprocess_exec(
#     'xcodebuild', 'test',
#     '-scheme', app_name,
#     '-destination', f'platform=iOS Simulator,id={device_id}',
#     ...
# )
```

---

## 🎨 **Frontend UI**

### **Button States:**
- **Before execution:** Green "Run in Simulator" button
- **During execution:** Loading spinner + "Running in Simulator..."
- **After execution:** Results card with video

### **Results Display:**
```
┌────────────────────────────────┐
│ Test Execution         ✓ Passed│
├────────────────────────────────┤
│ [Video Player]                 │
├────────────────────────────────┤
│ Device: iPhone 15 Pro          │
│ iOS: 17.0                      │
│ Duration: 5.23s                │
│ Test ID: abc-123...            │
├────────────────────────────────┤
│ Logs:                          │
│ Test executed successfully...  │
├────────────────────────────────┤
│ [Run Again]                    │
└────────────────────────────────┘
```

---

## 🐛 **Troubleshooting**

### **Error: Simulator not found**
```bash
# List available simulators
xcrun simctl list devices

# Boot simulator manually
xcrun simctl boot "iPhone 15 Pro"
```

### **Error: Recording failed**
- Ensure Xcode is installed
- Check simulator is bootable
- Verify disk space for recordings

### **Error: Backend not starting**
- Check `backend/recordings/` directory exists
- Verify Python dependencies installed

---

## 📦 **API Endpoints**

### **POST /run-test**
**Request:**
```json
{
  "test_code": "import XCTest...",
  "app_name": "YourApp",
  "device": "iPhone 15 Pro",
  "ios_version": "17.0"
}
```

**Response:**
```json
{
  "success": true,
  "test_id": "abc-123-...",
  "video_url": "/recordings/abc-123.mp4",
  "logs": "Test executed successfully",
  "duration": 5.23,
  "device": "iPhone 15 Pro",
  "ios_version": "17.0"
}
```

### **GET /recordings/{video_file}**
Returns video file (MP4)

---

## 🔄 **Next Steps**

### **To Make This Production-Ready:**

1. **Integrate with Real Xcode Project:**
   - Create Xcode project template
   - Auto-generate test target
   - Inject test code dynamically

2. **Support Multiple Apps:**
   - User uploads .app file
   - Install app in simulator
   - Run tests against it

3. **Advanced Features:**
   - Multiple device testing
   - Parallel test execution
   - Test result caching
   - Screenshot comparison

---

## 🎬 **Demo Flow**

1. **User enters:** "Test login with invalid password"
2. **Generate:** Swift XCUITest code created
3. **Run:** Click "Run in Simulator"
4. **Watch:** Video shows simulator booting and test running
5. **Results:** Pass/Fail + video playback

---

**The execution infrastructure is ready!**

Now needs actual app integration for real test runs.
