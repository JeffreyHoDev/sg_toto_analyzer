import requests
from bs4 import BeautifulSoup
import csv
import time

def crawl_toto_data():
    base_url = "https://en.lottolyzer.com/search/singapore/toto/search-by-date/2020-01-01/2026-02-02/page/{}/per-page/20/summary-view"
    output_file = "toto_results.csv"
    
    # Define headers to mimic a browser (prevents some 403 Forbidden errors)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write the header row
        writer.writerow(['Date', 'Winning No.', 'Addl No.'])

        for page_num in range(1, 32):  # Pages 1 to 31
            print(f"Scraping page {page_num}...")
            url = base_url.format(page_num)
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', id='summary-table')
                
                if not table:
                    print(f"Warning: No table found on page {page_num}")
                    continue
                
                rows = table.find('tbody').find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    
                    # Based on your HTML:
                    # Index 1 = Date
                    # Index 2 = Winning No.
                    # Index 3 = Addl No.
                    if len(cols) >= 4:
                        date = cols[1].get_text(strip=True)
                        winning_no = cols[2].get_text(strip=True)
                        addl_no = cols[3].get_text(strip=True)
                        
                        writer.writerow([date, winning_no, addl_no])
                
                # Small delay to be polite to the server
                time.sleep(1)
                
            except Exception as e:
                print(f"Error on page {page_num}: {e}")

    print(f"Done! Data saved to {output_file}")

if __name__ == "__main__":
    crawl_toto_data()