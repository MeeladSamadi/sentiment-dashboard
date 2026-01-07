# 📈 AI Financial Intelligence Engine

A full-stack financial dashboard that correlates **real-time news sentiment** with **stock price movements**. 

This application scrapes live global business news, analyzes it using NLP (VADER), and visualizes how market sentiment impacts assets like **NVIDIA, Apple, Bitcoin, and Gold**.

## 🚀 Key Features

* **Multi-Asset Tracking:** Monitors Tech Stocks (NVDA, AAPL, TSLA), Crypto (BTC), and Commodities (Gold, Silver) simultaneously.
* **AI Sentiment Analysis:** Uses Natural Language Processing (VADER) to score headlines from -1 (Negative) to +1 (Positive).
* **Self-Healing Data Pipeline:** Implements "Upsert" logic (Update/Insert) to prevent duplicate data, ensuring a clean database regardless of how often the scraper runs.
* **Interactive Dashboard:** Built with Streamlit & Plotly to allow dynamic filtering, price overlays, and deep-dives into specific news sources.
* **Multi-Source Scraping:** Aggregates news from BBC Business, CNBC, and Yahoo Finance.

## 🛠️ Tech Stack

* **Frontend:** Streamlit, Plotly Express, WordCloud
* **Backend:** Python 3.10+
* **Database:** SQLite (Cloud-Ready) / PostgreSQL (Compatible)
* **AI/NLP:** VADER Sentiment Analysis
* **Data Sources:** `yfinance` (Market Data), `BeautifulSoup` (Web Scraping)

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/sentiment-dashboard.git](https://github.com/yourusername/sentiment-dashboard.git)
    cd sentiment-dashboard
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## ⚡ How to Run

### 1. Run the Data Pipeline
This script scrapes the latest news and updates the stock prices in the database.
```bash
python app.py
