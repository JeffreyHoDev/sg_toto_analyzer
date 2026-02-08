from datetime import datetime
import click
def parse_date_range(ctx, param, value):
    """Callback to split 'YYYY-MM-DD-YYYY-MM-DD' into two dates."""
    if not value:
        return None, None
    
    try:
        # Split by the 11th character to handle YYYY-MM-DD-YYYY-MM-DD
        # (A simple .split('-') would fail because the dates themselves have dashes)
        parts = value.split(':') if ':' in value else [value]
        
        # If user provides "YYYY-MM-DD-YYYY-MM-DD"
        if len(parts) == 1 and len(value) > 10:
            # Fallback split logic if they use a dash between dates: 2024-01-01-2024-12-31
            # We look for the dash at index 10
            start_str = value[:10]
            end_str = value[11:]
        else:
            # Recommended format: 2024-01-01:2024-12-31
            start_str = parts[0]
            end_str = parts[1] if len(parts) > 1 else None

        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else None
        
        return start_dt, end_dt
    except Exception:
        raise click.BadParameter("Format must be YYYY-MM-DD:YYYY-MM-DD")