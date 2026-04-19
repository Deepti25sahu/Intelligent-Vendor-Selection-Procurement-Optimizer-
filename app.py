import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="P2P Optimizer", layout="wide")

# ---------------- STYLING ----------------
st.markdown("""
<style>
.main {background-color: #f5f7fa;}
div[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
}
h1,h2,h3 {color: #0a6ed1;}
</style>
""", unsafe_allow_html=True)

# ---------------- IMPORT ----------------
from auth import auth_screen, check_login
from database import (
    create_vendor_table, fetch_data,
    add_vendor, update_vendor, delete_vendor, upload_csv
)

# ---------------- AUTH ----------------
auth_screen()

if not check_login():
    st.warning("🔒 Please login")
    st.stop()

# ---------------- INIT ----------------
create_vendor_table()
df = fetch_data()

if df.empty:
    st.error("⚠️ No vendor data found")
    st.stop()

# ---------------- TITLE ----------------
st.title("💡 Intelligent Vendor Selection & Procurement Optimizer")

st.sidebar.success(f"👤 User: {st.session_state.get('user')}")
st.sidebar.info(f"Role: {st.session_state.get('role')}")

# ================= SEARCH =================
search = st.text_input("🔍 Search Vendor")

# ================= FILTER =================
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")

cat = st.sidebar.selectbox("Category", ["All"] + list(df['category'].unique()))
loc = st.sidebar.selectbox("Location", ["All"] + list(df['location'].unique()))
rate = st.sidebar.slider("Min Rating", 1.0, 5.0, 3.5)

f = df.copy()

if search:
    f = f[f['name'].str.contains(search, case=False)]

if cat != "All":
    f = f[f['category'] == cat]

if loc != "All":
    f = f[f['location'] == loc]

f = f[f['rating'] >= rate]

if f.empty:
    st.warning("No matching vendors")
    st.stop()

# ================= ADMIN =================
if st.session_state.get("role") == "admin":

    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Add Vendor")

    with st.sidebar.form("add_form"):
        vid = st.text_input("Vendor ID")
        name = st.text_input("Name")
        price = st.number_input("Price", min_value=0)
        delivery = st.number_input("Delivery Days", min_value=1)
        rating = st.slider("Rating", 1.0, 5.0, 3.5)
        loc = st.text_input("Location")
        catg = st.text_input("Category")

        if st.form_submit_button("Add"):
            if not vid or not name:
                st.sidebar.error("Fill required fields")
            else:
                if add_vendor(vid, name, price, delivery, rating, loc, catg):
                    st.sidebar.success("✅ Vendor added")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Vendor ID exists")

    # EDIT / DELETE
    st.sidebar.markdown("---")
    st.sidebar.subheader("✏️ Edit / Delete")

    vid = st.sidebar.selectbox("Select Vendor", df['vendor_id'])
    row = df[df['vendor_id'] == vid].iloc[0]

    n = st.sidebar.text_input("Name", row['name'])
    p = st.sidebar.number_input("Price", value=int(row['price']))
    d = st.sidebar.number_input("Delivery", value=int(row['delivery_days']))
    r = st.sidebar.slider("Rating", 1.0, 5.0, float(row['rating']))
    l = st.sidebar.text_input("Location", row['location'])
    c = st.sidebar.text_input("Category", row['category'])

    if st.sidebar.button("Update"):
        update_vendor(vid, n, p, d, r, l, c)
        st.rerun()

    if st.sidebar.button("Delete"):
        delete_vendor(vid)
        st.rerun()

    # UPLOAD
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Upload CSV")

    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        upload_csv(file)
        st.sidebar.success("Uploaded")
        st.rerun()

else:
    st.sidebar.warning("👀 View-only access")

# ================= SCORING =================
def norm(col, rev=False):
    if col.max() == col.min():
        return pd.Series([1]*len(col), index=col.index)
    return (col.max()-col)/(col.max()-col.min()) if rev else (col-col.min())/(col.max()-col.min())

f['score'] = (
    0.5 * norm(f['price'], True) +
    0.3 * norm(f['delivery_days'], True) +
    0.2 * norm(f['rating'])
)

# ================= RANKING =================
f['rank'] = f['score'].rank(ascending=False)

best = f.loc[f['score'].idxmax()]

# ================= KPI =================
c1, c2, c3 = st.columns(3)
c1.metric("🏆 Best Vendor", best['name'])
c2.metric("💰 Price", best['price'])
c3.metric("⭐ Rating", best['rating'])

# EXTRA KPI
st.markdown("### 📊 Key Insights")
c4, c5, c6 = st.columns(3)
c4.metric("Avg Price", round(f['price'].mean(),2))
c5.metric("Fastest Delivery", f['delivery_days'].min())
c6.metric("Top Rating", f['rating'].max())

# ================= ALERTS =================
st.markdown("### 🚨 Smart Alerts")

if best['price'] > f['price'].mean():
    st.warning("Best vendor price is above average")

if best['delivery_days'] > 5:
    st.warning("Delivery delay risk")

# ================= FAVORITES =================
st.markdown("### ⭐ Favorite Vendors")
fav = st.multiselect("Select Favorites", f['name'])
st.write("Selected:", fav)

# ================= CHARTS =================
st.subheader("📊 Vendor Score Comparison")
st.plotly_chart(px.bar(f, x='name', y='score', color='score'), use_container_width=True)

st.subheader("📈 Price vs Rating")
st.plotly_chart(px.scatter(f, x='price', y='rating', size='score', color='category'), use_container_width=True)

# CATEGORY CHART
st.subheader("🥧 Category Distribution")
st.plotly_chart(px.pie(f, names='category'), use_container_width=True)

# ================= TABLE =================
st.subheader("📋 Ranked Vendor Data")
st.dataframe(f.sort_values('rank'), use_container_width=True)

# ================= EXPORT =================
st.markdown("---")
st.subheader("📤 Export Data")

# CSV
csv = f.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "vendors.csv")

# Excel
buffer = io.BytesIO()
f.to_excel(buffer, index=False)
st.download_button("📊 Download Excel", buffer.getvalue(), "vendors.xlsx")

# Top 5
top5 = f.sort_values(by='score', ascending=False).head(5)
st.download_button("🏆 Download Top 5", top5.to_csv(index=False).encode(), "top5.csv")

# ================= LOGOUT =================
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()