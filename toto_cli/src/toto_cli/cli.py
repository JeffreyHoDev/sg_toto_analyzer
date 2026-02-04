import click
from pymongo import MongoClient, DESCENDING
from tabulate import tabulate

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING")
DB_NAME = os.getenv("MONGODB_DBNAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

@click.group()
def cli():
    """SG Toto CLI Tool"""
    pass

@cli.command()
@click.option('--num', type=int, default=3, help="Number of draws to fetch")
def latest(num):
    """Fetch the latest NUM results from MongoDB."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # 1. Sort by date descending (-1)
        # 2. Limit by the number provided
        results = list(collection.find().sort("date", DESCENDING).limit(num))

        if not results:
            click.echo("No results found in the database.")
            return

        # Prepare data for display
        table_data = []
        for doc in results:
            table_data.append([
                doc["date"].strftime("%Y-%m-%d"),
                ", ".join(map(str, doc["winning_numbers"])),
                doc.get("additional_number", "-")
            ])

        # Pretty print the output
        headers = ["Date", "Winning Numbers", "Addl No"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.secho(f"Error connecting to MongoDB: {e}", fg="red")
    finally:
        client.close()

if __name__ == "__main__":
    cli()