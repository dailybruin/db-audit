import json
import os
import pandas as pd
import re
import subprocess
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import deque

# create data frame
df = pd.DataFrame([], columns=['URL','SEO','Accessibility','Performance','Best Practices'])

# Configuration
SITE_URL = "https://dailybruin.com"
MAX_PAGES_TO_CRAWL = 50  # Limit to avoid overwhelming the site
RATE_LIMIT_DELAY = 2  # Seconds between requests (be respectful!)
MAX_DEPTH = 3  # Maximum depth to crawl from home page

# create support variables
name = "DailyBruin" 
getdate = datetime.now().strftime("%m-%d-%y")

# Track visited URLs to avoid duplicates
visited_urls = set()

def is_same_domain(url, base_domain):
    """Check if URL belongs to the same domain"""
    parsed = urlparse(url)
    return parsed.netloc == base_domain or parsed.netloc == "" or parsed.netloc.endswith("." + base_domain)

def normalize_url(url):
    """Normalize URL by removing fragments and trailing slashes"""
    parsed = urlparse(url)
    # Remove fragment
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    # Remove trailing slash except for root
    if normalized != SITE_URL and normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized

def crawl_website(start_url, max_pages=MAX_PAGES_TO_CRAWL, max_depth=MAX_DEPTH):
    """
    Crawl the website to discover URLs
    Uses BFS (Breadth-First Search) to find pages
    Since Scrapy is blocked, we use requests + BeautifulSoup
    """
    base_domain = urlparse(SITE_URL).netloc
    urls_to_visit = deque([(start_url, 0)])  # (url, depth)
    discovered_urls = set()
    
    print(f"Starting crawl from {start_url}...")
    print(f"Rate limiting: {RATE_LIMIT_DELAY} seconds between requests")
    print(f"Max pages: {max_pages}, Max depth: {max_depth}\n")
    
    while urls_to_visit and len(discovered_urls) < max_pages:
        current_url, depth = urls_to_visit.popleft()
        normalized = normalize_url(current_url)
        
        # Skip if already visited or too deep
        if normalized in visited_urls or depth > max_depth:
            continue
            
        visited_urls.add(normalized)
        
        # Rate limiting - be respectful!
        if len(discovered_urls) > 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        try:
            print(f"[Depth {depth}] Fetching: {normalized}")
            response = requests.get(normalized, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                discovered_urls.add(normalized)
                print(f"  ✓ Found page ({len(discovered_urls)}/{max_pages})")
                
                # Only parse HTML to find more links if we haven't reached max pages
                if len(discovered_urls) < max_pages and depth < max_depth:
                    try:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # Find all links
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            absolute_url = urljoin(normalized, href)
                            normalized_link = normalize_url(absolute_url)
                            
                            # Only follow same-domain links
                            if is_same_domain(normalized_link, base_domain):
                                if normalized_link not in visited_urls:
                                    urls_to_visit.append((normalized_link, depth + 1))
                    except Exception as e:
                        print(f"  ⚠ Error parsing HTML: {e}")
            else:
                print(f"  ✗ HTTP {response.status_code}: {normalized}")
                    
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error fetching {normalized}: {e}")
    
    print(f"\nCrawl complete! Discovered {len(discovered_urls)} URLs\n")
    return list(discovered_urls)

# Crawl the website to discover URLs automatically
print("="*60)
print("Daily Bruin Site Auditor - Web Crawler")
print("="*60)
urls = crawl_website(SITE_URL, MAX_PAGES_TO_CRAWL, MAX_DEPTH)
# Folder to save all reports (relative path)
output_dir = "audit-reports" 
os.makedirs(output_dir, exist_ok=True) 

# Run Lighthouse audit on discovered URLs
for url in urls:
    # create safe filename for JSON
    safe_url = re.sub(r'[^\w\-]', '_', url)
    json_filename = os.path.join(output_dir, f"{name}_{getdate}_{safe_url}.report.json")

    print(f"Running Lighthouse for: {url}")

    # Run Lighthouse synchronously and wait until done
    subprocess.run([
        "lighthouse",
        url,
        "--output=json",
        f"--output-path={json_filename}",
        "--quiet",
        "--chrome-flags=--headless"
    ], check=True)

    print(f"Report complete for: {url}")

    # Process JSON report
    with open(json_filename) as f:
        loaded_json = json.load(f)

    seo = str(round(loaded_json["categories"]["seo"]["score"] * 100))
    accessibility = str(round(loaded_json["categories"]["accessibility"]["score"] * 100))
    performance = str(round(loaded_json["categories"]["performance"]["score"] * 100))
    best_practices = str(round(loaded_json["categories"]["best-practices"]["score"] * 100))

    # add data to dataframe
    row = {
        "URL": url,
        "SEO": seo,
        "Accessibility": accessibility,
        "Performance": performance,
        "Best Practices": best_practices
    }

    # Append the dictionary as a new row in the DataFrame
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    print(f"Added results for {url}")
    print()  # Empty line for readability
  
save_path = os.path.join(output_dir, f"lighthouse_{name}_{getdate}.csv")
df.to_csv(save_path, index=False)

print("All results saved to:", save_path)
print(df)