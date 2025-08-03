import streamlit as st 
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Personal Finance Management", layout="wide")

category_file = "categories.json" # This file to save all categories & details

# 1. Category Dictionary Initialisation:

# Initialise category dictionary inside session_state:
if "categories" not in st.session_state: # Session_state saves the user selection, current inputs
    st.session_state.categories = {
        "Uncategorised": [],    
    }

if os.path.exists(category_file): # Check if category_file is currently in the existing disk from previous session, if yes, it loads the stored categories into session_state to json.load
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)
        
# Save any new categories added during the session to future use:
def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)
        
# 2. Transaction categorisation based on Narrative column:

# Categorise transactions based on extracted keywords:
def categorise_transactions(df):
    df['Category'] = "Uncategorised" # default state is Uncategorised

    for category, keywords in st.session_state.categories.items(): # Loop through category and keywords stored in session_state.categories
        if category == "Uncategorised"or not keywords:
            continue
        # All keywords in Narrative are set to be lowercase and no whitespace
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        # --> Just check any keywords inside the narrative text
        for idx, row in df.iterrows(): # Loop through rows and its contents (*) 
            details = row["Narrative"].lower().strip() # Get keyword in lowercase from Narrative column
            if any(keyword in details for keyword in lowered_keywords):
                df.at[idx, "Category"] = category 
    
    return df

def load_transactions(file):
    # Load the file
    try: 
        df = pd.read_csv(file)
        
        # Initial Cleaning
        df[['Debit Amount', 'Credit Amount']] = df[['Debit Amount', 'Credit Amount']].fillna(0) 
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df = df.drop(columns=['Serial'])
        
        # st.write(df) # Write data to the screen 
        return categorise_transactions(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}") # Show error on the screen if uploading file failed.
        return None # if error, no data to be loaded
    
# Add keyword into category:
def add_keyword_to_category(category, keyword):
    keyword = keyword.lower().strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    
    return False

# Main Streamlit App Process:
def main():
    st.title("💰 Personal Finance Management")
    # Set up upload file box:
    uploaded_file = st.file_uploader("Upload transaction CSV file", type=["csv"]) # function built in Streamlit

    if uploaded_file is not None: # Check if the file is uploaded
        df = load_transactions(uploaded_file) # Uploaded file is stored in df to use later in python
        
        if df is not None:
            debit_df = df[df['Debit Amount'] > 0].drop(columns=['Credit Amount']).copy()
            credit_df = df[df['Credit Amount'] > 0].drop(columns=['Debit Amount']).copy()
            
            st.session_state.debit_df = debit_df.copy()
            st.session_state.credit_df = credit_df.copy()
            
            debit_df = debit_df.reset_index(drop=True)
            credit_df = credit_df.reset_index(drop=True)
            
            # Add new category:
            st.markdown(
                "<h5 style='margin-bottom: 10px; font-size: 1rem;'>➕ Add a New Category</h5>", 
                unsafe_allow_html=True
            )
            # Text input for new category:
            new_category = st.text_input("New Category Name")
            # Dropdown to show existing ones (read-only)
            existing_category = st.selectbox(
                "📂 Existing Categories", 
                list(st.session_state.categories.keys()) if st.session_state.categories else ["(None yet)"],
                index=0
            )
            # Button to add new category
            add_button = st.button("Add Category")
                
            if add_button and new_category:
                if new_category in st.session_state.categories:
                    st.warning(f"⚠️ The category '{new_category}' already exists.")
                else:
                    st.session_state.categories[new_category] = []
                    save_categories() # save the new category inside the list
                    st.success(f"Added a new category: {new_category}") # Notify user of new category created
                    st.rerun() # rerun the Streamlit application to save the new category into the list

            # Create 2 tabs to see Expenses & Income
            st.markdown("---")
            st.subheader("📊 Report")
            tab1, tab2 = st.tabs(['Expenditures (Debits)', 'Incomes (Credits)'])
            with tab1: 
                editable_debit_df = st.data_editor(
                    st.session_state.debit_df[["Date", "Narrative", "Debit Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format = "DD/MM/YYYY"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options = list(st.session_state.categories.keys())
                        )
                    },
                    hide_index = True,
                    use_container_width=True,
                    key="debit_category_editor"
                )
                
                debit_save_button = st.button("Apply changes", type="primary", key="debit_save_button")
                if debit_save_button:
                    for idx, row in editable_debit_df.iterrows():
                        debit_new_category = row["Category"]
                        if debit_new_category == st.session_state.debit_df.at[idx, "Category"]:
                            continue
                        
                        debit_details = " ".join(row["Narrative"].split()[3:6])
                        st.session_state.debit_df.at[idx, "Category"] = debit_new_category
                        add_keyword_to_category(debit_new_category, debit_details)

                    st.rerun()
            
            with tab2:
                editable_credit_df = st.data_editor(
                    st.session_state.credit_df[["Date", "Narrative", "Credit Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format = "DD/MM/YYYY"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options = list(st.session_state.categories.keys())
                        )
                    },
                    hide_index = True,
                    use_container_width=True,
                    key="credit_category_editor"
                )
                
                credit_save_button = st.button("Apply changes", type="primary", key="credit_save_button")
                if credit_save_button:
                    for idx, row in editable_credit_df.iterrows():
                        credit_new_category = row["Category"]
                        if credit_new_category == st.session_state.credit_df.at[idx, "Category"]:
                            continue
                        
                        credit_details = " ".join(row["Narrative"].split()[3:6])
                        st.session_state.credit_df.at[idx, "Category"] = credit_new_category
                        add_keyword_to_category(credit_new_category, credit_details)
                        
                    st.rerun()

