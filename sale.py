import streamlit as st
import pandas as pd  # pip install pandas
import altair as alt  # pip install altair


# CONFIGS
YEAR = 2023
PREVIOUS_YEAR = 2022
CITIES = ["Tokyo", "Yokohama", "Osaka"]
DATA_URL = "https://raw.githubusercontent.com/Sven-Bo/datasets/master/store_sales_2022-2023.csv"

# Title with a subtitle for better clarity
st.title(f"Sales Dashboard")
st.write("## Overview of Sales Performance in Major Cities")

# Get and prepare the data
@st.cache_data
def get_and_prepare_data(data):
    df = pd.read_csv(data).assign(
        date_of_sale=lambda df: pd.to_datetime(df["date_of_sale"]),
        month=lambda df: df["date_of_sale"].dt.month,
        year=lambda df: df["date_of_sale"].dt.year,
    )
    return df


df = get_and_prepare_data(data=DATA_URL)

# Calculate total revenue for each city and year, and then calculate the percentage change
city_revenues = (
    df.groupby(["city", "year"])["sales_amount"]
    .sum()
    .unstack()
    .assign(change=lambda x: x.pct_change(axis=1)[YEAR] * 100)
)

# Display the data for each city in separate columns with a more responsive layout
st.write("### Key Metrics by City")
columns = st.columns(len(CITIES))
for i, city in enumerate(CITIES):
    with columns[i]:
        st.metric(
            label=f"{city} Sales",
            value=f"$ {city_revenues.loc[city, YEAR]:,.0f}",
            delta=f"{city_revenues.loc[city, 'change']:.0f}% vs. {PREVIOUS_YEAR}",
        )

# Selection fields
st.write("### Analysis Options")
left_col, right_col = st.columns(2)

# Dynamic filtering for multiple cities
selected_cities = left_col.multiselect("Select cities:", CITIES, default=CITIES)
analysis_type = right_col.selectbox(
    label="Analysis by:", options=["Month", "Product Category"], key="analysis_type"
)

# Toggle for selecting the year for visualization
previous_year_toggle = st.checkbox("Show Previous Year", key="switch_visualization")
visualization_year = PREVIOUS_YEAR if previous_year_toggle else YEAR

# Display the year above the chart based on the toggle switch
st.write(f"**Sales for {visualization_year}**")

# Filter data based on selections
filtered_data = df[df["city"].isin(selected_cities) & (df["year"] == visualization_year)]

if analysis_type == "Product Category":
    # Group data by product category
    grouped_data = filtered_data.groupby("product_category")["sales_amount"].sum().reset_index()
    x_col = "product_category"
    chart_title = "Sales by Product Category"
else:
    # Group data by month
    grouped_data = filtered_data.groupby("month")["sales_amount"].sum().reset_index()
    grouped_data["month"] = grouped_data["month"].apply(lambda x: f"{x:02d}")
    x_col = "month"
    chart_title = "Sales by Month"

# Create a bar chart with Altair for more interactive visuals
bar_chart = alt.Chart(grouped_data).mark_bar().encode(
    x=alt.X(f"{x_col}:N", sort=None, title=x_col.replace("_", " ").capitalize()),
    y=alt.Y("sales_amount:Q", title="Sales Amount"),
    tooltip=[alt.Tooltip(f"{x_col}:N"), alt.Tooltip("sales_amount:Q", title="Sales Amount ($)")],
    color=alt.condition(
        alt.datum.sales_amount > 100000,  # example condition
        alt.value('steelblue'),  # color for values > threshold
        alt.value('lightcoral')  # color for values <= threshold
    )
).properties(title=chart_title).interactive()

# Display the bar chart
st.altair_chart(bar_chart, use_container_width=True)

# Add another KPI for overall performance summary
st.write("### Additional Insights")

# Calculate total sales and average sales per city
total_sales = filtered_data["sales_amount"].sum()
average_sales = filtered_data.groupby("city")["sales_amount"].mean()

st.write(f"**Total Sales in Selected Cities: $ {total_sales:,.0f}**")
st.write(f"**Average Sales per City: $ {average_sales.mean():,.0f}**")
