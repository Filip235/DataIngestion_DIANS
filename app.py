from flask import Flask, request, render_template, jsonify
import yfinance as yf
import datetime
import requests
import json
import pandas as pd
from yahooquery import Screener
from confluent_kafka import Producer, Consumer
import psycopg2
from sklearn.linear_model import LinearRegression
import joblib
import numpy as np
import os

DB_CONFIG = {
    "dbname": "DataBase",
    "user": "postgres",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

def train_model(ticker):
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.today() - datetime.timedelta(days=5 * 365)).strftime('%Y-%m-%d')
        history = stock.history(start=start_date, end=end_date)

        if history.empty:
            print(f"⚠ No historical data found for {ticker}")
            return

        history["Previous Close"] = history["Close"].shift(1)
        history.dropna(inplace=True)

        history["Close"] = history["Close"].replace('[\$,]', '', regex=True).astype(float)
        history["Previous Close"] = history["Previous Close"].replace('[\$,]', '', regex=True).astype(float)
        history.dropna(inplace=True)

        X = history[["Previous Close"]]
        y = history["Close"]

        model = LinearRegression()
        model.fit(X, y)

        model_filename = os.path.join("models", f"{ticker}_price_prediction_model.pkl")
        joblib.dump(model, model_filename)
        print(f"Model trained and saved for {ticker} at {model_filename}.")
    except Exception as e:
        print(f"❌ Error training model for {ticker}: {e}")


def predict_price(ticker, previous_close):
    try:
        model_filename = os.path.join("models", f"{ticker}_price_prediction_model.pkl")
        if not os.path.exists(model_filename):
            train_model(ticker)

        model = joblib.load(model_filename)
        prediction = model.predict([[previous_close]])
        return prediction[0]
    except Exception as e:
        print(f"❌ Error predicting price for {ticker}: {e}")
        return None

import os

def connect_db():
    return psycopg2.connect(**DB_CONFIG)


def insert_company_data(company_name, stock_price):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        stock_price = float(stock_price)
        query = """
        INSERT INTO companies (name, stock_price)
        VALUES (%s, %s)
        ON CONFLICT (name) 
        DO UPDATE SET stock_price = EXCLUDED.stock_price;
        """

        cursor.execute(query, (company_name, stock_price))
        conn.commit()
        cursor.close()
        conn.close()

        print(f"Successfully Inserted/Updated {company_name}: {stock_price}$")

    except Exception as e:
        print(f"Database Insert Error!: {e}")


KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "stock_prices"

producer = Producer({"bootstrap.servers": KAFKA_BROKER})

consumer = Consumer({
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "flask-consumer-group",
    "auto.offset.reset": "earliest"
})
consumer.subscribe([KAFKA_TOPIC])

app = Flask(__name__)


def get_all_tickers():
    """Fetch all stock tickers from Yahoo Finance for major exchanges."""
    screener = Screener()
    tickers = {}
    exchanges = ["most_actives", "day_gainers", "day_losers", "nasdaq", "nyse", "tsx", "london"]

    for exchange in exchanges:
        try:
            data = screener.get_screeners(exchange, count=100)
            if exchange in data and "quotes" in data[exchange]:
                for stock in data[exchange]["quotes"]:
                    tickers[stock["symbol"]] = stock.get("shortName", stock["symbol"])
        except Exception as e:
            print(f"Error fetching {exchange}: {e}")

    return tickers


COMPANIES = get_all_tickers()


def get_historical_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.today() - datetime.timedelta(days=5 * 365)).strftime('%Y-%m-%d')

        history = stock.history(start=start_date, end=end_date)

        if history.empty:
            print(f"⚠ No historical data found for {ticker}")
            return None

        history = history.reset_index()
        history["Date"] = pd.to_datetime(history["Date"])

        history = history[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends']]

        history = history.sort_index(ascending=False)

        history["Date"] = history["Date"].dt.strftime('%Y-%m-%d')

        history["Close"] = history["Close"].replace('[\$,]', '', regex=True).astype(float)

        history["Close_Formatted"] = history["Close"].apply(lambda x: f"${x:.2f}")

        return history
    except Exception as e:
        print(f"❌ Error fetching historical data: {e}")
        return None


def get_real_time_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]

        stock_price = round(price, 2)
        insert_company_data(ticker, stock_price)

        producer.produce(KAFKA_TOPIC, key=ticker, value=json.dumps({"ticker": ticker, "price": stock_price}))
        producer.flush()

        return f"{stock_price}$"
    except Exception as e:
        print(f"❌ Yahoo Finance Error: {e}")
        return "Error"


def consume_kafka():
    """Consume real-time stock data from Kafka."""
    try:
        msg = consumer.poll(1.0)
        if msg is None:
            return "Waiting for data..."
        if msg.error():
            return f"Consumer error: {msg.error()}"

        data = json.loads(msg.value().decode("utf-8"))
        return f"{data['ticker']}: {data['price']}"
    except Exception as e:
        return f"Error consuming Kafka data: {e}"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        ticker = request.form["ticker"]

        historical_data = get_historical_data(ticker)
        if historical_data is None or historical_data.empty:
            return jsonify({"error": f"No historical data found for {ticker}."})

        most_recent_close = historical_data.iloc[0]["Close"]
        if pd.isna(most_recent_close):
            return jsonify({"error": f"No valid closing price found for {ticker}."})

        prediction = predict_price(ticker, most_recent_close)
        if prediction:
            return jsonify({"prediction": prediction})
        else:
            return jsonify({"error": "Unable to make prediction."})
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route("/", methods=["GET", "POST"])
def index():
    historical_data = None
    real_time_price = "N/A"
    kafka_data = "Waiting for data..."
    selected_ticker = ""
    chart_data = None

    if request.method == "POST":
        selected_ticker = request.form["ticker"]
        df = get_historical_data(selected_ticker)

        if df is not None:
            # Use the formatted column for display
            df_display = df.copy()
            df_display["Close"] = df_display["Close_Formatted"]
            chart_data = df.to_dict(orient="records")

        real_time_price = get_real_time_price(selected_ticker)
        kafka_data = consume_kafka()

    return render_template("index.html",
                           historical_data=df_display.to_html() if df is not None else None,
                           real_time_price=real_time_price,
                           kafka_data=kafka_data,
                           selected_ticker=selected_ticker,
                           companies=COMPANIES,
                           chart_data=json.dumps(chart_data))

if __name__ == "__main__":
    app.run(debug=True)



