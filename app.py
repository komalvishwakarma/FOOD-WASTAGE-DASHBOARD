import streamlit as st
import pandas as pd
import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect("food_wastage.db")

st.set_page_config(page_title="Food Wastage Dashboard", layout="wide")
st.title("🍽️ Food Wastage Management Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Add Listing", "🛠️ Manage Listings"])

with tab2:
    st.subheader("➕ Add New Food Listing")

    provider_names = pd.read_sql("SELECT Name, Provider_ID FROM Providers", conn)
    selected_provider = st.selectbox("Select Provider", provider_names['Name'])
    provider_id = provider_names[provider_names['Name'] == selected_provider]['Provider_ID'].values[0]

with st.form("add_food_form"):
    provider_id = st.text_input("Provider ID")
    food_name = st.text_input("Food Name")
    food_type = st.selectbox("Food Type", ["Vegetables", "Fruits", "Grains", "Dairy", "Snacks", "Meals"])
    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
    quantity = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
    expiry_date = st.date_input("Expiry Date")
    submitted = st.form_submit_button("Add Listing")

    if submitted:
        insert_query = """
        INSERT INTO Food_Listings (Provider_ID, Food_Name, Food_Type, Meal_Type, Quantity, Expiry_Date)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        conn.execute(insert_query, (provider_id, food_name, food_type, meal_type, quantity, expiry_date))
        conn.commit()
        st.success("✅ New food listing added successfully!")

with tab3:
    st.subheader("✏️ Update Food Listing")

    # Get all Food_IDs
    food_ids = pd.read_sql("SELECT Food_ID FROM Food_Listings", conn)['Food_ID'].tolist()
    selected_id = st.selectbox("Select Food ID to Update", food_ids)

    # Fetch current details
    current = pd.read_sql(f"SELECT * FROM Food_Listings WHERE Food_ID = {selected_id}", conn)

    with st.form("update_form"):
        new_quantity = st.number_input("New Quantity (kg)", value=float(current['Quantity'][0]), min_value=0.0, step=0.1)
        new_meal_type = st.selectbox("New Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"], index=["Breakfast", "Lunch", "Dinner", "Snack"].index(current['Meal_Type'][0]))
        update_btn = st.form_submit_button("Update Listing")

        if update_btn:
            update_query = """
            UPDATE Food_Listings
            SET Quantity = ?, Meal_Type = ?
            WHERE Food_ID = ?
            """
            conn.execute(update_query, (new_quantity, new_meal_type, selected_id))
            conn.commit()
            st.success("✅ Food listing updated successfully!")

    st.subheader("🗑️ Delete Food Listing")

    # Select Food_ID to delete
    delete_id = st.selectbox("Select Food ID to Delete", food_ids, key="delete")

    if st.button("Delete Listing"):
        delete_query = "DELETE FROM Food_Listings WHERE Food_ID = ?"
        conn.execute(delete_query, (delete_id,))
        conn.commit()
        st.success(f"✅ Food listing with ID {delete_id} deleted successfully!")

with tab1:  

    st.subheader("🔎 Filter Food Listings")

# Get unique providers and food types
providers = pd.read_sql("SELECT DISTINCT Name FROM Providers", conn)['Name'].tolist()
food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM Food_Listings", conn)['Food_Type'].tolist()

# Create filters
selected_provider = st.selectbox("Select Provider", providers)
selected_food_type = st.selectbox("Select Food Type", food_types)

# Filtered query
filter_query = f"""
SELECT f.Food_Name, f.Quantity, f.Meal_Type, f.Expiry_Date
FROM Food_Listings f
JOIN Providers p ON f.Provider_ID = p.Provider_ID
WHERE p.Name = '{selected_provider}' AND f.Food_Type = '{selected_food_type}'
"""

df_filtered = pd.read_sql(filter_query, conn)
st.dataframe(df_filtered)

st.subheader("📊 Dashboard Visuals")

 # 🔢 Summary Metrics

total_listings = pd.read_sql("SELECT COUNT(*) FROM Food_Listings", conn).iloc[0, 0]
total_claims = pd.read_sql("SELECT COUNT(*) FROM Claims", conn).iloc[0, 0]
avg_quantity = pd.read_sql("SELECT ROUND(AVG(Quantity), 2) FROM Food_Listings", conn).iloc[0, 0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Listings", value=total_listings)
with col2:
    st.metric(label="Total Claims", value=total_claims)
with col3:
    st.metric(label="Avg. Quantity per Listing", value=avg_quantity)

# Create horizontal tabs
tab1, tab2 = st.tabs(["📊 Food Types", "📈 Claims Over Time"])

# Tab 1: Bar chart of food types
with tab1:
    food_type_counts = pd.read_sql("""
    SELECT Food_Type, COUNT(Food_ID) AS Count
    FROM Food_Listings
    GROUP BY Food_Type
    """, conn)
    st.bar_chart(food_type_counts.set_index("Food_Type")

# Tab 2: Line chart of claims over time
with tab2:
    claims_ts = pd.read_sql("""
    SELECT DATE(Timestamp) AS Claim_Date, COUNT(*) AS Claims
    FROM Claims
    GROUP BY Claim_Date
    ORDER BY Claim_Date
    """, conn)
    claims_ts["Claim_Date"] = pd.to_datetime(claims_ts["Claim_Date"])
    claims_ts.set_index("Claim_Date", inplace=True)
    st.line_chart(claims_ts)

# Query 1: Providers per city
st.subheader("📊 Number of Food Providers per City")

query1 = """
SELECT City, COUNT(*) AS Provider_Count
FROM Providers
GROUP BY City
"""

df1 = pd.read_sql(query1, conn)
st.dataframe(df1)

# Query 2: Number of receivers per city
st.subheader("👥 Number of Food Receivers per City")

query2 = """
SELECT City, COUNT(*) AS Receiver_Count
FROM Receivers
GROUP BY City
"""

df2 = pd.read_sql(query2, conn)
st.dataframe(df2)

# Query 3: Provider type contributing the most food
st.subheader("🏪 Provider Type Contribution")

query3 = """
SELECT Provider_Type, SUM(Quantity) AS Total_Quantity
FROM Food_Listings
GROUP BY Provider_Type
ORDER BY Total_Quantity DESC
"""

df3 = pd.read_sql(query3, conn)
st.dataframe(df3)

# Query 4: Provider contact info by city
st.subheader("📞 Provider Contact Info by City")

# Get list of cities from Providers table
cities = pd.read_sql("SELECT DISTINCT City FROM Providers", conn)['City'].tolist()

# Create dropdown filter
selected_city = st.selectbox("Select a City", cities)

# Run filtered query
contact_query = f"""
SELECT Name, Contact
FROM Providers
WHERE City = '{selected_city}'
"""

df4 = pd.read_sql(contact_query, conn)
st.dataframe(df4)

# Query 5: Receivers with most claims
st.subheader("📦 Most Active Receivers (by Claims)")

query5 = """
SELECT r.Name, COUNT(*) AS Total_Claims
FROM Claims c
JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Name
ORDER BY Total_Claims DESC
"""

df5 = pd.read_sql(query5, conn)
st.dataframe(df5)

# Query 6: Total quantity of food available
st.subheader("🍽️ Total Quantity of Food Available")

query6 = """
SELECT SUM(Quantity) AS Total_Food_Available
FROM Food_Listings
"""

df6 = pd.read_sql(query6, conn)
st.dataframe(df6)

# Query 7: City with highest number of food listings
st.subheader("🏙️ Food Listings by City")

query7 = """
SELECT p.City, COUNT(*) AS Listings_Count
FROM Food_Listings f
JOIN Providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.City
ORDER BY Listings_Count DESC
"""

df7 = pd.read_sql(query7, conn)
st.dataframe(df7)

# Query 8: Most commonly available food types
st.subheader("🍞 Most Commonly Available Food Types")

query8 = """
SELECT Food_Type, COUNT(*) AS Frequency
FROM Food_Listings
GROUP BY Food_Type
ORDER BY Frequency DESC
"""

df8 = pd.read_sql(query8, conn)
st.dataframe(df8)

# Query 9: Claims per food item
st.subheader("📦 Claims Made per Food Item")

query9 = """
SELECT f.Food_Name, COUNT(*) AS Claim_Count
FROM Claims c
JOIN Food_Listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Food_Name
ORDER BY Claim_Count DESC
"""

df9 = pd.read_sql(query9, conn)
st.dataframe(df9)

# Query 10: Providers with most successful claims
st.subheader("🏆 Top Providers by Successful Claims")

query10 = """
SELECT p.Name, COUNT(*) AS Successful_Claims
FROM Claims c
JOIN Food_Listings f ON c.Food_ID = f.Food_ID
JOIN Providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Name
ORDER BY Successful_Claims DESC
"""

df10 = pd.read_sql(query10, conn)
st.dataframe(df10)

# Query 11: Average quantity of food listed per provider
st.subheader("📊 Average Quantity of Food Listed per Provider")

query11 = """
SELECT p.Name, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity
FROM Food_Listings f
JOIN Providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Name
ORDER BY Avg_Quantity DESC
"""

df11 = pd.read_sql(query11, conn)
st.dataframe(df11)

# Query 12: Distribution of meal types
st.subheader("🍽️ Distribution of Meal Types")

query12 = """
SELECT Meal_Type, COUNT(*) AS Count
FROM Food_Listings
GROUP BY Meal_Type
ORDER BY Count DESC
"""

df12 = pd.read_sql(query12, conn)
st.dataframe(df12)

# Query 13: Most frequently listed food items by provider type
st.subheader("🍱 Top Food Items by Provider Type")

query13 = """
SELECT Provider_Type, Food_Name, COUNT(*) AS Frequency
FROM Food_Listings
GROUP BY Provider_Type, Food_Name
ORDER BY Provider_Type, Frequency DESC
"""

df13 = pd.read_sql(query13, conn)
st.dataframe(df13)

# Query 14: Average time between expiry and claim
st.subheader("⏱️ Average Time Between Expiry and Claim")

query14 = """
SELECT ROUND(AVG(
    JULIANDAY(c.Timestamp) - JULIANDAY(f.Expiry_Date)
), 2) AS Avg_Claim_Delay_Days
FROM Claims c
JOIN Food_Listings f ON c.Food_ID = f.Food_ID
WHERE c.Timestamp IS NOT NULL AND f.Expiry_Date IS NOT NULL
"""

df14 = pd.read_sql(query14, conn)
st.dataframe(df14)

# Query 15: Providers with unclaimed food listings
st.subheader("🚫 Providers with No Claimed Food")

query15 = """
SELECT DISTINCT p.Name
FROM Providers p
JOIN Food_Listings f ON p.Provider_ID = f.Provider_ID
WHERE f.Food_ID NOT IN (
    SELECT Food_ID FROM Claims
)
"""

df15 = pd.read_sql(query15, conn)
st.dataframe(df15)








