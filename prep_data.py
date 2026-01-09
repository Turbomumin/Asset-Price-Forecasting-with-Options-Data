import yfinance as yf
import pandas as pd

def fetch_option_chain(symbol):
    """Fetch full option chain for all expiries for one symbol."""
    ticker = yf.Ticker(symbol)
    expiries = ticker.options

    all_chains = []

    for exp in expiries:
        try:
            chain = ticker.option_chain(exp)
        except Exception as e:
            print(f"Failed to load expiry {exp}: {e}")
            continue

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        # Attach expiry as datetime
        calls["expiry"] = pd.to_datetime(exp)
        puts["expiry"] = pd.to_datetime(exp)

        # Mark option type
        calls["option_type"] = "C"
        puts["option_type"] = "P"

        all_chains.append(calls)
        all_chains.append(puts)

    if not all_chains:
        raise ValueError("No option chains loaded")

    options_df = pd.concat(all_chains, ignore_index=True)

    # Days to expiry
    today = pd.Timestamp.today().normalize()
    options_df["days_to_expiry"] = (options_df["expiry"] - today).dt.days

    # Remove unnecessary columns
    cols_to_drop = [
        "contractSize",
        "currency",
        "percentChange",
        "change"
    ]
    options_df = options_df.drop(columns=[c for c in cols_to_drop if c in options_df.columns])

    return options_df

def chain_preprocess(options_df, spot):
    df = options_df.copy()

    print(f"Shape before filtering: {df.shape}")

    # Ensure lastTradeDate is datetime and timezone naive
    s = pd.to_datetime(df["lastTradeDate"], utc=True, errors="coerce")
    df["lastTradeDate"] = s.dt.tz_localize(None)

    # Add mid quote and moneyness
    df["mid_price"] = (df["ask"] + df["bid"])/2
    df["spread"] = (df["ask"] - df["bid"])

    # Keep only options traded in the last 2 days
    time_cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=2)
    df = df[df["lastTradeDate"] >= time_cutoff]

    # Filter out undesirable values
    volume_cutoff = 10
    Bid_Ask_Cutoff = 0.01
    days_cutoff = 0.01

    df = df[df["volume"] >= volume_cutoff]
    print(f"Options with less than {volume_cutoff} volune discarded. New shape is {df.shape}")

    df = df[df["bid"] >= Bid_Ask_Cutoff]
    print(f"Options with no bid prices discarded. New shape is {df.shape}")

    df = df[df["ask"] >= Bid_Ask_Cutoff]
    print(f"Options with no ask prices discarded. New shape is {df.shape}")

    df = df[df["days_to_expiry"] >= days_cutoff]
    print(f"Options expiring today discarded. New shape is {df.shape}")

    print(f"Shape after filtering: {df.shape}")

    options_df = df
    return options_df


def fetch_spot(symbol):
    """Fetch current spot price for the underlying."""
    ticker = yf.Ticker(symbol)
    try:
        spot = ticker.fast_info["last_price"]
    except Exception:
        hist = ticker.history(period="1d")
        spot = float(hist["Close"].iloc[-1])
    return spot
