# Mutual Fund Risk-Adjusted Performance Analyzer

## What This Does

I built this to help figure out which large-cap mutual funds actually deliver good returns without crazy volatility. There are thousands of funds out there, and I wanted a data-driven way to compare them beyond just looking at returns.

The tool pulls live data on 340+ large-cap equity funds, calculates key risk metrics (CAGR, volatility, Sharpe ratio), and ranks them using a composite score. Think of it as building a "which fund should I actually invest in?" ranking system.

## Why I Built This

Honestly, I was tired of seeing articles that just list "top 10 funds" without showing the math. I wanted to understand:
- Which funds give consistent returns (not just high one-time gains)
- How risky each fund actually is (volatility matters)
- Risk-adjusted performance (Sharpe ratio - returns per unit of risk)

Plus, I wanted to practice working with real financial data and MySQL at scale.

## What It Actually Does

1. **Data Collection**: Uses the `mftool` Python library to fetch live data on 14,000+ mutual funds from AMFI (Association of Mutual Funds in India)

2. **Filtering**: Narrows down to large-cap and bluechip funds only (342 funds)

3. **Metric Calculation**: For each fund, computes:
   - 3-year and 5-year CAGR (compound annual growth rate)
   - Volatility (standard deviation of returns)
   - Sharpe ratio (risk-adjusted returns)
   - Downside deviation (bad volatility only)

4. **Ranking System**: Uses z-score normalization to create a composite score. Funds with:
   - Higher returns → Higher score
   - Lower volatility → Higher score
   - Better Sharpe ratio → Higher score

5. **Database Storage**: Stores everything in MySQL for easy querying

## Tech Stack

- **Python**: Pandas, NumPy (data manipulation), Matplotlib/Seaborn (quick charts)
- **mftool**: Library to fetch Indian mutual fund data
- **MySQL**: Data storage
- **SQLAlchemy**: Python ↔ MySQL connection
- **Jupyter Notebook**: Analysis and exploration

## Key Findings (Example)

When I ran this on ICICI funds, I found:
- **ICICI US Bluechip**: 18.59% CAGR (higher) but 17.68% volatility
- **ICICI Large Cap**: 18.22% CAGR (slightly lower) but only 15.24% volatility

The Large Cap fund had a better risk-reward profile (normalized score: 1.04 vs 0.51), making it the better pick for steady long-term growth.

Discovered 15+ funds with 15%+ returns and <18% volatility - solid options for conservative investors.

## How to Run

```bash
# Install dependencies
pip install mftool pandas numpy matplotlib seaborn sqlalchemy pymysql

# Setup MySQL database
mysql -u root -p
CREATE DATABASE mutual_funds;

# Run the notebook
jupyter notebook Get_mf_data.ipynb
```

**Note**: Update database credentials in the notebook (`create_engine` line)

## Sample Output

The analysis produces a ranked dataframe like:

| Fund Name | 5Y CAGR | Volatility | Sharpe | Risk-Reward Score |
|-----------|---------|------------|--------|-------------------|
| ICICI Large Cap | 18.22% | 15.24% | 0.648 | 1.04 |
| ICICI US Bluechip | 18.59% | 17.68% | 0.691 | 0.51 |
| ... | ... | ... | ... | ... |

## What I Learned

- Working with financial APIs (mftool isn't the most stable, had to handle errors)
- Z-score normalization for ranking (way better than simple sorting)
- Sharpe ratio isn't perfect but it's a good starting point for risk-adjusted returns
- Filtering 14k funds down to relevant ones requires domain knowledge (what even is a "bluechip" fund?)

## Future Improvements

- **Historical backtesting**: How would these picks have performed if chosen 3 years ago?
- **Add more fund categories**: Mid-cap, small-cap, hybrid funds
- **Expense ratio consideration**: Currently not factoring in management fees
- **Rolling returns**: Better than point-in-time CAGR
- **Web dashboard**: Make this usable for non-technical folks (maybe Streamlit)
- **Automated alerts**: Notify when a fund's metrics change significantly

## Why This Matters for Product Analytics

The logic here (segmentation, scoring, ranking) is the same as analyzing user cohorts:
- Segment funds by risk profile = Segment users by behavior
- Rank by composite score = Identify high-value user segments
- Filter for stable performers = Find "sticky" users who don't churn

Just different domain, same analytical thinking.

---

**Dataset**: Live data from AMFI via mftool  
**Date**: December 2025 - January 2026  
**Funds Analyzed**: 342 large-cap equity funds