import pandas as pd
import random

# === Parameters ===
initial_balance = 1000

# === Pip Value Calculation ===
def get_pip_value(symbol, lot_size):
    if 'JPY' in symbol:
        return 1000 * lot_size
    elif symbol == 'XAUUSD':
        return 10 * lot_size
    else:
        return 10 * lot_size

# === Load Data ===
def load_data(filepath):
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# === Simulate Strategy ===
def simulate(df, lot_size, loss_trigger, profit_target, symbol="EURUSD"):
    balance = initial_balance
    direction = random.choice(['buy', 'sell'])
    open_trades = []

    pip_value = get_pip_value(symbol, lot_size)

    for i in range(1, len(df)):
        price = df.iloc[i]['Close']

        # Update profits
        for t in open_trades:
            entry_price = t['entry']
            if t['direction'] == 'buy':
                t['profit'] = (price - entry_price) * pip_value
            else:
                t['profit'] = (entry_price - price) * pip_value

        # Close trades that hit profit target
        closed_profits = 0
        remaining_trades = []
        for t in open_trades:
            if t['profit'] >= profit_target:
                balance += t['profit']
                direction = random.choice(['buy', 'sell'])  # reset direction after win
            else:
                remaining_trades.append(t)
        open_trades = remaining_trades

        # Open new trade if none are open
        if len(open_trades) == 0:
            open_trades.append({'entry': price, 'direction': direction, 'profit': 0})
        else:
            last_trade = open_trades[-1]
            if last_trade['profit'] <= -loss_trigger:
                open_trades.append({'entry': price, 'direction': direction, 'profit': 0})

    # Final floating profit
    final_profit = sum([t['profit'] for t in open_trades])
    final_balance = balance + final_profit
    net_profit = final_balance - initial_balance
    return round(net_profit, 2), round(final_balance, 2)

# === Optimization Runner ===
def optimize(csv_path, symbol):
    df = load_data(csv_path)

    results = []
    for lot in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:
        for loss_trigger in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
            for profit_target in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                net_profit, net_capital = simulate(df, lot, loss_trigger, profit_target, symbol)
                results.append({
                    'lot_size': lot,
                    'loss_trigger': loss_trigger,
                    'profit_target': profit_target,
                    'year_end_net_profit': net_profit,
                    'year_end_net_capital': net_capital
                })

    result_df = pd.DataFrame(results)
    result_df.sort_values(by='year_end_net_profit', ascending=False, inplace=True)
    print(result_df.head(10))
    result_df.to_csv('year_end_optimization.csv', index=False)

# === Run It ===
optimize('DATA.csv', 'EURUSD')  # replace with your actual file name
