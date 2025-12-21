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

    # Keep only options traded in the last 2 days
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=2)
    df = df[df["lastTradeDate"] >= cutoff]

    print(f"Shape after filtering: {df.shape}")

    # Add mid quote and moneyness
    df["mid"] = (df["bid"] + df["ask"]) / 2
    df["spread"] = (df["ask"] - df["bid"])
    df["moneyness"] = df["strike"] / spot

    options_df = df
    return df


def fetch_spot(symbol):
    """Fetch current spot price for the underlying."""
    ticker = yf.Ticker(symbol)
    try:
        spot = ticker.fast_info["last_price"]
    except Exception:
        hist = ticker.history(period="1d")
        spot = float(hist["Close"].iloc[-1])
    return spot