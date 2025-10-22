import csv
import re
import time
from playwright.sync_api import Playwright, sync_playwright, expect
from urllib.parse import urlparse, parse_qs

def extract_room_id(url):
    """Extract room ID from Airbnb URL"""
    # Match pattern after /rooms/ and before ?
    match = re.search(r'/rooms/(\d+)', url)
    if match:
        return match.group(1)
    return None

def extract_check_in_out_dates(url):
    """Extract check-in and check-out dates from URL"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    check_in = params.get('check_in', [None])[0]
    check_out = params.get('check_out', [None])[0]
    return check_in, check_out

def clean_url(url):
    """Remove extra parameters from URL to get clean Airbnb listing URL"""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return base_url

def reconstruct_url(room_id, check_in=None, check_out=None):
    """Reconstruct Airbnb URL with room ID and optional dates"""
    base_url = f"https://www.airbnb.com/rooms/{room_id}"
    params = []

    if check_in:
        params.append(f"check_in={check_in}")
    if check_out:
        params.append(f"check_out={check_out}")

    # Add basic parameters
    params.extend(["adults=1", "search_mode=regular_search", "children=0", "infants=0", "pets=0"])

    if params:
        query_string = "&".join(params)
        return f"{base_url}?{query_string}"

    return base_url

def format_date_for_selection(date_str):
    """Convert YYYY-MM-DD to format for calendar selection"""
    if not date_str:
        return None

    try:
        year, month, day = date_str.split('-')
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

        month_name = months[int(month) - 1]
        day_num = int(day.lstrip('0'))

        return f"{day_num}, {month_name}, {year}."
    except:
        return None

def scrape_airbnb_price(url, check_in_date, check_out_date):
    """Scrape price from a single Airbnb URL"""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"Opening URL: {url}")
            page.goto(url)

            # Wait for page to load
            page.wait_for_load_state('networkidle')

            # Close any popups
            try:
                close_button = page.get_by_role("button", name="Close").first
                if close_button.is_visible(timeout=5000):
                    close_button.click()
            except:
                pass

            # If dates are provided, try to set them
            if check_in_date and check_out_date:
                try:
                    # Click on date change button
                    date_button = page.get_by_role("button", name="Change dates")
                    if date_button.is_visible(timeout=10000):
                        date_button.click()
                        time.sleep(2)

                        # Format dates for selection
                        check_in_formatted = format_date_for_selection(check_in_date)
                        check_out_formatted = format_date_for_selection(check_out_date)

                        if check_in_formatted and check_out_formatted:
                            # Select check-in date
                            try:
                                page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name=check_in_formatted).click()
                            except:
                                print(f"Could not find check-in date: {check_in_formatted}")

                            # Select check-out date
                            try:
                                page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name=check_out_formatted).click()
                            except:
                                print(f"Could not find check-out date: {check_out_formatted}")

                        time.sleep(2)
                except Exception as e:
                    print(f"Error setting dates: {e}")

            # Wait for price to load
            time.sleep(3)

            # Try to extract price using multiple methods
            price = None

            # Method 1: Look for price breakdown text
            try:
                price_elements = page.locator("[data-testid*='price']").all()
                for element in price_elements:
                    text = element.text_content()
                    if text and ('฿' in text or 'zł' in text or '$' in text):
                        price = text
                        break
            except:
                pass

            # Method 2: Look for price in booking sidebar
            if not price:
                try:
                    price_text = page.get_by_test_id("bookit-sidebar").text_content()
                    # Extract price using regex
                    price_match = re.search(r'[฿$zł]\s*[\d,]+', price_text)
                    if price_match:
                        price = price_match.group()
                except:
                    pass

            # Method 3: General text search for price patterns
            if not price:
                try:
                    page_text = page.text_content("body")
                    # Look for patterns like "฿13,952 for 19 nights" or "278 zł"
                    price_patterns = [
                        r'[฿$zł]\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
                        r'[฿$zł]\s*\d+(?:\.\d{2})?'
                    ]

                    for pattern in price_patterns:
                        matches = re.findall(pattern, page_text)
                        if matches:
                            # Take the first match that looks like a main price
                            for match in matches:
                                if len(match.replace(',', '').replace('฿', '').replace('$', '').replace('zł', '').replace(' ', '')) > 2:
                                    price = match
                                    break
                            if price:
                                break
                except:
                    pass

            print(f"Price found: {price if price else 'Price not found'}")
            return price

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            page.close()
            context.close()
            browser.close()

def main():
    """Main function to read CSV and process URLs"""
    csv_file = 'airbnb.csv'
    check_in = '2025-11-12'  # Hardcoded check-in date
    check_out = '2025-11-17'  # Hardcoded check-out date

    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Skip header row

            print("Starting Airbnb price scraping...")
            print(f"Using hardcoded dates: {check_in} to {check_out}")
            print("=" * 50)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                if len(row) > 0:  # Make sure row has data
                    original_url = row[0]  # URL is in the first column

                    if not original_url or not original_url.startswith('https://www.airbnb.com'):
                        print(f"Skipping invalid URL in row {row_num}: {original_url}")
                        continue

                    print(f"\nProcessing row {row_num}:")
                    print(f"Original URL: {original_url}")

                    # Extract room ID from URL
                    room_id = extract_room_id(original_url)
                    if not room_id:
                        print(f"Could not extract room ID from URL: {original_url}")
                        continue

                    print(f"Room ID: {room_id}")
                    print(f"Using hardcoded dates: {check_in}, {check_out}")

                    # Create clean URL for navigation
                    clean_url_to_use = clean_url(original_url)
                    print(f"Clean URL: {clean_url_to_use}")

                    # Reconstruct URL with room ID and hardcoded dates
                    reconstructed_url = reconstruct_url(room_id, check_in, check_out)
                    print(f"Reconstructed URL: {reconstructed_url}")

                    # Use reconstructed URL for scraping
                    url_to_scrape = reconstructed_url

                    # Scrape price
                    price = scrape_airbnb_price(url_to_scrape, check_in, check_out)

                    print(f"Final price: {price}")
                    print("-" * 30)

                    # Wait a bit between requests to be respectful
                    time.sleep(2)

    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

if __name__ == "__main__":
    main()