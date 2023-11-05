#To run the app, open cmd in the folder where app.py is downloaded and run the command: python -m streamlit run app.py
#Alternatively use the link: https://technical-analysis-of-stocks.streamlit.app/

import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
import streamlit as st
import os
import warnings
warnings.filterwarnings("ignore")


st.title('Techinical Analysis')

option = st.selectbox(
     'Select Stock',
     ('MSFT', 'AMZN', 'GOOGL','NFLX','META','SMSN.IL','ADANIPOWER.NS'))
#user_input=st.text_input('Enter Stock Name','MSFT')
user_input1=st.text_input('Enter Start Date ','2018-10-7')
user_input2=st.text_input('Enter End Date ','2023-11-3')


dataF = yf.download(option, start=user_input1, end=user_input2, interval='1d')


st.subheader("Data description")
st.write(dataF.describe())


st.subheader("My Strategy")
st.write("In my trading strategy, I've integrated three potent technical indicators to optimize investment decisions. The first component revolves around open-close patterns. By scrutinizing daily price fluctuations, I pinpoint bullish and bearish patterns,timing my market entries and exits in response to short-term price dynamics.Adding depth to my strategy is the Relative Strength Index (RSI), a momentum-driven indicator. It aids in deciphering market sentiment, sounding the alarm when RSI values surpass 70, suggesting overbought conditions and a potential sell opportunity. Conversely, RSI values below 30 indicate oversold conditions, signaling potential buying opportunities.However, the backbone of my strategy lies in the moving averages, particularly the 5-day and 20-day variants. These averages provide a broader perspective on price trends. A bullish crossover, where the 5-day average exceeds the 20-day average, triggers consideration of a buying position. Conversely, a bearish crossover, with the 5-day average falling below the 20-day average, prompts contemplation of a sell position.")
#-------------------------------------------------------------------------------------------------------------

def signal_generator_open_close(df):
    open = df.Open.iloc[-1]
    close = df.Close.iloc[-1]
    previous_open = df.Open.iloc[-2]
    previous_close = df.Close.iloc[-2]
    
    # Bearish Pattern
    if (open>close and 
    previous_open<previous_close and 
    close<=previous_open and
    open>=previous_close):
        return 1

    # Bullish Pattern
    elif (open<close and 
        previous_open>previous_close and 
        close>previous_open and
        open<previous_close):
        return 2
    
    # No clear pattern
    else:
        return 0

open_close_signal = []
open_close_signal.append(0)
for i in range(1,len(dataF)):
    df = dataF[i-1:i+1]
    open_close_signal.append(signal_generator_open_close(df))

#------------------------------------------------------------------------------------------------------------
#Moving average techinical indicator

ma_signal = []

# Calculate moving averages and add them to the DataFrame
dataF["short_ma"] = dataF["Close"].rolling(window=5).mean()
dataF["long_ma"] = dataF["Close"].rolling(window=20).mean()

# Iterate through the DataFrame rows
for index, row in dataF.iterrows():
    short_ma = row['short_ma']
    long_ma = row['long_ma']
    
    if short_ma>long_ma:
        if (short_ma -long_ma)>=short_ma/100:
            ma_signal.append(2)
        else:
            ma_signal.append(0)
    elif short_ma<long_ma:
        if (long_ma-short_ma)>=short_ma/100:
            ma_signal.append(1)
        else:
            ma_signal.append(0)
    else:
        ma_signal.append(0)
        
#----------------------------------------------------------------------------------------------------------------
#RSI Techinical indicator

dataF['RSI'] = ta.momentum.RSIIndicator(dataF['Close']).rsi()
rsi_signals = []
for i in range(len(dataF)):
    if dataF['RSI'][i] > 55:  # Overbought RSI
        s= 1  # Bearish signal
    elif dataF['RSI'][i] < 40:  # Oversold RSI
        s = 2  # Bullish signal
    else:
        s=0
    rsi_signals.append(s)
    
#----------------------------------------------------------------------------------------------------------------
signal=[]
for i in range(0,len(open_close_signal)):
    if ma_signal[i]==1:
        signal.append(1)
    elif ma_signal[i]==2:
        signal.append(2)
    else:
        signal.append(0)
        
