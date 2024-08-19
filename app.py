import os
import tomli
import streamlit as st
import snowflake.connector
import pandas as pd
import altair as alt


# page layout setup
st.set_page_config(
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded")

st.write("## Financial Market Analysis Dashboard")
st.divider()

# Function to load SQL query from a file
def get_query_from_file(file_path):
    with open(file_path, 'r') as file:
        query = file.read()
    return query

# Initialize connection.
conn = st.connection("snowflake")

# Snowflake connection
def _get_snowflake_connection():
    credentials = _load_snowflake_credentials()
    connection_params = {
        "user": credentials.get("user_name"),
        "password": credentials.get("password"),
        "account": credentials.get("account"),
        "database": credentials.get("database"),
        "schema": credentials.get("schema"),
        "warehouse": credentials.get("warehouse"),
        "role": credentials.get("role"),
    }
    try:
        return snowflake.connector.connect(**connection_params)
    except Exception as e:
        st.error(f"An error occurred while connecting to Snowflake: {e}")
        return None

# Function to execute query from SQL file
def load_query_from_file(file_path):
    query = get_query_from_file(file_path)
    try:
        # Execute query
        df = conn.query(query, ttl=600)
        return df
    except Exception as e:
        st.error(f"An error occurred while executing the query: {e}")
        return None

## Q1 - Top 10 Sectors by Position

# title
st.subheader("Top 10 Sectors by Position (USD)")

# load the query from the file
top_10_sectors_data = load_query_from_file('queries/top_10_sectors.sql')

# query the top 10 sectors
top_10_sectors_df = run_query(top_10_sectors_data)

if not top_10_sectors_df.empty:
    # create the chart
    chart = alt.Chart(top_10_sectors_df).mark_bar().encode(
        y=alt.Y(
            'SECTOR_NAME:N', 
            title='Sector Name', 
            sort='-x', 
            axis=alt.Axis(labelLimit=300)  # Increase the space allowed for the sector names
        ),
        x=alt.X(
            'SECTOR_POSITION_USD:Q', 
            title='Sector Position (USD)', 
            scale=alt.Scale(type='log'),
            axis=alt.Axis(grid=False, labels=False)  # Remove gridlines and labels        
        ),
        color=alt.Color(
            'SECTOR_POSITION_USD:Q', 
            scale=alt.Scale(
                range=['#c6dbef', '#08306b'],  # Light to dark blue shades for the gradient
                type='linear'
            ),
            legend=None  # Hide legend
        ),
        tooltip=[
            alt.Tooltip('SECTOR_NAME:N', title='Sector Name'),
            alt.Tooltip('SECTOR_POSITION_USD:Q', title='Position (USD)', format='$,.2f')
        ]
    ).properties(
        title='From highest to lowest',
    ).interactive()

    # Add text labels on the bars
    text = chart.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Adjust the distance of the text from the bars
    ).encode(
        text=alt.Text('SECTOR_POSITION_USD:Q', format='$,.2f')  # Format the text as USD
    )
    final_chart = chart + text

    # Display the chart 
    st.altair_chart(final_chart, use_container_width=True)

else:
    st.write("Refresh page to get the data")


st.divider()


######### Q2 - Top 25% Companies latest data  #########
st.subheader("Top 25% Companies latest data")

# load the data from file
top_25_percent_query = load_query_from_file('queries/top_25_percent_data.sql')

# query the top 25% from snowflake
top_25_data = run_query(top_25_percent_query)

# display the dataframe
st.dataframe(top_25_data, use_container_width=True)

st.divider()

######### Q3 - Daily close price timeseries #########

# getting companies tickers
companies_names = load_query_from_file('queries/companies_names.sql')

# getting companies tickers
df_company = run_query(companies_names)
companies_tickers = df_company['TICKER'].tolist()

# title
st.subheader("Daily close price timeseries for the selected company")

# select box for the companies
selected_company = st.selectbox("Select a company", companies_tickers)

# get selected company daily closing price
query_company_daily_close_price = f"""
SELECT p.date,c.ticker, p.close_usd
FROM 
    price p
JOIN
    company c ON p.company_id = c.id
WHERE 
    c.ticker = '{selected_company}'
ORDER BY 
    date ASC
"""

# Fetch the data for the selected company
df_company_data = run_query(query_company_daily_close_price)

# Check if there is data available for the selected company
if not df_company_data.empty:
    # Line chart for the selected company
    line_chart = alt.Chart(df_company_data).mark_line().encode(
        x='DATE:T',
        y='CLOSE_USD:Q',
        tooltip=['DATE:T', 'CLOSE_USD:Q']
    ).properties(
        title=f"Daily Close Price for {selected_company}"
    )
    st.altair_chart(line_chart, use_container_width=True)
else:
    st.warning("No data available for the selected company.")
