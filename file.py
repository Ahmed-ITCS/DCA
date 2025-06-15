import pandas as pd
import random
import logging

# === Configuration ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df

# === Simulate One Year and Track Monthly Performance ===
def simulate_monthly_tracking(df, lot_size, loss_trigger, profit_target, symbol="EURUSD"):
    balance = initial_balance
    direction = random.choice(['buy', 'sell'])
    open_trades = []
    pip_value = get_pip_value(symbol, lot_size)

    monthly_results = {}

    for i in range(1, len(df)):
        row = df.iloc[i]
        price = row['CLOSE']
        date = row['DATE']
        month = date.strftime('%Y-%m')

        # Update profits
        for t in open_trades:
            entry_price = t['entry']
            if t['direction'] == 'buy':
                t['profit'] = (price - entry_price) * pip_value
            else:
                t['profit'] = (entry_price - price) * pip_value

        # Close profitable trades
        remaining_trades = []
        for t in open_trades:
            if t['profit'] >= profit_target:
                balance += t['profit']
                direction = random.choice(['buy', 'sell'])
            else:
                remaining_trades.append(t)
        open_trades = remaining_trades

        # Open new trade logic
        if len(open_trades) == 0:
            open_trades.append({'entry': price, 'direction': direction, 'profit': 0})
        else:
            last_trade = open_trades[-1]
            if last_trade['profit'] <= -loss_trigger:
                open_trades.append({'entry': price, 'direction': direction, 'profit': 0})

        # Track monthly performance
        if month not in monthly_results:
            monthly_results[month] = {
                'start_balance': balance,
                'final_balance': balance
            }
        monthly_results[month]['final_balance'] = balance

    # Add floating profit to the last month's balance
    final_profit = sum([t['profit'] for t in open_trades])
    if monthly_results:
        last_month = max(monthly_results)
        monthly_results[last_month]['final_balance'] += final_profit

    # Convert results
    result_list = []
    for month, data in monthly_results.items():
        profit = data['final_balance'] - data['start_balance']
        result_list.append({
            'month': month,
            'lot_size': lot_size,
            'loss_trigger': loss_trigger,
            'profit_target': profit_target,
            'net_profit': round(profit, 2),
            'final_balance': round(data['final_balance'], 2)
        })

    return result_list

# === Run for All Parameter Combinations ===
def full_year_parameter_sweep(filepath, symbol="EURUSD"):
    logging.info(f"Running full-year parameter sweep for {symbol}")
    df = load_data(filepath)

    all_results = []

    for lot in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:
        for loss_trigger in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
            for profit_target in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                monthly_results = simulate_monthly_tracking(df, lot, loss_trigger, profit_target, symbol)
                all_results.extend(monthly_results)
                logging.info(f"Done: Lot {lot}, Loss {loss_trigger}, TP {profit_target}")

    result_df = pd.DataFrame(all_results)
    result_df.to_csv('yearly_split_monthly_results.csv', index=False)
    logging.info("Saved all results to yearly_split_monthly_results.csv")

# === Execute ===
if __name__ == '__main__':
    full_year_parameter_sweep('DATA.csv', 'EURUSD')  # Replace 'DATA.csv' with your actual file path