dataF['signal']=signal


#-------------------------------------------------------------------------------------------------------------
## Initialising Virtual Portfolio

balance = 100000  # Starting cash balance
b=balance
shares_held = 0
position_value = 0
total_profit = 0
time_to_buy=1
trades = []
actual_trade=[]
bal=[]
drawdowns=[]
revenue=0
no_trades=0
# Define trading strategy
def trading_strategy(signal, cash_balance, price):
    global no_trades,revenue,actual_trade,balance,shares_held,total_profit,position_value,time_to_buy
    if signal == 2:  
        if time_to_buy==0:
         # Sell when a bearish signal is generated
            time_to_buy=1
            if revenue!=0:
                drawdowns.append((revenue-cash_balance)*100/revenue)
            elif revenue==0:
                drawdowns.append((b-cash_balance)*100/b)
            revenue = shares_held * price
            cash_balance += revenue
            balance=cash_balance
            total_profit += revenue - position_value
            shares_held = 0
            position_value = 0
            trades.append((price, shares_held, 'Sell'))
            actual_trade.append(2)
            bal.append(balance)
            no_trades+=1
        else:
            actual_trade.append(0)
            bal.append(balance)
            
    elif signal==1:
        if cash_balance>price:
            shares_to_buy = (cash_balance// price)
            cost = shares_to_buy * price
            cash_balance -= cost
            balance=cash_balance
            shares_held += shares_to_buy
            position_value += shares_to_buy* price
            trades.append((price, shares_to_buy, 'Buy'))
            time_to_buy=0
            actual_trade.append(1)
            bal.append(balance)
            no_trades+=1
            #now you can sell
        else:
            actual_trade.append(0)
            bal.append(balance)
    
    else:
        actual_trade.append(0)
        bal.append(balance)

# Backtest the strategy
for index, row in dataF.iterrows():
    signal = row['signal']
    price = row['Close']
    trading_strategy(signal,balance, price)

# Calculate performance metrics
total_returns = total_profit*100 /b
# Calculate Sharpe ratio and other metrics
dataF['Daily Return'] = dataF['Close'].pct_change()
average_daily_return = dataF['Daily Return'].mean()
std_dev_daily_return = dataF['Daily Return'].std()
risk_free_rate = 0.01  # chosen risk-free rate
sharpe_ratio = (average_daily_return - risk_free_rate) / std_dev_daily_return
AAN=((balance/b)**(1/5)-1)*100

# Print or display the results and metrics

st.subheader("Metrics for my Portfolio")
st.write("Initial Cash Balance:",b)
st.write("Total Profit: $", total_profit)
st.write("Total Returns: ", total_returns,"%")
st.write("Final Portfolio Value:",balance)
st.write("Sharpe_ratio: ",sharpe_ratio)
st.write("No. of executed trades:",no_trades)
st.write("Maximum drawdown:",max(drawdowns))
st.write("Average Annualised return:",AAN,"%")


dataF['actual_trade']=actual_trade

#-------------------------------------------------------------------------------------------------------------
#Creating a .csv file containing the buying and selling points

signals_df = pd.DataFrame({
    'Date': dataF.index,
    'Buy Signal': dataF['actual_trade'] == 1,
    'Sell Signal': dataF['actual_trade'] == 2,
    'Position Open': 0,  # Initialize to 0
    'Portfolio Value': 0  # Initialize to 0
})

# Initialize variables to keep track of position and portfolio value
position = 0 #no of stocks
portfolio_value = b  # Initialize with your initial portfolio value
cash=b
# Update the 'Position Open' and 'Portfolio Value' columns in the DataFrame
position = 0
for i in range(len(signals_df)):
    if dataF['actual_trade'][i]==1:
        position += cash// dataF['Close'][i]
        cash-=position*dataF['Close'][i]
    elif dataF['actual_trade'][i]==2:
        portfolio_value = position * dataF['Close'][i]
        cash=position * dataF['Close'][i]
        position = 0
    signals_df['Position Open'][i] = position
    signals_df['Portfolio Value'][i] = portfolio_value
    
# Set the date format for the 'Date' column
date_format = '%Y-%m-%d'
signals_df['Date'] = signals_df['Date'].dt.strftime(date_format)

file_path = 'buy_sell_signals.csv'

# Check if the file exists and remove it if it does
if os.path.exists(file_path):
    os.remove(file_path)

# Save the DataFrame to a CSV file
signals_df.to_csv(file_path, index=False)


#-------------------------------------------------------------------------------------------------------------
# Create plot of Stock Closing Price with Buy/Sell Signals

fig = go.Figure()
buying_points = dataF[dataF['actual_trade'] == 1].index
selling_points = dataF[dataF['actual_trade'] == 2].index
y=dataF.loc[buying_points]
# Add a trace for the closing price
fig.add_trace(go.Scatter(x=dataF.index, y=dataF['Close'], mode='lines', name='Closing Price', line=dict(color='white')))

# Overlay green dots for selling points
fig.add_trace(go.Scatter(x=selling_points, y=dataF.loc[selling_points]['Close'], mode='markers', name='Selling Points', marker=dict(color='green', size=8, symbol='circle')))

# Overlay red dots for buying points
fig.add_trace(go.Scatter(x=buying_points, y=dataF.loc[buying_points]['Close'], mode='markers', name='Buying Points', marker=dict(color='red', size=5, symbol='circle')))

# Customize the layout (add title, labels, etc.)
fig.update_layout(
    title='Stock Closing Price with Buy/Sell Signals',
    xaxis_title='Date',
    yaxis_title='Closing Price',
    showlegend=True,
    xaxis=dict(
        type='date',
        tickformat='%b-%Y',  # Format for month and year (e.g., Nov-2023)

    )
)

#-------------------------------------------------------------------------------------------------------------

st.plotly_chart(fig)
st.write("Please select dark theme from the top right corner (under settings) to see the graphs properly")
st.write("Please use the zoom and pan functionality (in the top right of the graph) to navigate better")
fig = go.Figure()

fig.add_trace(go.Scatter(x=dataF.index, y=bal
                         , mode='lines', name='Balance', line=dict(color='white')))
# fig.add_trace(go.Scatter(x=dataF.index, y=bal
#                          , name='Balance', mode='markers', marker=dict(color='green', size=5, symbol='circle')))
fig.update_layout(
    title='Total cash balance',
    xaxis_title='Date',
    yaxis_title='Closing Price',
    showlegend=True,
    xaxis=dict(
        type='date',
        tickformat='%b-%Y',  # Format for month and year (e.g., Nov-2023)

    )
)
st.plotly_chart(fig)

#-------------------------------------------------------------------------------------------------------------

profit=[]
for i in range(len(bal)):
    prof=bal[i]-b
    if(prof>=0):
        profit.append(prof)
    else:
        profit.append(0)

fig = go.Figure()

fig.add_trace(go.Scatter(x=dataF.index, y=profit
                         , mode='lines', name='Closing Price', line=dict(color='white')))
fig.update_layout(
    title='Total Profit',
    xaxis_title='Date',
    yaxis_title='Closing Price',
    showlegend=True,
    xaxis=dict(
        type='date',
        tickformat='%b-%Y',  # Format for month and year (e.g., Nov-2023)

    )
)
st.plotly_chart(fig)


#-------------------------------------------------------------------------------------------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(x=selling_points, y=drawdowns
                         , mode='markers', name='drawdowns',  marker=dict(color='green', size=8, symbol='circle')))
fig.add_trace(go.Scatter(x=selling_points, y=drawdowns
                         , mode='lines', name='drawdowns',  marker=dict(color='white', size=5)))
              # fig.add_trace(go.Scatter(x=dataF.index, y=bal
#                          , name='Balance', mode='markers', marker=dict(color='green', size=5, symbol='circle')))
fig.update_layout(
    title='Drawdowns',
    xaxis_title='Date',
    yaxis_title='Drawdowns',
    showlegend=True,
    xaxis=dict(
        type='date',
        tickformat='%b-%Y',  # Format for month and year (e.g., Nov-2023)

    )
)
st.plotly_chart(fig)

#-------------------------------------------------------------------------------------------------------------
st.write("The .csv file containing the buying and selling points is created in the app.py directory")
