"""Shared discovery logic — transport-agnostic functions that work with any Appium driver."""
import logging
import time
from typing import List

from app.utils.accessibility_tree_parser import (
    MultiScreenSnapshot,
    ScreenCapture,
    parse_wda_xml,
)

logger = logging.getLogger(__name__)


def try_auto_login(driver) -> None:
    """Attempt auto-login if a login screen is detected and credentials are configured."""
    from app.core.config import settings
    from appium.webdriver.common.appiumby import AppiumBy

    email = settings.test_credentials_email
    password = settings.test_credentials_password
    if not email or not password:
        return

    email_ids = ["emailTextField", "email_field", "usernameField", "email", "Email"]
    password_ids = ["passwordTextField", "password_field", "passwordField", "password", "Password"]
    login_btn_ids = ["loginButton", "login_button", "signInButton", "Log in", "Sign in"]

    email_field = None
    for fid in email_ids:
        try:
            el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, fid)
            if el.is_displayed():
                email_field = el
                break
        except Exception:
            continue

    if not email_field:
        logger.debug("No login screen detected, skipping auto-login")
        return

    logger.info("Login screen detected, entering credentials...")
    email_field.clear()
    email_field.send_keys(email)

    for pid in password_ids:
        try:
            pwd_field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, pid)
            if pwd_field.is_displayed():
                pwd_field.clear()
                pwd_field.send_keys(password)
                break
        except Exception:
            continue

    for bid in login_btn_ids:
        try:
            btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, bid)
            if btn.is_displayed():
                btn.click()
                time.sleep(3)
                logger.info("Auto-login completed")
                return
        except Exception:
            continue

    logger.warning("Could not find login button after entering credentials")


def capture_screen(driver, label: str, nav_path: str = "", wait_for_stable: bool = True) -> ScreenCapture:
    """Capture current screen's accessibility tree.

    Polls page_source until element count stabilizes, then scrolls
    to reveal off-screen elements.
    """
    def get_page_source_safe(drv, retries=3):
        """Get page_source with retries — WDA can temporarily lose connection on BrowserStack."""
        for attempt in range(retries):
            try:
                return drv.page_source
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning("page_source failed (attempt %d/%d): %s", attempt + 1, retries, e)
                    time.sleep(3)
                else:
                    raise

    if wait_for_stable:
        prev_count = 0
        stable_checks = 0
        deadline = time.time() + 15

        while time.time() < deadline:
            xml = get_page_source_safe(driver)
            elements = parse_wda_xml(xml)
            interactive = [e for e in elements if e.is_interactive and e.has_useful_name]
            current_count = len(interactive)

            if current_count == prev_count and current_count > 0:
                stable_checks += 1
                if stable_checks >= 2:
                    break
            else:
                stable_checks = 0
                prev_count = current_count

            time.sleep(1.5)
    else:
        xml = get_page_source_safe(driver)
        elements = parse_wda_xml(xml)
        interactive = [e for e in elements if e.is_interactive and e.has_useful_name]

    # Scroll to reveal off-screen elements
    interactive = [e for e in elements if e.is_interactive and e.has_useful_name]
    should_scroll = len(interactive) < 200
    if should_scroll:
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            scrollable = driver.find_elements(AppiumBy.IOS_CLASS_CHAIN,
                "**/XCUIElementTypeScrollView")
            if scrollable:
                size = driver.get_window_size()
                start_y = int(size['height'] * 0.8)
                end_y = int(size['height'] * 0.3)
                mid_x = int(size['width'] * 0.5)
                driver.swipe(mid_x, start_y, mid_x, end_y, duration=500)
                time.sleep(1)

                xml2 = driver.page_source
                extra_elements = parse_wda_xml(xml2)
                existing_names = {(e.element_type, e.name) for e in elements if e.name}
                for e in extra_elements:
                    if e.name and (e.element_type, e.name) not in existing_names:
                        elements.append(e)
                        existing_names.add((e.element_type, e.name))

                driver.swipe(mid_x, end_y, mid_x, start_y, duration=500)
                time.sleep(0.5)
        except Exception:
            pass

    interactive = [e for e in elements if e.is_interactive and e.has_useful_name]

    try:
        screenshot_b64 = driver.get_screenshot_as_base64()
    except Exception:
        screenshot_b64 = ""

    logger.info(
        "  Screen '%s': %d elements, %d interactive",
        label, len(elements), len(interactive),
    )
    return ScreenCapture(
        screen_label=label,
        elements=elements,
        screenshot_b64=screenshot_b64,
        navigation_path=nav_path,
    )


KEYBOARD_NOISE = {
    "shift", "delete", "more", "space", "Return", "Next keyboard", "dictation",
    "Padding-Left", "Padding-Right", "Dictate", "numbers", "emoji",
}


