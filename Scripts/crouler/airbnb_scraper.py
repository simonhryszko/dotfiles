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

def scrape_airbnb_price(url, check_in_date, check_out_date, max_retries=3):
    """Scrape price from a single Airbnb URL with retry logic"""
    for attempt in range(max_retries):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                print(f"🚀 Attempt {attempt + 1}/{max_retries}: Opening URL: {url}")

                # Monitor network activity
                print("📡 Monitoring network requests...")
                request_count = 0

                def handle_request(request):
                    nonlocal request_count
                    request_count += 1
                    if request_count <= 5:  # Show first few requests
                        print(f"   📤 Request {request_count}: {request.url}")

                def handle_response(response):
                    if request_count <= 5:  # Show first few responses
                        print(f"   📥 Response: {response.status} - {response.url}")

                page.on("request", handle_request)
                page.on("response", handle_response)

                # Navigate with longer timeout
                print(f"⏳ Loading page (timeout: 30s)...")
                start_time = time.time()
                page.goto(url, timeout=30000, wait_until='domcontentloaded')

                # Wait for network to be calm with progressive timeout
                print("🌐 Waiting for network activity to settle...")
                for i in range(10):  # Check network status every 2 seconds for 20 seconds total
                    try:
                        page.wait_for_load_state('networkidle', timeout=2000)
                        elapsed = time.time() - start_time
                        print(f"✅ Network settled after {elapsed:.1f}s")
                        break
                    except:
                        elapsed = time.time() - start_time
                        print(f"   ⏱️  Still loading... {elapsed:.1f}s elapsed")
                        if i == 9:  # Last attempt
                            print("⚠️  Network didn't fully settle, proceeding anyway...")
                            break

                # Close any popups
                try:
                    close_button = page.get_by_role("button", name="Close").first
                    if close_button.is_visible(timeout=5000):
                        close_button.click()
                        print("✅ Closed popup")
                except:
                    print("ℹ️  No popup found")

                # If dates are provided, try to set them
                if check_in_date and check_out_date:
                    try:
                        print(f"📅 Setting dates: {check_in_date} to {check_out_date}")
                        # Click on date change button
                        date_button = page.get_by_role("button", name="Change dates")
                        if date_button.is_visible(timeout=10000):
                            date_button.click()
                            print("⏳ Waiting for calendar to load...")
                            time.sleep(3)

                            # Format dates for selection
                            check_in_formatted = format_date_for_selection(check_in_date)
                            check_out_formatted = format_date_for_selection(check_out_date)

                            if check_in_formatted and check_out_formatted:
                                # Select check-in date
                                try:
                                    page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name=check_in_formatted).click()
                                    print(f"✅ Selected check-in: {check_in_formatted}")
                                except:
                                    print(f"⚠️  Could not find check-in date: {check_in_formatted}")

                                # Select check-out date
                                try:
                                    page.get_by_test_id("bookit-sidebar-availability-calendar").get_by_role("button", name=check_out_formatted).click()
                                    print(f"✅ Selected check-out: {check_out_formatted}")
                                except:
                                    print(f"⚠️  Could not find check-out date: {check_out_formatted}")

                            time.sleep(3)
                    except Exception as e:
                        print(f"⚠️  Error setting dates: {e}")

                # Check if room is available first
                print("🔍 Checking room availability...")
                is_available = check_availability(page)

                if not is_available:
                    print("🚫 Room not available - returning 'Not Available'")
                    return "Not Available"

                # Multiple attempts to extract price with progressive waiting
                price = None
                for price_attempt in range(3):
                    wait_time = (price_attempt + 1) * 3  # 3s, 6s, 9s
                    print(f"💰 Price attempt {price_attempt + 1}: waiting {wait_time}s...")
                    time.sleep(wait_time)
                    price = try_extract_price(page)

                    if price:
                        print(f"✅ Price found on attempt {price_attempt + 1}: {price}")
                        break
                    else:
                        print(f"❌ No price found on attempt {price_attempt + 1}")

                        # Try to close popups between attempts
                        if price_attempt < 2:
                            try:
                                close_button = page.get_by_role("button", name="Close").first
                                if close_button.is_visible(timeout=2000):
                                    close_button.click()
                                    print("✅ Closed popup during price extraction")
                                    time.sleep(2)
                            except:
                                pass

                print(f"{'✅' if price else '❌'} Final result: {price if price else 'Price not found'}")

                if price:
                    return price
                else:
                    raise Exception("Price not found after multiple attempts")

            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5s, 10s, 15s between retries
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed for {url}")
                    return None
            finally:
                page.close()
                context.close()
                browser.close()

    return None

def check_availability(page):
    """Check if the room is available for the selected dates"""
    try:
        # Check for "Those dates are not available" message
        not_available_text = page.get_by_text("Those dates are not available")
        if not_available_text.is_visible(timeout=3000):
            print("🚫 Room is NOT available for selected dates")
            return False

        # Check for other unavailability indicators
        unavailable_indicators = [
            "Dates not available",
            "Not available",
            "Booked",
            "Unavailable"
        ]

        page_text = page.text_content("body")
        for indicator in unavailable_indicators:
            if indicator.lower() in page_text.lower():
                print(f"🚫 Room appears unavailable (found: {indicator})")
                return False

        print("✅ Room appears to be available")
        return True

    except Exception as e:
        print(f"⚠️  Could not check availability: {e}")
        return True  # Assume available if we can't check

