### Lighthouse Audit Script

This script runs Lighthouse audits on selected Daily Bruin URLs and outputs
JSON reports and a consolidated CSV file.

#### Setup

1. Install Python dependencies:
```bash
pip install pandas 
```
2. Install Lighthouse:
```bash
npm install -g lighthouse
```
3. Run Audit (it may take around 1 minute to run). Files will be made into audit-reports folder.
```bash
python3 audit.py
```
4. Open the CSV file to view the audit results. JSON files are generated per URL.
