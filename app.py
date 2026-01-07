import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

# --- CONFIGURATION ---
# OLD: DB_URL = "postgresql://postgres:Meelad@127.0.0.1:5432/sentiment_engine"
# NEW: Use SQLite for easy cloud deployment
DB_URL = "sqlite:///sentiment.db"
engine = create_engine(DB_URL)

def save_data_safely(df, table_name, engine):
    """
    Deletes existing records for the same ticker & date before saving.
    Prevents duplicate rows in the database (Upsert Logic).
    """
    if df.empty:
        return

    with engine.connect() as conn:
        for _, row in df.iterrows():
            # Use CAST(x AS DATE) instead of x::date to avoid Python syntax errors
            delete_sql = text(f"""
                DELETE FROM {table_name} 
                WHERE ticker_symbol = :ticker 
                AND CAST(published_date AS DATE) = CAST(:date AS DATE)
            """)
            
            conn.execute(delete_sql, {
                "ticker": row['ticker_symbol'], 
                "date": row['published_date']
            })
            conn.commit()

    # Insert the fresh data
    df.to_sql(table_name, engine, if_exists='append', index=False)

def run_full_pipeline():
    # 1. DEFINE ASSETS & SOURCES
    tickers = ["NVDA", "AAPL", "TSLA", "BTC-USD", "GC=F", "SI=F"]
    
    sources = [
        {"name": "BBC Business", "url": "https://www.bbc.com/news/business", "tag": "h3"},
        {"name": "CNBC Markets", "url": "https://www.cnbc.com/markets/", "tag": "a"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/", "tag": "h3"}
    ]
    
    # 2. SCRAPE HEADLINES (Global Sentiment)
    print("--- Step 1: Scraping Multi-Source News ---")
    analyzer = SentimentIntensityAnalyzer()
    current_time = datetime.now()
    valid_headlines = []
    
    for source in sources:
        try:
            print(f"Scraping {source['name']}...")
            response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            raw_tags = soup.find_all(source['tag'])
            
            for h in raw_tags:
                text_content = h.text.strip()
                # Clean up filters
                if len(text_content) < 25 or "BBC is in multiple languages" in text_content:
                    continue
                
                valid_headlines.append({
                    "text": text_content,
                    "source": source['name']
                })
        except Exception as e:
            print(f"⚠️ Could not scrape {source['name']}: {e}")

    # 3. APPLY TO TICKERS & FETCH PRICES
    print(f"\n--- Step 2: Processing {len(tickers)} Assets ---")
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        
        # A. Prepare Sentiment Data
        sentiment_rows = []
        for item in valid_headlines:
            score = analyzer.polarity_scores(item['text'])['compound']
            # Only save if score is not 0 (Optional: remove this if you want neutral news)
            # if score == 0: continue 
            
            sentiment_rows.append({
                'published_date': current_time,
                'sentiment_score': score,
                'source_name': item['source'],
                'raw_text': item['text'],
                'sentiment_label': 'Positive' if score >= 0.05 else 'Negative' if score <= -0.05 else 'Neutral',
                'ticker_symbol': ticker
            })
            
        # B. Fetch Stock Price
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            
            if not hist.empty:
                price = hist['Close'].iloc[0]
                
                # Save Price (Upsert)
                stock_df = pd.DataFrame([{
                    'published_date': current_time,
                    'close_price': price,
                    'ticker_symbol': ticker
                }])
                save_data_safely(stock_df, 'stock_trends', engine)
                
                # Save Sentiment (Upsert logic optional, usually append is fine for news, but let's keep it clean)
                if sentiment_rows:
                    sent_df = pd.DataFrame(sentiment_rows)
                    sent_df.to_sql('market_sentiment', engine, if_exists='append', index=False)
                
                print(f"   ✅ Upserted {ticker}: ${price:,.2f} | Headlines: {len(sentiment_rows)}")
            else:
                print(f"   ⚠️ No price data found for {ticker}")
        except Exception as e:
            print(f"   ❌ Error for {ticker}: {e}")

if __name__ == "__main__":
    try:
        run_full_pipeline()
        print("\n✅ PIPELINE SUCCESS: Check your dashboard at localhost:8501")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")