def try_extract_price(page):
    """Try to extract price using multiple methods"""
    price = None

    # Method 1: Look for price breakdown text
    try:
        price_elements = page.locator("[data-testid*='price']").all()
        for element in price_elements:
            text = element.text_content()
            if text and ('฿' in text or 'zł' in text or '$' in text):
                price = text
                print(f"💰 Method 1 found price: {price}")
                return price
    except:
        pass

    # Method 2: Look for price in booking sidebar (from old script)
    if not price:
        try:
            price_text = page.get_by_test_id("bookit-sidebar").text_content()
            # Extract price using regex
            price_match = re.search(r'[฿$zł]\s*[\d,]+', price_text)
            if price_match:
                price = price_match.group()
                print(f"💰 Method 2 found price: {price}")
                return price
        except:
            pass

    # Method 3: Look for specific price text from old script
    if not price:
        try:
            # Try the exact selector from the old script
            price_element = page.get_by_text("฿").first
            if price_element.is_visible(timeout=2000):
                text = price_element.text_content()
                if text and ('฿' in text or 'zł' in text or '$' in text):
                    price = text
                    print(f"💰 Method 3 found price: {price}")
                    return price
        except:
            pass

    # Method 4: General text search for price patterns
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
                            print(f"💰 Method 4 found price: {price}")
                            return price
        except:
            pass

    return None

def main():
    """Main function to read CSV and process URLs"""
    csv_file = 'airbnb.csv'
    check_in = '2025-11-23'  # Hardcoded check-in date
    check_out = '2026-01-06' # Hardcoded check-out date

    # Initialize statistics
    stats = {
        'total_processed': 0,
        'successful_prices': 0,
        'not_available': 0,
        'failed_scrapes': 0,
        'skipped_invalid': 0,
        'prices_found': []
    }

    try:
        print("🔍 Loading CSV file...")
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Skip header row

            print("🚀 Starting Airbnb price scraping...")
            print(f"📅 Using hardcoded dates: {check_in} to {check_out}")
            print("=" * 50)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                if len(row) > 0:  # Make sure row has data
                    original_url = row[0]  # URL is in the first column

                    if not original_url or not original_url.startswith('https://www.airbnb.com'):
                        print(f"⏭️  Skipping invalid URL in row {row_num}: {original_url}")
                        stats['skipped_invalid'] += 1
                        continue

                    stats['total_processed'] += 1
                    print(f"\n📍 Processing row {row_num}:")
                    print(f"🔗 Original URL: {original_url}")

                    # Extract room ID from URL
                    room_id = extract_room_id(original_url)
                    if not room_id:
                        print(f"❌ Could not extract room ID from URL: {original_url}")
                        stats['failed_scrapes'] += 1
                        continue

                    print(f"🏠 Room ID: {room_id}")
                    print(f"📅 Using hardcoded dates: {check_in}, {check_out}")

                    # Create clean URL for navigation
                    clean_url_to_use = clean_url(original_url)
                    print(f"✨ Clean URL: {clean_url_to_use}")

                    # Reconstruct URL with room ID and hardcoded dates
                    reconstructed_url = reconstruct_url(room_id, check_in, check_out)
                    print(f"🔧 Reconstructed URL: {reconstructed_url}")

                    # Use reconstructed URL for scraping
                    url_to_scrape = reconstructed_url

                    # Scrape price
                    print("🎯 Starting price scraping...")
                    price = scrape_airbnb_price(url_to_scrape, check_in, check_out)

                    # Update statistics
                    if price == "Not Available":
                        stats['not_available'] += 1
                        print(f"🚫 Status: Not Available")
                    elif price and price != "Not Available":
                        stats['successful_prices'] += 1
                        stats['prices_found'].append({
                            'row': row_num,
                            'room_id': room_id,
                            'price': price,
                            'url': url_to_scrape
                        })
                        print(f"💰 Status: Price found - {price}")
                    else:
                        stats['failed_scrapes'] += 1
                        print(f"❌ Status: Failed to scrape")

                    print(f"💵 Final price: {price if price else 'Not found'}")
                    print("-" * 30)

                    # Wait longer between requests to be respectful and avoid rate limiting
                    wait_time = 5 + (row_num % 3) * 2  # 5-9 seconds with some variation
                    print(f"⏳ Waiting {wait_time} seconds before next request...")
                    time.sleep(wait_time)

        # Print summary statistics
        print_summary(stats, check_in, check_out)

    except FileNotFoundError:
        print(f"❌ Error: File '{csv_file}' not found")
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")

def print_summary(stats, check_in, check_out):
    """Print comprehensive summary of scraping results"""
    print("\n" + "=" * 60)
    print("📊 SCRAPING SUMMARY")
    print("=" * 60)
    print(f"📅 Dates checked: {check_in} to {check_out}")
    print(f"🔗 Total URLs processed: {stats['total_processed']}")
    print(f"⏭️  Skipped invalid URLs: {stats['skipped_invalid']}")
    print("-" * 60)
    print(f"✅ Successful price extraction: {stats['successful_prices']}")
    print(f"🚫 Rooms not available: {stats['not_available']}")
    print(f"❌ Failed scrapes: {stats['failed_scrapes']}")
    print("-" * 60)

    # Calculate success rate
    if stats['total_processed'] > 0:
        success_rate = (stats['successful_prices'] / stats['total_processed']) * 100
        availability_rate = (stats['not_available'] / stats['total_processed']) * 100
        failure_rate = (stats['failed_scrapes'] / stats['total_processed']) * 100

        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"🚫 Unavailability rate: {availability_rate:.1f}%")
        print(f"❌ Failure rate: {failure_rate:.1f}%")

    # Show found prices
    if stats['prices_found']:
        print(f"\n💰 PRICES FOUND ({len(stats['prices_found'])} listings):")
        print("-" * 40)
        for i, item in enumerate(stats['prices_found'], 1):
            print(f"{i}. Row {item['row']} - Room {item['room_id']}: {item['price']}")

    print("\n🎉 Scraping completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
