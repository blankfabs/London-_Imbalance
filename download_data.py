import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

def download_eurusd_data(start_date, end_date):
    """Download EURUSD 5-minute data from Yahoo Finance"""
    ticker = "EURUSD=X"
    
    print(f"Downloading {ticker} from {start_date} to {end_date}...")
    
    try:
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval="5m",
            progress=False
        )
        
        if df.empty:
            raise ValueError("No data downloaded. Check date range and ticker symbol.")
        
        # Clean data
        df = df.dropna()
        df.columns = [col.lower() for col in df.columns]
        
        print(f"Downloaded {len(df)} bars")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save to CSV
        output_file = "data/eurusd_5m.csv"
        df.to_csv(output_file)
        print(f"Saved to {output_file}")
        
        return df
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        raise

if __name__ == "__main__":
    # Download last 60 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    download_eurusd_data(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
