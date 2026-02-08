import click
from pymongo import MongoClient, DESCENDING
from tabulate import tabulate
import pandas as pd
import os
from dotenv import load_dotenv

from .util import parse_date_range

# Load variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING")
DB_NAME = os.getenv("MONGODB_DBNAME")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION")

@click.group()
def cli():
    """SG Toto CLI Tool"""
    pass

@click.command()
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

@click.command()
@click.option('--num', type=int, default=6, help="Number of results to show")
@click.option('--csv', is_flag=True, help="Save results to CSV")
@click.option('--range', 'date_range', callback=parse_date_range, 
              help="Format YYYY-MM-DD:YYYY-MM-DD")
def topnum(num, csv, date_range):
    """Analyze TOTO frequencies using local Pandas filtering."""
    try:
        client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        db = client[os.getenv("MONGODB_DBNAME")]
        collection = db[os.getenv("MONGODB_COLLECTION")]
        
        # 1. Fetch EVERYTHING (since strings can't be filtered efficiently in DB)
        click.echo("📥 Fetching data from MongoDB...")
        data = list(collection.find({}, {"winning_numbers": 1, "date": 1, "_id": 0}))
        
        if not data:
            click.echo("No data found in MongoDB.")
            return

        # 2. Convert to DataFrame
        df = pd.DataFrame(data)
        # 3. Fix the Date Type locally (DOES NOT update MongoDB)
        # errors='coerce' turns bad dates into NaT (Not a Time)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # 4. Filter the DataFrame if range is provided
        start, end = date_range if date_range else (None, None)
        if start or end:
            if start:
                df = df[df['date'] >= pd.Timestamp(start)]
            if end:
                # Set to end of day to be inclusive
                df = df[df['date'] <= pd.Timestamp(end).replace(hour=23, minute=59)]
            click.echo(f"📅 Filtered locally for range. Remaining records: {len(df)}")

        if df.empty:
            click.echo("No records match that date range.")
            return

        # 5. Explode and Count (Your existing logic)
        exploded_df = df.explode('winning_numbers')
        counts = exploded_df['winning_numbers'].value_counts().reset_index()
        counts.columns = ['Number', 'Occurrence']
        
        top_results = counts.head(num)

        # 6. Output
        if csv:
            output_file = f"top_{num}_numbers.csv"
            top_results.to_csv(output_file, index=False)
            click.secho(f"✅ Saved to {output_file}", fg="green")
        else:
            click.echo(f"\n--- Top {num} Frequent Numbers ---")
            click.echo(top_results.to_string(index=False))

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
    finally:
        client.close()

cli.add_command(latest)
cli.add_command(topnum)

if __name__ == "__main__":
    cli()


