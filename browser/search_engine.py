from playwright.sync_api import sync_playwright
import time
import random
from browser.scrolling import human_mouse_move

def click_search_button(page, log=print):
    
    time.sleep(random.uniform(0.5, 1.0))
    
    search_button = None
    selectors = [
        'a[href="#"]:has(svg[aria-label="Search"])',
        'xpath=//a[.//svg[@aria-label="Search"]]',
        'xpath=//span[text()="Search"]/ancestor::a',
        'xpath=//div[contains(@class, "x1n2onr6")]//a[.//svg[@aria-label="Search"]]',
        '[role="link"]:has(svg[aria-label="Search"])',
        'xpath=//*[@aria-label="Search" or @aria-label="search"]',
    ]
    
    for selector in selectors:
        try:
            search_button = page.query_selector(selector)
            if search_button:
                break
        except:
            continue
    
    if not search_button:
        search_button = page.query_selector('svg[aria-label="Search"]')
        if search_button:
            search_button = page.query_selector('xpath=//svg[@aria-label="Search"]/ancestor::a[1]')
    
    if search_button:
        try:
            human_mouse_move(page, search_button)
            search_button.hover()
            time.sleep(random.uniform(0.5, 1.0))
            search_button.click()
            log("Search button clicked!")
            return True
        except:
            try:
                page.click('svg[aria-label="Search"]')
                log("Search button clicked!")
                return True
            except:
                pass
    
    # Fallback to keyboard shortcut
    log("Search button not found, trying keyboard shortcut...")
    page.keyboard.press('/')
    return True


def find_and_activate_search_input(page, log=print):
    time.sleep(random.uniform(1.5, 2.5))
    
    search_input = None
    input_selectors = [
        'input[placeholder="Search"]',
        'input[aria-label="Search input"]',
        'input[type="text"][placeholder*="Search"]',
        'xpath=//input[@placeholder="Search"]',
        'xpath=//input[contains(@aria-label, "Search")]',
    ]
    
    for selector in input_selectors:
        try:
            search_input = page.wait_for_selector(selector, timeout=3000)
            if search_input:
                log("Found search input!")
                break
        except:
            continue
    
    if search_input:
        try:
            human_mouse_move(page, search_input)
            search_input.hover()
            time.sleep(random.uniform(0.4, 0.8))
            search_input.click()
            log("Search input activated!")
            time.sleep(random.uniform(0.5, 1.0))
            return search_input
        except Exception as e:
            log(f"Error activating search input: {e}")
    
    return None


def type_search_term(page, search_term, log=print):
    log(f"Typing '{search_term}'...")
    time.sleep(random.uniform(0.3, 0.7))
    
    try:
        search_input = page.query_selector('input[placeholder="Search"]')
        if not search_input:
            search_input = page.query_selector('input[aria-label="Search input"]')
        
        if search_input:
            search_input.fill('')
            time.sleep(random.uniform(0.2, 0.4))
            
            for char in search_term:
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.2, 0.4))
                search_input.type(char, delay=random.uniform(80, 180))
                time.sleep(random.uniform(0.03, 0.12))
            
            log(f"✅ Typed: {search_term}")
            return True
        else:
            log("earch input not found, using keyboard...")
            page.keyboard.type(search_term, delay=random.uniform(80, 180))
            return True
            
    except Exception as e:
        log(f"❌ Error typing: {e}")
        return False


def click_search_result(page, search_type="hashtag", log=print):
    time.sleep(random.uniform(2.0, 3.0))
    
    if search_type == "hashtag":
        log("Looking for hashtag results...")
        result_selectors = [
            'xpath=//a[contains(@href, "/explore/tags/")]',
            'xpath=//span[contains(text(), "#")]/ancestor::a',
        ]
    else:
        log("Looking for user results...")
        result_selectors = [
            'xpath=//a[contains(@href, "/") and not(contains(@href, "/explore/"))]',
            'xpath=//div[@role="none"]//a',
        ]
    
    for selector in result_selectors:
        try:
            results = page.query_selector_all(selector)
            if results:
                visible_results = [r for r in results[:5] if r.is_visible()]
                if visible_results:
                    target = visible_results[0]
                    time.sleep(random.uniform(0.3, 0.6))
                    human_mouse_move(page, target)
                    target.hover()
                    time.sleep(random.uniform(0.4, 0.8))
                    target.click()
                    log("✅ Clicked on search result!")
                    return True
        except:
            continue
    
    log("Could not find result to click")
    return False


def perform_search(page, search_term, search_type="hashtag", log=print):
    # Click search button
    if not click_search_button(page, log):
        return False
    
    # Find and activate search input
    search_input = find_and_activate_search_input(page, log)
    if not search_input:
        log("❌ Could not find search input")
        return False
    
    # Type the search term
    if not type_search_term(page, search_term, log):
        return False
    
    # Click on result
    return click_search_result(page, search_type, log)

def search_instagram(account_path, search_term, search_type="hashtag", stop_flag=None, log_callback=None, keep_open=True, headless=False):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    
    def should_stop():
        if stop_flag and callable(stop_flag):
            return stop_flag()
        return False
    
    # Status updates
    if headless:
        log("Running in headless mode (browser hidden)")
    else:
        log("Running with visible browser")
    
    log("Launching browser...")
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            account_path, 
            headless=headless,
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        log("Browser launched successfully")
        
        # Navigate to Instagram
        log("Navigating to Instagram...")
        page.goto("https://www.instagram.com")
        try:
            page.wait_for_load_state('domcontentloaded', timeout=5000)
            log("✅ Instagram loaded")
        except:
            log("Page loading...")
        
        # Human-like initial wait
        time.sleep(random.uniform(1.5, 2.5))
        
        # Perform search using helper functions
        log("🔍 Starting search process...")
        if not perform_search(page, search_term, search_type, log):
            log("❌ Search failed")
            context.close()
            return
        
        time.sleep(random.uniform(2.0, 3.0))
        log(f"🎉 Search completed for: {search_term}")
        
        # Keep browser open if requested
        if keep_open:
            log("📌 Browser staying open. Click 'Stop' to close.")
            while not should_stop():
                try:
                    page.wait_for_timeout(1000)
                except:
                    break
        try:
            context.close()
        except:
            pass