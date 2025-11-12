import json
import os
import pandas as pd
import re
import subprocess
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# create data frame
df = pd.DataFrame([], columns=['URL','SEO','Accessibility','Performance','Best Practices','Broken Links'])

# create support variables
name = "DailyBruin" 
getdate = datetime.now().strftime("%m-%d-%y")

# Rate limiting: delay between link checks (in seconds)
DELAY_BETWEEN_CHECKS = 0.5  # Check links every 0.5 seconds to avoid overwhelming the server
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests (in seconds)

def extract_links_from_page(url):
    """Extract all links (href attributes) from a given page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()  # Use set to avoid duplicates
        
        # Find all anchor tags with href attributes
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(url, href)
            # Remove fragment (#section) from URL
            parsed = urlparse(absolute_url)
            absolute_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                absolute_url += f"?{parsed.query}"
            links.add(absolute_url)
        
        return list(links)
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        return []

def check_link_status(link_url):
    """Check if a link returns a successful HTTP status code."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        # Use HEAD request first (faster), fall back to GET if not supported
        response = requests.head(link_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        # If HEAD is not allowed, try GET
        if response.status_code == 405:
            response = requests.get(link_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        return response.status_code, None
    except requests.exceptions.RequestException as e:
        return None, str(e)

def find_broken_links(base_url, all_links):
    """Check all links and return list of broken ones."""
    broken_links = []
    print(f"  Checking {len(all_links)} links found on {base_url}...")
    
    for i, link in enumerate(all_links, 1):
        # Skip links that are not HTTP/HTTPS (like mailto:, tel:, javascript:, etc.)
        if not link.startswith(('http://', 'https://')):
            continue
        
        status_code, error = check_link_status(link)
        
        # Consider 4xx and 5xx status codes as broken
        if status_code and (status_code >= 400):
            broken_links.append({
                'url': link,
                'status_code': status_code,
                'error': error
            })
            print(f"    ❌ Broken link found ({i}/{len(all_links)}): {link} - Status: {status_code}")
        
        # Rate limiting: delay between checks
        if i < len(all_links):
            time.sleep(DELAY_BETWEEN_CHECKS)
    
    return broken_links

def load_urls_from_csv(csv_path):
    """
    Load URLs from a CSV file created by webcrawling.py
    
    Args:
        csv_path: Path to the CSV file containing URLs
        
    Returns:
        List of URLs extracted from the 'URL' column
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Check if 'URL' column exists
        if 'URL' not in df.columns:
            print(f"Error: 'URL' column not found in {csv_path}")
            print(f"Available columns: {list(df.columns)}")
            return []
        
        # Extract URLs and remove any NaN values
        urls = df['URL'].dropna().tolist()
        
        print(f"Loaded {len(urls)} URLs from {csv_path}")
        return urls
        
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

# manually select some URLs to test this audit on, later we can expand this to crawl the site
urls = load_urls_from_csv("audit-reports/URL_List.csv")
# Folder to save all reports (relative path)
output_dir = "audit-reports" 
os.makedirs(output_dir, exist_ok=True) 

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
    
    # Delete the Lighthouse JSON report after extracting scores
    try:
        os.remove(json_filename)
        print(f"  ✓ Deleted Lighthouse report: {json_filename}")
    except Exception as e:
        print(f"  ⚠ Could not delete {json_filename}: {e}")

    # Check for broken links first (before adding to DataFrame)
    print(f"\nChecking for broken links on: {url}")
    all_links = extract_links_from_page(url)
    broken_links = find_broken_links(url, all_links)
    
    # Save broken links to a separate JSON file
    broken_links_filename = os.path.join(output_dir, f"{name}_{getdate}_{safe_url}.broken_links.json")
    broken_links_data = {
        'page_url': url,
        'total_links_checked': len(all_links),
        'broken_links_count': len(broken_links),
        'broken_links': broken_links,
        'timestamp': datetime.now().isoformat()
    }
    # with open(broken_links_filename, 'w') as f:
    #     json.dump(broken_links_data, f, indent=2)
    
    print(f"  ✓ Found {len(broken_links)} broken link(s) out of {len(all_links)} total links")

    # add data to dataframe
    row = {
        "URL": url,
        "SEO": seo,
        "Accessibility": accessibility,
        "Performance": performance,
        "Best Practices": best_practices,
        "Broken Links Count": len(broken_links),
        "Broken Links": broken_links
    }

    # Append the dictionary as a new row in the DataFrame
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    print(f"Added results for {url}\n")
  
save_path = os.path.join(output_dir, f"lighthouse_{name}_{getdate}.csv")
df.to_csv(save_path, index=False)

print("All results saved to:", save_path)
print(df)