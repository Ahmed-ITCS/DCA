import pandas as pd
import random
import logging
import os

# === Configuration ===
# Removed global basicConfig to allow dynamic logging per file
initial_balance = 1000

# === Pip Value Calculation ===
def get_pip_value(symbol, lot_size):
    if 'JPY' in symbol:
        return 1000 * lot_size
    elif symbol == 'XAUUSD':
        return 10 * lot_size
    else:
        return 10 * lot_size

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load a ticks/quotes file where the four items are
    Date, Time, Close, Other – separated by *whitespace or semicolons*.
    Returns a tidy DataFrame with DATE (datetime64) and CLOSE (float).
    """

    # 1️⃣  Read file using a regex separator: any run of whitespace OR ';'
    df = pd.read_csv(
        filepath,
        header=None,
        sep=r"[;\s]+",          # split on ; or whitespace
        engine="python",        # needed for regex sep
        usecols=[0, 1, 2, 3],   # ignore any extra junk columns
    )

    # 2️⃣  Make sure we have at least the three main columns
    if df.shape[1] < 3:
        raise ValueError(f"{filepath}: expected ≥3 columns, got {df.shape[1]}.")

    # 3️⃣  Label the columns we actually care about
    df.columns = ["Date", "Time", "CLOSE", "Other"]

    # 4️⃣  Combine date+time strings → datetime
    df["DATE"] = pd.to_datetime(
        df["Date"].astype(str) + df["Time"].astype(str),
        format="%Y%m%d%H%M%S",
        errors="coerce"      # bad rows become NaT (we’ll drop them)
    )

    # 5️⃣  Force CLOSE to numeric, coercing errors → NaN
    df["CLOSE"] = pd.to_numeric(df["CLOSE"], errors="coerce")

    # 6️⃣  Drop rows where either DATE or CLOSE couldn’t be parsed
    df = df.dropna(subset=["DATE", "CLOSE"])

    # 7️⃣  Keep only what the rest of the code needs
    return df[["DATE", "CLOSE"]].reset_index(drop=True)


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

        # Update profits for all open trades
        for t in open_trades:
            entry_price = t['entry']
            if t['direction'] == 'buy':
                t['profit'] = (price - entry_price) * pip_value
            else:
                t['profit'] = (entry_price - price) * pip_value

        # Calculate total floating profit
        total_profit = sum(t['profit'] for t in open_trades)

        # Check if total profit reached target → close all trades
        if open_trades and total_profit >= profit_target:
            balance += total_profit
            open_trades = []
            direction = random.choice(['buy', 'sell'])  # New random direction

        # If last trade loss exceeds loss_trigger → add another trade same direction
        elif open_trades:
            last_trade = open_trades[-1]
            if last_trade['profit'] <= -loss_trigger:
                open_trades.append({'entry': price, 'direction': direction, 'profit': 0})

        # If no open trades → open the first trade
        if not open_trades:
            open_trades.append({'entry': price, 'direction': direction, 'profit': 0})

        # Track monthly performance
        if month not in monthly_results:
            monthly_results[month] = {
                'start_balance': balance,
                'final_balance': balance
            }
        monthly_results[month]['final_balance'] = balance + total_profit  # Include floating profit

    # Convert monthly results to list
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


def full_year_parameter_sweep(filepaths, symbol="EURUSD"):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    for filepath in filepaths:
        filename_base = os.path.basename(filepath).split('.')[0]
        log_filename = f'{filename_base}_backtest.log'

        if logger.hasHandlers():
            logger.handlers.clear()

        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        logger.info(f"Processing file: {filepath}")
        df = load_data(filepath)

        # Track monthly results for this file
        all_monthly_results = {}

        for lot in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:
            for loss_trigger in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
                for profit_target in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                    monthly_results = simulate_monthly_tracking(df, lot, loss_trigger, profit_target, symbol)
                    for res in monthly_results:
                        month = res['month']
                        if month not in all_monthly_results:
                            all_monthly_results[month] = []
                        all_monthly_results[month].append(res)
                    logger.info(f"Done: Lot {lot}, Loss {loss_trigger}, TP {profit_target} for {filepath}")

        # Save results by month
        for month, results in all_monthly_results.items():
            out_path = f'{filename_base}_{month}_results.csv'
            pd.DataFrame(results).to_csv(out_path, index=False)
            logger.info(f"Saved monthly results to: {out_path}")

# === Execute ===
if __name__ == '__main__':
    data_files = [
        '/Users/ahmed/Desktop/backtest/DATA1.csv',
        '/Users/ahmed/Desktop/backtest/DATA2.csv',
        '/Users/ahmed/Desktop/backtest/DATA3.csv',
        '/Users/ahmed/Desktop/backtest/DATA4.csv',
        '/Users/ahmed/Desktop/backtest/DATA5.csv',
        '/Users/ahmed/Desktop/backtest/DATA6.csv',
        '/Users/ahmed/Desktop/backtest/DATA7.csv',
        '/Users/ahmed/Desktop/backtest/DATA8.csv',
        '/Users/ahmed/Desktop/backtest/DATA9.csv',
        '/Users/ahmed/Desktop/backtest/DATA10.csv',
        '/Users/ahmed/Desktop/backtest/DATA11.csv',
        '/Users/ahmed/Desktop/backtest/DATA12.csv'
    ]
    full_year_parameter_sweep(data_files, 'EURUSD')