def discover_screens(driver) -> List[ScreenCapture]:
    """Multi-screen discovery — captures home screen, tabs, and sub-screens.

    Works with any Appium driver (local or BrowserStack).
    """
    from appium.webdriver.common.appiumby import AppiumBy

    screens: List[ScreenCapture] = []

    def dismiss_keyboard(drv):
        """Try multiple methods to dismiss the keyboard."""
        try:
            drv.hide_keyboard()
            time.sleep(0.5)
            return
        except Exception:
            pass
        # Fallback: tap on a neutral area (top of screen)
        try:
            size = drv.get_window_size()
            drv.tap([(size['width'] // 2, 100)])
            time.sleep(0.5)
        except Exception:
            pass

    dismiss_keyboard(driver)

    # 1. Capture login/launch screen BEFORE auto-login
    screens.append(capture_screen(driver, "Login"))
    logger.info("Captured login/launch screen")

    # Auto-login if credentials configured
    try_auto_login(driver)

    # Wait for post-login screen to load (real devices need more time)
    time.sleep(5)

    # Dismiss keyboard after login
    dismiss_keyboard(driver)
    time.sleep(1)

    # 2. Capture home screen (post-login)
    screens.append(capture_screen(driver, "Home"))

    # 3. Discover tab bar buttons and navigate to each tab
    # Use the LAST captured screen (post-login home), not the first (login)
    home_elements = screens[-1].elements
    tab_names = []

    # Check for TabBar element type first (most reliable)
    for e in home_elements:
        if e.element_type == "XCUIElementTypeTabBar":
            # TabBar found — its children are the tab items
            logger.info("Found TabBar element, looking for tab items...")
            for child in home_elements:
                if (child.element_type in ("XCUIElementTypeButton", "XCUIElementTypeTab")
                    and child.has_useful_name
                    and child.name not in KEYBOARD_NOISE
                    and len(child.name) > 1
                    # Tab items are inside the tab bar's y range
                    and abs(child.y - e.y) < 100
                    and child.name not in tab_names
                ):
                    tab_names.append(child.name)
            break

    # Strategy B: Fallback to heuristic — buttons at bottom of screen
    if not tab_names:
        for e in home_elements:
            if (e.element_type == "XCUIElementTypeButton"
                and e.has_useful_name
                and e.y > 700
                and e.name not in tab_names
                and e.name not in KEYBOARD_NOISE
                and e.element_type != "XCUIElementTypeKey"
                and len(e.name) > 1
            ):
                tab_names.append(e.name)

    logger.info("Detected tab bar buttons: %s", tab_names)

    for tab_name in tab_names:
        try:
            tab_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, tab_name)
            tab_el.click()
            time.sleep(1.5)

            screen = capture_screen(
                driver,
                label=tab_name,
                nav_path=f"tap '{tab_name}'",
            )
            screens.append(screen)

            # 3. Try tapping expandable sections on each tab
            tappable = [
                e for e in screen.interactive_elements()
                if e.element_type == "XCUIElementTypeButton"
                and e.has_useful_name
                and e.y < 700
                and e.name not in tab_names
                and e.name not in KEYBOARD_NOISE
                and e.name not in ("Cancel", "Close", "Back", "Done",
                                   "See results", "Reset all", "icon  cross")
                and len(e.name) > 1
            ]

            for btn in tappable[:5]:
                try:
                    pre_click_names = {
                        e.name for e in parse_wda_xml(driver.page_source)
                        if e.is_interactive and e.has_useful_name
                    }

                    btn_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, btn.name)
                    btn_el.click()

                    deadline = time.time() + 8
                    sub_screen = None
                    while time.time() < deadline:
                        time.sleep(1)
                        candidate = capture_screen(
                            driver,
                            label=f"{tab_name} > {btn.name}",
                            nav_path=f"tap '{tab_name}', then tap '{btn.name}'",
                        )
                        current_names = {
                            e.name for e in candidate.interactive_elements()
                        }
                        new_names = current_names - pre_click_names
                        if new_names:
                            sub_screen = candidate
                            break

                    if sub_screen:
                        screens.append(sub_screen)
                        logger.info(
                            "  Sub-screen '%s > %s' revealed new elements",
                            tab_name, btn.name,
                        )

                    # Navigate back
                    try:
                        back = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "BackButton")
                        back.click()
                    except Exception:
                        try:
                            btn_el = driver.find_element(AppiumBy.ACCESSIBILITY_ID, btn.name)
                            btn_el.click()
                        except Exception:
                            pass
                    time.sleep(1)

                except Exception as e:
                    logger.debug("Could not explore sub-screen '%s': %s", btn.name, e)

        except Exception as e:
            logger.debug("Could not navigate to tab '%s': %s", tab_name, e)

    total_interactive = len(MultiScreenSnapshot(screens=screens).all_interactive_elements())
    logger.info(
        "Discovery complete: %d screens, %d unique interactive elements",
        len(screens), total_interactive,
    )

    return screens
