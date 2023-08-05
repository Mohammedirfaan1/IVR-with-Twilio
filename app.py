import os
from flask import Flask, request, render_template
from twilio.twiml.voice_response import Gather, VoiceResponse
import requests



app = Flask(__name__)
app.debug = True  # Enable debug mode

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Twilio credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_phone_number = os.environ['TWILIO_PHONE_NUMBER']

# Alpha Vantage API key
alpha_vantage_api_key = os.environ['ALPHA_VANTAGE_API_KEY']


@app.route('/ivr', methods=['POST'])
def ivr():
    response = VoiceResponse()

    gather = Gather(input='speech dtmf', timeout=5, num_digits=1, action='/menu', method='POST')
    gather.say("Welcome to Stock Trading. Press 1 or say 'stock' to inquire about a stock price. Press 2 or say 'buy' to buy a stock.")
    response.append(gather)

    return str(response)

@app.route('/menu', methods=['POST'])
def menu():
    selected_option = request.form['SpeechResult'] if 'SpeechResult' in request.form else request.form['Digits']

    if selected_option == '1' or selected_option.lower() == 'stock':
        response = VoiceResponse()

        gather = Gather(input='speech dtmf', timeout=5, num_digits=4, action='/stock-price', method='POST')
        gather.say("Please enter the stock symbol using the keypad or say it out loud.")
        response.append(gather)
    elif selected_option == '2' or selected_option.lower() == 'buy':
        response = VoiceResponse()

        gather = Gather(input='speech dtmf', timeout=5, num_digits=4, action='/buy-stock', method='POST')
        gather.say("Please enter the stock symbol you want to buy using the keypad or say it out loud.")
        response.append(gather)
    else:
        response = VoiceResponse()
        response.say("Invalid option. Please try again.")
        response.redirect('/ivr')

    return str(response)

@app.route('/stock-price', methods=['POST'])
def stock_price():
    stock_symbol = request.form['SpeechResult'] if 'SpeechResult' in request.form else request.form['Digits']
    stock_price = fetch_stock_data(stock_symbol)

    if stock_price:
        response = VoiceResponse()
        response.say(f"The current price of {stock_symbol} is {stock_price:.2f} USD.")
    else:
        response = VoiceResponse()
        response.say(f"Sorry, the stock symbol {stock_symbol} is not found or there was an issue fetching the data.")

    return str(response)

@app.route('/buy-stock', methods=['POST'])
def buy_stock():
    stock_symbol = request.form['SpeechResult'] if 'SpeechResult' in request.form else request.form['Digits']
    stock_price = fetch_stock_data(stock_symbol)
    user_phone_number = request.form['From']
    user_balance = get_user_balance(user_phone_number)

    if stock_price and user_balance:
        purchase_amount = stock_price
        if user_balance >= purchase_amount:
            update_user_balance(user_phone_number, user_balance - purchase_amount)
            add_to_user_portfolio(user_phone_number, stock_symbol, purchase_amount)
            response = VoiceResponse()
            response.say(f"Stock purchase successful. {stock_symbol} bought at {stock_price:.2f} USD.")
        else:
            response = VoiceResponse()
            response.say("Sorry, you don't have sufficient funds for this purchase.")
    else:
        response = VoiceResponse()
        response.say(f"Sorry, the stock symbol {stock_symbol} is not found or there was an issue fetching the data.")

    return str(response)

def fetch_stock_data(stock_symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={alpha_vantage_api_key}"

    try:
        response = requests.get(url)
        data = response.json()
        if 'Global Quote' in data:
            stock_price = float(data['Global Quote']['05. price'])
            return stock_price
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def get_user_balance(phone_number):
    user_data = db.users.find_one({'phone_number': phone_number})
    return user_data['balance'] if user_data else None

def update_user_balance(phone_number, new_balance):
    db.users.update_one({'phone_number': phone_number}, {'$set': {'balance': new_balance}})

def add_to_user_portfolio(phone_number, stock_symbol, purchase_amount):
    db.users.update_one({'phone_number': phone_number}, {'$push': {'portfolio': {'stock_symbol': stock_symbol, 'purchase_amount': purchase_amount}}})

if __name__ == '__main__':
    app.run()
