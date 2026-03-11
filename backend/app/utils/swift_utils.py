"""Swift code utility functions"""


def strip_code_fences(swift_code: str) -> str:
    """Remove markdown code fences from generated code"""
    s = swift_code.strip()
    if s.startswith("```swift"):
        s = s[len("```swift"):].strip()
    if s.startswith("```"):
        s = s[len("```"):].strip()
    if s.endswith("```"):
        s = s[:-3].strip()
    return s


def extract_class_name(swift_code: str, fallback: str) -> str:
    """Extract the test class name from generated Swift code"""
    # Handles "final class X: XCTestCase" and "class X: XCTestCase"
    for line in swift_code.splitlines():
        if "class " in line and ": XCTestCase" in line:
            try:
                after = line.split("class ", 1)[1]
                name = after.split(":", 1)[0].strip()
                if name:
                    return name
            except Exception:
                pass
    return fallback
