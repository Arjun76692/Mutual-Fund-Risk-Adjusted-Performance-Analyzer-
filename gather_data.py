from mftool import Mftool
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import time

mf = Mftool()

def all_schem_codes():
    all_scheme_codes = mf.get_scheme_codes()
    master_funds = pd.DataFrame(all_scheme_codes.items())
    master_funds.columns = ['Scheme_Code', 'Scheme_Name']
    master_funds = master_funds[1:]
    master_funds.reset_index(drop=True, inplace=True)
    return master_funds

def get_scheme_details(code):
    details = mf.get_scheme_details(code)
    return details, type(details)

def get_group_scheme_details(df):
    data = []
    for code in df['Scheme_Code']:
        details = mf.get_scheme_details(code)
        data.append(details)
    agg_df = pd.DataFrame(data)
    agg_df['start_date'] = pd.to_datetime(agg_df['scheme_start_date'].apply(lambda x: x['date']), dayfirst=True)
    agg_df['nav'] = agg_df['scheme_code'].apply(lambda code: mf.get_scheme_quote(str(code))['nav'])
    agg_df['nav'] = agg_df['nav'].astype(float)
    return agg_df

def current_nav(code):
    nav = mf.get_scheme_quote(code)['nav']
    return nav

def get_historical_nav(scheme_code):
    hist = mf.get_scheme_historical_nav(scheme_code)
    if not hist or not isinstance(hist, dict):
        return pd.DataFrame(columns=["date", "nav"])
    hist_list = list(hist.values())
    if not hist_list:
        return pd.DataFrame(columns=["date", "nav"])
    hist_df = pd.DataFrame(hist_list)
    hist_df["date"] = pd.to_datetime(hist_df["date"], dayfirst=True, errors="coerce")
    hist_df["nav"] = pd.to_numeric(hist_df["nav"], errors="coerce")
    hist_df = hist_df.dropna(subset=["date", "nav"]).sort_values("date")
    hist_df.set_index("date", inplace=True)
    return hist_df

def compute_cagr_from_hist(hist_df, yrs):
    if hist_df.empty:
        return np.nan
    last_date = hist_df.index.max()
    start_date = last_date - pd.DateOffset(years=yrs)
    sub = hist_df[hist_df.index >= start_date]['nav'].dropna()
    if len(sub) < 2:
        return np.nan
    start_nav = sub.iloc[0]
    end_nav = sub.iloc[-1]
    if start_nav <= 0:
        return np.nan
    return (end_nav / start_nav) ** (1 / yrs) * 100 - 100

def compute_fund_metrics(group_df):
    rows = []
    for _, row in group_df.iterrows():
        code = row['scheme_code']
        name = row['scheme_name']
        start_date = row['start_date']
        nav = row['nav']
        hist_df = get_historical_nav(code)
        cagr_3 = compute_cagr_from_hist(hist_df, 3)
        cagr_5 = compute_cagr_from_hist(hist_df, 5)
        cagr_10 = compute_cagr_from_hist(hist_df, 10)
        rows.append({
            'scheme_code': code,
            'scheme_name': name,
            'start_date': start_date,
            'nav': nav,
            'cagr_3yrs': cagr_3,
            'cagr_5yrs': cagr_5,
            'cagr_10yrs': cagr_10
        })
    final_df = pd.DataFrame(rows)
    return final_df

