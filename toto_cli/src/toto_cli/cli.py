import click
from pymongo import MongoClient, DESCENDING
from itertools import combinations
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
              help="Format YYYY-MM-DD:YYYY-MM-DD Show the result within the date range")
def topnum(num, csv, date_range):
    """Analyze TOTO frequencies using local Pandas filtering."""
    try:
        client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        db = client[os.getenv("MONGODB_DBNAME")]
        collection = db[os.getenv("MONGODB_COLLECTION")]
        
        # 1. Fetch all data
        click.echo("📥 Fetching data from MongoDB...")
        data = list(collection.find({}, {"winning_numbers": 1, "date": 1, "_id": 0}))
        
        if not data:
            click.echo("No data found in MongoDB.")
            return

        # 2. Convert to DataFrame
        df = pd.DataFrame(data)
        # 3. Fix the Date Type locally (DOES NOT update MongoDB)
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

        # 5. Explode and Count
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

@click.command()
def combination():
    """Analyze TOTO combination frequency."""
    try:
        client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        db = client[os.getenv("MONGODB_DBNAME")]
        collection = db[os.getenv("MONGODB_COLLECTION")]

        data = list(collection.find({}, {"winning_numbers": 1, "date": 1, "_id": 0}))
        df = pd.DataFrame(data)
        df["Combination"] = df["winning_numbers"].apply(lambda nums: tuple(sorted(nums)))
        combo_counts = (
            df["Combination"]
            .value_counts()
            .reset_index()
            .rename(columns={"Combination": "winning_numbers", "count": "Occurrences"})
        )

        combo_counts["winning_numbers"] = combo_counts["winning_numbers"].apply(
            lambda c: ", ".join(str(n) for n in c)
        )

        # Pretty print the output
        headers = ["Combination", "Occurrences"]
        click.echo(tabulate(combo_counts.head(3), headers=headers, tablefmt="grid", showindex=False))

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
    finally:
        client.close()    

@click.command()
@click.option('--group-size', '-g', default=2, type=click.IntRange(2, 6), 
              help='Size of number groups to analyze (2-6, default: 2)')
@click.option('--top', '-t', default=10, type=int,
              help='Number of top results to display (default: 10)')
def groupfreq(group_size, top):
    """
    Analyze frequency of number groups in lottery history.
    
    Examples:
        lottery frequency --group-size 2    # Find most common pairs
        lottery frequency -g 3 -t 15        # Find top 15 triplets
        lottery frequency -g 6              # Find exact 6-number combinations
    """
    try:
        client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        db = client[os.getenv("MONGODB_DBNAME")]
        collection = db[os.getenv("MONGODB_COLLECTION")]

        # Load data from MongoDB
        data = list(collection.find({}, {"winning_numbers": 1, "_id": 0}))
        df = pd.DataFrame(data)
        
        if df.empty:
            click.secho("❌ No data found in database", fg="red")
            return

        # Generate all combinations of the specified size from each draw
        all_combos = []
        for numbers in df["winning_numbers"]:
            for combo in combinations(sorted(numbers), group_size):
                all_combos.append(combo)
        
        # Count occurrences using pandas
        combo_series = pd.Series(all_combos)
        combo_counts = (
            combo_series
            .value_counts()
            .reset_index()
            .rename(columns={"index": "Numbers", "count": "Occurrences"})
        )
        
        # Format the numbers as readable strings
        combo_counts["Numbers"] = combo_counts["Numbers"].apply(
            lambda c: ", ".join(str(n) for n in c)
        )
        
        # Display results
        group_labels = {2: "Pairs", 3: "Triplets", 4: "Quads", 5: "Quintets", 6: "Six-Number Sets"}
        click.secho(f"\n🎲 Top {top} Most Frequent {group_labels.get(group_size, f'{group_size}-Number Groups')}", 
                    fg="cyan", bold=True)
        
        headers = ["Numbers", "Occurrences"]
        click.echo(tabulate(combo_counts.head(top), headers=headers, tablefmt="grid", showindex=False))
        click.echo()

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
    finally:
        client.close()



cli.add_command(latest)
cli.add_command(topnum)
cli.add_command(combination)
cli.add_command(groupfreq)


if __name__ == "__main__":
    cli()