# 3. Data Visualisation:

            st.markdown("---")
            st.subheader("📊 Personal Finance Dashboard")
            
            st.markdown("<h4 style='margin-bottom: 8px;'>📅 Filter Transactions</h4>", unsafe_allow_html=True)
            combined_df = pd.concat([
                            st.session_state.debit_df[["Date", "Narrative", "Debit Amount", "Category"]].rename(columns={"Debit Amount": "Amount"}).assign(Type="Expense"),
                            st.session_state.credit_df[["Date", "Narrative", "Credit Amount", "Category"]].rename(columns={"Credit Amount": "Amount"}).assign(Type="Income")
                        ])
            # Ensure 'Date' is datetime
            combined_df["Date"] = pd.to_datetime(combined_df["Date"])
            
            # Date filter
            min_date = combined_df["Date"].min()
            max_date = combined_df["Date"].max()
            start_date, end_date = st.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

            # Category filter (multiselect)
            all_categories = sorted(combined_df["Category"].dropna().unique())
            selected_categories = st.multiselect("Select Categories", all_categories, default=all_categories)
            
            # Filter the DataFrame
            filtered_df = combined_df[
                (combined_df["Date"] >= pd.to_datetime(start_date)) &
                (combined_df["Date"] <= pd.to_datetime(end_date)) &
                (combined_df["Category"].isin(selected_categories))
            ]
            
            # 3.1.Scorecards:
            # average_expense = filtered_df['Debit Amount'].mean()
            st.markdown("#### 💸 KPI Overview")
            total_expense = filtered_df[filtered_df["Type"] == "Expense"]["Amount"].sum()
            total_income = filtered_df[filtered_df["Type"] == "Income"]["Amount"].sum()
            net_balance = total_income - total_expense
            
            col1, col2, col3 = st.columns(3)
            col1.metric("📈 Net Balance", f"${net_balance:,.2f}")
            col2.metric("💸Total Expenses", f"${total_expense:,.2f}")
            col3.metric("💰 Total Income", f"${total_income:,.2f}")
            
            # 3.2. Line graph - Trend Analysis
            st.markdown("#### 📈 Cash Flow Line Chart")
            cashflow_by_day = filtered_df.groupby(["Date", "Type"])["Amount"].sum().reset_index()
            fig_line = px.line(cashflow_by_day, 
                               x="Date", y="Amount", 
                               color="Type",
                               markers=True, 
                               color_discrete_map={
                                    "Income": "#2ca02c",   # green
                                    "Expense": "#d62728"   # red
                                })
            st.plotly_chart(fig_line, use_container_width=True)
            
            # 3.3. Bar graph: Spending by Category
            # expense_by_category = filtered_df[filtered_df["Type"] == "Expense"].groupby("Category")["Amount"].sum().reset_index()
            st.markdown("#### 📊 Expenses by Category")
            expense_by_category = (
                filtered_df[filtered_df["Type"] == "Expense"]
                .groupby("Category")["Amount"]
                .sum()
                .reset_index()
                .sort_values("Amount", ascending=True)  # ✅ ascending=True for top-to-bottom bars
            )
            fig_bar = px.bar(
                        expense_by_category,
                        x="Amount",
                        y="Category",
                        orientation="h"
                    )
            st.plotly_chart(fig_bar, use_container_width=True)
            
# Call out function to use it:
main() # streamlit run main.py