def compute_sharpe_and_drawdown(hist_nav):
    returns = hist_nav['nav'].pct_change().dropna()
    if returns.empty:
        return np.nan, np.nan
    mean_ret = returns.mean()
    std_ret = returns.std()
    if std_ret == 0:
        sharpe = np.nan
    else:
        sharpe = (mean_ret / std_ret) * np.sqrt(252)
    cum_nav = (1 + returns).cumprod()
    rolling_max = cum_nav.cummax()
    drawdown = (cum_nav - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100
    return sharpe, max_drawdown

def add_risk_metrics(group_df):
    rows = []
    for _, row in group_df.iterrows():
        code = row['scheme_code']
        hist_df = get_historical_nav(code)
        if hist_df.empty:
            sharpe = np.nan
            drawdown = np.nan
        else:
            sharpe, drawdown = compute_sharpe_and_drawdown(hist_df)
        r = row.to_dict()
        r['sharpe_ratio'] = round(sharpe, 3) if pd.notna(sharpe) else np.nan
        r['drawdown'] = round(drawdown, 2) if pd.notna(drawdown) else np.nan
        rows.append(r)
    out_df = pd.DataFrame(rows)
    return out_df

def compute_volatility(hist_nav):
    returns = hist_nav['nav'].pct_change().dropna()
    if returns.empty:
        return np.nan
    return returns.std() * np.sqrt(252) * 100

def add_volatility(group_df):
    rows = []
    for _, row in group_df.iterrows():
        code = row['scheme_code']
        hist_df = get_historical_nav(code)
        vol = compute_volatility(hist_df) if not hist_df.empty else np.nan
        r = row.to_dict()
        r['volatility'] = round(vol, 3) if pd.notna(vol) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)

def compute_market_capture(hist_nav, index_nav):
    fund_ret = hist_nav['nav'].pct_change().dropna()
    index_ret = index_nav['nav'].pct_change().dropna()
    df = pd.concat([fund_ret, index_ret], axis=1, join='inner')
    df.columns = ['fund', 'index']
    if df.empty:
        return np.nan, np.nan
    up = df[df['index'] > 0]
    down = df[df['index'] < 0]
    if up.empty:
        up_capture = np.nan
    else:
        up_capture = (up['fund'].mean() / up['index'].mean()) * 100
    if down.empty:
        down_capture = np.nan
    else:
        down_capture = (down['fund'].mean() / down['index'].mean()) * 100
    return up_capture, down_capture

def add_market_capture(group_df, index_code):
    index_hist = get_historical_nav(index_code)
    rows = []
    for _, row in group_df.iterrows():
        code = row['scheme_code']
        hist_df = get_historical_nav(code)
        if hist_df.empty or index_hist.empty:
            up_cap = np.nan
            down_cap = np.nan
        else:
            up_cap, down_cap = compute_market_capture(hist_df, index_hist)
        r = row.to_dict()
        r['upmarket_capture'] = round(up_cap, 3) if pd.notna(up_cap) else np.nan
        r['downmarket_capture'] = round(down_cap, 3) if pd.notna(down_cap) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)

def add_fund_age(df):
    today = pd.Timestamp.now().normalize()
    df['fund_age_years'] = (today - df['start_date']).dt.days / 365.25
    df['fund_age_years'] = df['fund_age_years'].round(0)
    return df

def add_normalized_risk_reward(df):
    df = df.copy()
    df['normalized_risk_reward'] = np.nan
    mask = df['volatility'] > 0
    df.loc[mask, 'normalized_risk_reward'] = df.loc[mask, 'cagr_5yrs'] / df.loc[mask, 'volatility']
    return df

def persist_to_db(df):
    connection_string = "mysql+pymysql://root:Root@123@localhost:3306/mutual_funds"
    engine = create_engine(connection_string)
    df.to_sql('large_cap_analysis', engine, if_exists='replace', index=False)

if __name__ == "__main__":
    master_funds = all_schem_codes()
    large = master_funds['Scheme_Name'].str.contains('large cap|bluechip|nifty 50', case=False, na=False)
    large_funds = master_funds[large]
    group_details = get_group_scheme_details(large_funds)
    final_df = compute_fund_metrics(group_details)
    final_df = add_risk_metrics(final_df)
    final_df = add_volatility(final_df)
    final_df = add_market_capture(final_df, index_code=135320)
    final_df = add_fund_age(final_df)
    final_df = add_normalized_risk_reward(final_df)
    persist_to_db(final_df)
    print(final_df.head())
