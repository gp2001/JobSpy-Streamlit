import pandas as pd
from ddgs import DDGS


def ddg_linkedin_search(query: str, max_results: int = 10) -> pd.DataFrame:
    """
    Search DuckDuckGo for LinkedIn profiles using the duckduckgo-search library.
    Much more reliable than scraping Bing directly — no Selenium or HTML parsing needed.
    """
    search_query = f"site:linkedin.com/in/ {query}"
    results = []

    try:
        with DDGS() as searcher:
            for r in searcher.text(search_query, max_results=max_results * 3):
                url = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")

                if "linkedin.com/in/" not in url:
                    continue

                # Clean up the name from the page title
                name = title
                for suffix in [" | LinkedIn", " - LinkedIn", "| LinkedIn", "- LinkedIn"]:
                    name = name.replace(suffix, "")
                name = name.strip()

                results.append({
                    "name": name,
                    "url": url,
                    "description": body,
                })

                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")

    cols = ["name", "url", "description"]
    return pd.DataFrame(results, columns=cols) if results else pd.DataFrame(columns=cols)


# Backwards-compatible wrapper — app.py calls this name
def selenium_bing_linkedin_search(query: str, max_results: int = 10, **kwargs) -> pd.DataFrame:
    """
    Previously used Selenium + Bing, but Bing blocks automated requests.
    Now delegates to DuckDuckGo search which is reliable without a browser.
    """
    return ddg_linkedin_search(query, max_results)


if __name__ == "__main__":
    query = "ICT Group Netherlands data scientist"
    df = ddg_linkedin_search(query, max_results=10)
    print(df.to_string())