import csv
from datetime import datetime
from pymongo import MongoClient

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

connection_string = os.getenv("MONGODB_CONNECTION_STRING")
client = MongoClient(connection_string)
db = client['lottery_db']
collection = db['toto_results']

def ingest_data(file_path):
    draws = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert "4,19,40,41,46,47" -> [4, 19, 40, 41, 46, 47]
            win_nums = [int(n.strip()) for n in row['Winning No.'].split(',') if n.strip()]
            
            doc = {
                "date": datetime.strptime(row['Date'], "%Y-%m-%d"),
                "winning_numbers": win_nums,
                "additional_number": int(row['Addl No.']) if row['Addl No.'].strip() else None
            }
            draws.append(doc)
    
    # Insert many for efficiency
    if draws:
        result = collection.insert_many(draws)
        print(f"Successfully ingested {len(result.inserted_ids)} draws.")

if __name__ == "__main__":
    ingest_data('../toto_results.csv')