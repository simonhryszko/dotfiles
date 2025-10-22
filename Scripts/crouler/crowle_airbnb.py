import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.airbnb.com/rooms/1013515193789896780?adults=1&search_mode=regular_search&category_tag=Tag%3A8678&check_in=2025-11-14&check_out=2025-11-19&children=0&infants=0&pets=0&photo_id=1809136199&source_impression_id=p3_1761116881_P3poysljzhOlkjv8&previous_page_section_name=1000&federated_search_id=5add8475-2fa6-4474-a686-3caa9246c6b0")
    page.get_by_role("button", name="Close").click()
    page.get_by_role("button", name="Change dates; Check-in: 2025-").click()
    page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name="23, Sunday, November 2025.").click()
    page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name="Move forward to switch to the").click()
    page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name="12, Friday, December 2025.").click()
    page.get_by_text("฿13,952Show price breakdown ฿13,952 for 19 nightsfor 19 nights").nth(1).click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
