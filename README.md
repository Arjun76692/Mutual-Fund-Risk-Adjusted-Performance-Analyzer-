# 📈 Mutual Fund Performance Analytics

A Python-based tool to extract, analyze, and compare Indian Mutual Funds. This project helps investors visualize performance on a "level playing field" by using data normalization and risk-adjusted metrics.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![Seaborn](https://img.shields.io/badge/Seaborn-blue?style=for-the-badge&logo=pandas&logoColor=white)

---

## 🚀 The Problem This Solves
Comparing two Mutual Funds by their NAV (price) is difficult. For example:
* **Fund A:** NAV of ₹500
* **Fund B:** NAV of ₹25

If you plot them raw, Fund B looks like a flat line. This project **Normalizes (Rebases)** the data to 100, showing you the **Growth Percentage** so you can see which fund actually performed better.



---

## 📊 Key Analytics Included

### 1. Cumulative Growth (Rebased to 100)
We "Melt" the data to create a multi-line graph. This shows the journey of ₹100 invested in each fund. 
* **Goal:** Identify which fund generates the highest returns over time.

### 2. Correlation Heatmap
We check if the funds in your portfolio are too similar. 
* **Insight:** If two funds have a correlation of 0.98, they are likely holding the exact same stocks. True diversification requires lower correlation.



### 3. Volatility (Annualized Risk)
Using `numpy` and `std()`, we calculate the annualized risk.
* **Formula used:** $\sigma_{annual} = \sigma_{daily} \times \sqrt{252}$
* **Insight:** High volatility means more significant price swings and higher risk.

---

## 🛠️ How to Use

### Prerequisites
You will need Python installed. Install the libraries using pip:
```bash
pip install mftool pandas numpy matplotlib seaborn
