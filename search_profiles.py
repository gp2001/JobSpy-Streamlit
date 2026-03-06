import random
import time
from urllib.parse import quote_plus, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    return random.choice(user_agents)


def requests_bing_linkedin_search(query, max_results=10, timeout=10):
    """Use requests library to search Bing for LinkedIn profiles."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.bing.com/",
    })

    search_url = f"https://www.bing.com/search?q={quote_plus(f'site:linkedin.com/in/ {query}')}"
    print(f"Fetching: {search_url}")

    try:
        response = session.get(search_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch Bing results: {e}")
        return pd.DataFrame(columns=["url", "title"])

    soup = BeautifulSoup(response.content, "html.parser")

    results = []
    seen = set()

    # Try multiple selectors that Bing may use
    selectors_map = [
        ("li.b_algo h2 a", "h2 a"),
        ("div.b_algo h2 a", "h2 a"),
        ("h2 a", None),
    ]

    for selector, child_selector in selectors_map:
        if selector == "h2 a":
            links = soup.find_all("h2")
            for link_elem in links:
                a_tag = link_elem.find("a")
                if a_tag and a_tag.get("href"):
                    href = a_tag.get("href")
                    if "linkedin.com/in/" in href and href not in seen:
                        seen.add(href)
                        results.append({"url": href, "title": a_tag.text.strip()})
        else:
            links = soup.select(selector)
            for a_tag in links:
                if a_tag.get("href"):
                    href = a_tag.get("href")
                    # Extract actual LinkedIn URL if it's a redirect
                    if "url=" in href:
                        try:
                            parsed = parse_qs(urlparse(href).query)
                            if "u" in parsed:
                                href = parsed["u"][0]
                            elif "url" in parsed:
                                href = parsed["url"][0]
                        except Exception:
                            pass

                    if "linkedin.com/in/" in href and href not in seen:
                        seen.add(href)
                        results.append({"url": href, "title": a_tag.text.strip()})

        if results:
            break

    if results:
        return pd.DataFrame(results[:max_results], columns=["url", "title"])

    print(f"No LinkedIn profiles found via requests. Response status: {response.status_code}")
    print(f"Page title: {soup.title.string if soup.title else 'No title'}")
    return pd.DataFrame(columns=["url", "title"])


def selenium_bing_linkedin_search(query, max_results=10, timeout=20, headless=True):
    """Search Bing for LinkedIn profiles using Selenium with JavaScript execution."""
    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ModuleNotFoundError:
        print("Selenium not available, falling back to requests-based search...")
        return requests_bing_linkedin_search(query, max_results, timeout)

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)

        search_url = f"https://www.bing.com/search?q={quote_plus(f'site:linkedin.com/in/ {query}')}"
        print(f"Fetching with Selenium: {search_url}")
        driver.get(search_url)

        # Wait for page to fully load
        time.sleep(4)

        wait = WebDriverWait(driver, timeout)

        # Try to wait for results, with a fallback if timeout
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo h2 a")))
        except TimeoutException:
            print("Timeout waiting for standard Bing results. Checking page state...")

        # Primary and fallback selectors for Bing result links.
        selectors = ["li.b_algo h2 a", "#b_results h2 a", "a[href*='linkedin.com/in/']"]
        elems = []
        for selector in selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, selector)
                if elems:
                    print(f"Found {len(elems)} elements with selector: {selector}")
                    break
            except NoSuchElementException:
                continue

        results = []
        seen = set()
        for elem in elems:
            try:
                href = elem.get_attribute("href")
                if not href or "linkedin.com/in/" not in href:
                    continue
                if href in seen:
                    continue

                seen.add(href)
                title = elem.text.strip() if elem.text else "LinkedIn Profile"
                results.append({"url": href, "title": title})
                if len(results) >= max_results:
                    break
            except Exception as e:
                print(f"Skipping element due to error: {e}")
                continue

        if results:
            return pd.DataFrame(results, columns=["url", "title"])

        print(f"No results via Selenium. Falling back to requests-based search...")
        return requests_bing_linkedin_search(query, max_results, timeout)

    except WebDriverException as e:
        print(f"WebDriver error: {e}. Falling back to requests...")
        return requests_bing_linkedin_search(query, max_results, timeout)
    except TimeoutException as e:
        print(f"Timeout: {e}. Falling back to requests...")
        return requests_bing_linkedin_search(query, max_results, timeout)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    query = "ICT Group Netherlands data scientist"
    df = selenium_bing_linkedin_search(query, max_results=20)
    print(df)

