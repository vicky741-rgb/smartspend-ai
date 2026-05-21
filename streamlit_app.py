from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SmartSpend AI Analytics", page_icon="$", layout="wide")
st.title("SmartSpend AI - Streamlit Analytics")
st.caption("Upload a finance dataset or inspect the generated sample dataset used for ML forecasting.")

sample_path = Path("datasets/sample_expenses.csv")
uploaded = st.file_uploader("Upload CSV with amount, category, and month/date columns", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
elif sample_path.exists():
    df = pd.read_csv(sample_path)
else:
    st.warning("Run the Flask app once to generate datasets/sample_expenses.csv.")
    st.stop()

amount_col = "amount" if "amount" in df.columns else st.selectbox("Amount column", df.columns)
category_col = "category" if "category" in df.columns else st.selectbox("Category column", df.columns)
month_col = "month_index" if "month_index" in df.columns else st.selectbox("Month/date column", df.columns)

total = df[amount_col].sum()
avg = df[amount_col].mean()
top_category = df.groupby(category_col)[amount_col].sum().idxmax()

c1, c2, c3 = st.columns(3)
c1.metric("Total Spend", f"${total:,.2f}")
c2.metric("Average Transaction", f"${avg:,.2f}")
c3.metric("Top Category", top_category)

left, right = st.columns(2)
with left:
    st.plotly_chart(px.pie(df, names=category_col, values=amount_col, title="Category Breakdown"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(df.groupby(category_col, as_index=False)[amount_col].sum(), x=category_col, y=amount_col, title="Spend by Category"), use_container_width=True)

monthly = df.groupby(month_col, as_index=False)[amount_col].sum()
st.plotly_chart(px.line(monthly, x=month_col, y=amount_col, markers=True, title="Spending Trend"), use_container_width=True)

st.subheader("Smart Recommendations")
if len(monthly) >= 2 and monthly[amount_col].iloc[-1] > monthly[amount_col].iloc[-2]:
    st.error("Latest period spending increased. Review recurring bills and discretionary categories.")
else:
    st.success("Latest period spending improved or remained stable. Consider automating the saved amount.")
st.info(f"{top_category} is your highest category. A category-wise cap can improve your financial health score.")
