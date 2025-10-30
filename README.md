### Lighthouse Audit Script

This script runs Lighthouse audits on selected Daily Bruin URLs and outputs
JSON reports and a consolidated CSV file. It also checks for broken links on each page.

#### Setup

1. Install Python dependencies:
```bash
pip install pandas requests beautifulsoup4
```
2. Install Lighthouse:
```bash
npm install -g lighthouse
```
3. Run Audit (it may take several minutes to run, depending on the number of links found). Files will be made into audit-reports folder.
```bash
python3 audit.py
```
4. Open the CSV file to view the audit results. JSON files are generated per URL.
   - Lighthouse reports: `DailyBruin_MM-DD-YY_[URL].report.json`
   - Broken links: `DailyBruin_MM-DD-YY_[URL].broken_links.json`
   - Summary CSV: `lighthouse_DailyBruin_MM-DD-YY.csv`

#### Features

- **Lighthouse Audits**: Performance, SEO, Accessibility, and Best Practices scores
- **Broken Link Detection**: Automatically checks all links on each page for 404 errors and other HTTP errors
- **Rate Limiting**: Includes delays between link checks to avoid overwhelming the server
