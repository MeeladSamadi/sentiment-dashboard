import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 1. Database Connection
# Using SQLite for easier Cloud Deployment
DB_URL = "sqlite:///sentiment.db"
engine = create_engine(DB_URL)

st.set_page_config(page_title="AI Market Sentiment", layout="wide")

# 2. Sidebar & Setup
st.sidebar.title("Controls")

# REFRESH BUTTON (Always visible so you can initialize the DB)
if st.sidebar.button("🔄 Refresh Data Now"):
    with st.spinner("Fetching latest news & prices..."):
        try:
            # Import and run the pipeline logic
            from app import run_full_pipeline
            run_full_pipeline() 
            st.success("Done! Refreshing page...")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.header("Asset Selection")

# Initialize selected_ticker as None
selected_ticker = None

try:
    # Try to fetch tickers. If table doesn't exist, this fails silently.
    all_tickers = pd.read_sql("SELECT DISTINCT ticker_symbol FROM stock_trends", engine)
    selected_ticker = st.sidebar.selectbox("Choose Asset:", all_tickers['ticker_symbol'])
except:
    # If DB is empty, we just show a warning, but we DO NOT set selected_ticker to 'NVDA'
    st.sidebar.warning("⚠️ Database Empty. Click Refresh!")

# 3. Data Loading Function
def load_data(ticker):
    # FIX: Switched from '::date' (Postgres) to 'DATE()' (SQLite)
    query = f"""
    SELECT 
        DATE(p.published_date) as date, 
        AVG(s.sentiment_score) as avg_sentiment,
        MAX(p.close_price) as price
    FROM stock_trends p
    LEFT JOIN market_sentiment s ON DATE(p.published_date) = DATE(s.published_date)
    WHERE p.ticker_symbol = '{ticker}'
    GROUP BY 1 ORDER BY 1 ASC;
    """
    return pd.read_sql(query, engine)

# 4. Main Dashboard Logic
if selected_ticker:
    # ONLY try to load data if we actually have a selected ticker
    st.title(f"📊 {selected_ticker} Analysis")
    
    try:
        data = load_data(selected_ticker)

        if not data.empty:
            # --- TOP METRICS ---
            col1, col2 = st.columns(2)
            current_price = data['price'].iloc[-1]
            latest_sentiment = data['avg_sentiment'].iloc[-1]
            
            col1.metric(f"Current {selected_ticker} Price", f"${current_price:,.2f}")
            col2.metric("Latest AI Sentiment", f"{latest_sentiment:.2f}")

            # --- CHARTS ---
            fig = px.line(data, x='date', y='avg_sentiment', 
                          title=f'Daily Sentiment Score: {selected_ticker}', markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = px.area(data, x='date', y='price', 
                           title=f'{selected_ticker} Price Trend',
                           color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig2, use_container_width=True)

            # --- SAFE HAVEN COMPARISON ---
            st.divider()
            st.subheader("🛡️ Market Correlation: Tech vs. Precious Metals")
            
            # FIX: Updated to SQLite DATE() syntax
            comp_query = f"""
                SELECT DATE(published_date) as date, ticker_symbol, close_price 
                FROM stock_trends 
                WHERE ticker_symbol IN ('{selected_ticker}', 'GC=F', 'SI=F')
            """
            comp_df = pd.read_sql(comp_query, engine)

            if not comp_df.empty:
                comp_df['indexed_price'] = comp_df.groupby('ticker_symbol')['close_price'].transform(lambda x: (x / x.iloc[-1]) * 100)
                fig_idx = px.line(comp_df, x='date', y='indexed_price', color='ticker_symbol',
                                  title="Relative Performance Index (Normalized)")
                st.plotly_chart(fig_idx, use_container_width=True)

            # --- HEADLINE EXPLORER ---
            st.divider()
            st.subheader(f"📰 Recent Headlines for {selected_ticker}")
            
            label_filter = st.sidebar.multiselect(
                "Filter News by Sentiment:",
                options=['Positive', 'Neutral', 'Negative'],
                default=['Positive', 'Neutral', 'Negative']
            )
            
            raw_query = f"""
                SELECT raw_text, sentiment_label, sentiment_score, source_name 
                FROM market_sentiment 
                WHERE ticker_symbol = '{selected_ticker}'
                ORDER BY published_date DESC LIMIT 50
            """
            raw_data = pd.read_sql(raw_query, engine)
            
            if not raw_data.empty:
                filtered_headlines = raw_data[raw_data['sentiment_label'].isin(label_filter)]
                
                # Word Cloud
                st.subheader(f"☁️ Key Themes")
                if not filtered_headlines.empty:
                    text = " ".join(headline for headline in filtered_headlines['raw_text'])
                    custom_stopwords = {"BBC", "News", "Business", "market", "year", "said", "US", "price", "stocks"}
                    wc = WordCloud(width=800, height=300, background_color="white", stopwords=custom_stopwords).generate(text)
                    fig_wc, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig_wc)

                # News List
                st.write("### Latest News")
                for index, row in filtered_headlines.head(10).iterrows():
                    emoji = "🟢" if row['sentiment_label'] == 'Positive' else "🔴" if row['sentiment_label'] == 'Negative' else "⚪"
                    with st.expander(f"{emoji} {row['raw_text'][:80]}..."):
                        st.write(f"**Full Headline:** {row['raw_text']}")
                        st.write(f"**Source:** {row['source_name']}")
                        st.progress((row['sentiment_score'] + 1) / 2)
                        st.caption(f"Score: {row['sentiment_score']:.2f}")
    except Exception as e:
        st.error(f"Error loading data: {e}")

else:
    # 5. Welcome Screen (Empty State)
    st.title("🚀 Welcome to Your Sentiment Engine")
    st.info("The database is currently empty.")
    st.warning("⬅️ Please click **'Refresh Data Now'** in the sidebar to initialize the app!")
