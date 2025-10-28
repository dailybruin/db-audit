import json
import os
import pandas as pd
import re
import subprocess
from datetime import datetime

# create data frame
df = pd.DataFrame([], columns=['URL','SEO','Accessibility','Performance','Best Practices'])

# create support variables
name = "DailyBruin" 
getdate = datetime.now().strftime("%m-%d-%y")

# manually select some URLs to test this audit on, later we can expand this to crawl the site
urls = ["https://dailybruin.com/",
        "https://dailybruin.com/2025/10/27/beat-breakdown-following-ryder-dodd-who-is-ucla-mens-waterpolos-next-best-player",
        "https://dailybruin.com/category/news"
]
output_dir = "/Users/hannie/db-audit"
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
  
save_path = "/Users/hannie/db-audit/lighthouse_" + name + "_" + getdate + ".csv"
df.to_csv(save_path, index=False)

print("All results saved to:", save_path)
print(df)