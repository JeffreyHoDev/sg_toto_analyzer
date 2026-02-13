import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime

import os
from dotenv import load_dotenv

from fastapi import FastAPI

app = FastAPI()

load_dotenv()
# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING")
URL = "https://en.lottolyzer.com/history/singapore/toto/"
DB_NAME = os.getenv("MONGODB_DBNAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

def get_latest_draw_from_web():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table and the first row in tbody
        table = soup.find('table', id='summary-table')
        if not table:
            print("Could not find the summary table.")
            return None
            
        first_row = table.find('tbody').find('tr')
        cells = first_row.find_all('td')

        # Data Extraction based on your provided HTML structure
        draw_no = int(cells[0].text.strip())
        date_str = cells[1].text.strip() # "2026-02-02"
        win_nums_raw = cells[2].text.strip() # "4,19,40,41,46,47"
        add_num_raw = cells[3].text.strip() # "20"

        # Convert to proper types
        draw_date = datetime.strptime(date_str, "%Y-%m-%d")
        winning_numbers = [int(n.strip()) for n in win_nums_raw.split(',') if n.strip()]
        additional_number = int(add_num_raw) if add_num_raw else None

        return {
            "draw_no": draw_no,
            "date": draw_date,
            "winning_numbers": winning_numbers,
            "additional_number": additional_number
        }

    except Exception as e:
        print(f"Error scraping data: {e}")
        return None

def sync_to_mongodb(latest_data):
    if not latest_data:
        return

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Check if data with this date already exists
    query = {"date": latest_data["date"]}
    existing_doc = collection.find_one(query)

    if existing_doc:
        print(f"[-] Data for {latest_data['date'].strftime('%Y-%m-%d')} already exists. Skipping.")
    else:
        # Insert the document
        latest_data["updated_at"] = datetime.now()
        collection.insert_one(latest_data)
        print(f"[+] Successfully inserted Draw {latest_data['draw_no']} for {latest_data['date'].strftime('%Y-%m-%d')}")

    client.close()

@app.get("/")
def read_root():
    try:
        print(f"Starting sync at {datetime.now()}")
        data = get_latest_draw_from_web()
        if data:
            sync_to_mongodb(data)
            return "Success"
        return "Failed"
    except Exception as e:
        return f"Error-{str(e)}"

@app.get("/health")
def health():
    try:
        return "OK"
    except Exception as e:
        return f"Error-{str(e)}"
    