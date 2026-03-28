import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import joblib

st.set_page_config(page_title="Airbnb Analysis", layout="wide")

df = pd.read_csv("airbnb_clean_data.csv")

#ml
model = joblib.load("airbnb_model.pkl")
feature_columns = joblib.load("feature_columns.pkl")

# =========================
# FIX AREA
# =========================
def get_area(row):
    if row["area_Ampelokipoi-Menemeni"] == 1:
        return "Ampelokipoi-Menemeni"
    elif row["area_Evosmos"] == 1:
        return "Evosmos"
    elif row["area_Stavroupoli"] == 1:
        return "Stavroupoli"
    return "Unknown"

df["area"] = df.apply(get_area, axis=1)

# =========================
# SIDEBAR
# =========================
st.title("Airbnb Analysis Dashboard")

area = st.sidebar.selectbox(
    "Επίλεξε περιοχή",
    ["All"] + sorted(df["area"].unique().tolist())
)

if area != "All":
    df = df[df["area"] == area]

# =========================
# DATA PREVIEW
# =========================
st.subheader("Data Preview")
st.dataframe(df.head())

# =========================
# CORRELATION MATRIX
# =========================
st.subheader("Correlation Matrix: Property Type vs Price")
corr_cols = ["price", "beds", "baths", "bedrooms", "guests"]
corr = df[corr_cols].corr()
fig, ax = plt.subplots(figsize=(4, 2))

sns.heatmap(
    corr,
    annot=True,
    cmap="pink",
    fmt=".2f",
    linewidths=0.5,
    ax=ax
)

ax.set_title("Correlation Matrix")
st.pyplot(fig)

# =========================
# TOP / BOTTOM STAYS
# =========================
st.subheader("Top-10 & Bottom-10 Rated Stays")

# Κρατάμε μόνο listings με τουλάχιστον 5 reviews
rank_df = df[df["reviews"] >= 5].copy()

# Αν δεν υπάρχουν αρκετά δεδομένα
if rank_df.empty:
    st.warning("Δεν υπάρχουν αρκετά δεδομένα με reviews >= 5 για ranking.")
else:
    # Weighted score
    rank_df["weighted_score"] = rank_df["rating"] * np.log1p(rank_df["reviews"])

    # Labels πιο καθαρά
    rank_df["listing_label"] = (
        rank_df["area"]
        + " | rating: " + rank_df["rating"].round(2).astype(str)
        + " | reviews: " + rank_df["reviews"].astype(int).astype(str)
    )

    top10 = rank_df.sort_values("weighted_score", ascending=False).head(10).copy()
    bottom10 = rank_df.sort_values("weighted_score", ascending=True).head(10).copy()

    col1, col2 = st.columns(2)

    with col1:
        st.write("Top 10 stays")

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(top10["listing_label"], top10["weighted_score"])
        ax.invert_yaxis()
        ax.set_xlabel("Weighted Score")
        ax.set_ylabel("")
        ax.set_title("Top Rated Listings")
        st.pyplot(fig)

        st.dataframe(
            top10[["area", "rating", "reviews", "weighted_score"]]
            .round(2)
            .reset_index(drop=True)
        )

    with col2:
        st.write("Bottom 10 stays")

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(bottom10["listing_label"], bottom10["weighted_score"])
        ax.invert_yaxis()
        ax.set_xlabel("Weighted Score")
        ax.set_ylabel("")
        ax.set_title("Lowest Rated Listings")
        st.pyplot(fig)

        st.dataframe(
            bottom10[["area", "rating", "reviews", "weighted_score"]]
            .round(2)
            .reset_index(drop=True)
        )

# ====================================================================================
# CHARACTERISTICS ANALYSIS
# ====================================================================================
st.subheader("Top 5 Important Characteristics")

# όλα τα features που θέλουμε να εξετάσουμε
all_features = [
    "guests",
    "beds",
    "bedrooms",
    "baths",
    "reviews",
    "superhost",
    "favourite",
    "parking",
    "view",
    "self_checkin"
]

# correlation με rating
corr = df[all_features + ["rating"]].corr()

rating_corr = corr["rating"].drop("rating")

# παίρνουμε τα 5 πιο σημαντικά (μεγαλύτερη απόλυτη τιμή)
top5_corr = rating_corr.abs().sort_values(ascending=False).head(5)

top5_features = top5_corr.index.tolist()

# -------------------------------------------------
# BAR CHART (importance)
# -------------------------------------------------
st.markdown("### Top 5 Most Important Features (based on correlation)")

fig, ax = plt.subplots(figsize=(7, 4))

ax.bar(top5_features, rating_corr[top5_features])
ax.set_title("Top 5 Features Affecting Rating")
ax.set_ylabel("Correlation with Rating")

st.pyplot(fig)

# -------------------------------------------------
# CORRELATION MATRIX
# -------------------------------------------------
st.markdown("### Correlation Matrix (Top 5 Features)")

corr_top5 = df[top5_features + ["rating"]].corr()

fig, ax = plt.subplots(figsize=(6, 4))

sns.heatmap(
    corr_top5,
    annot=True,
    cmap="RdPu",
    fmt=".2f",
    ax=ax
)

st.pyplot(fig)

# ================================================================================
# STATS PER LOCATION
# =========================
st.subheader("Stats per Location")

stats = df.groupby("area")[["price", "rating", "reviews", "beds", "bedrooms", "baths", "guests"]].mean()
st.dataframe(stats)

# =========================
# MAP
# =========================

import plotly.express as px

st.subheader("Map with Listings and Basic Info")

map_df = df.dropna(subset=["latitude", "longitude"]).copy()

if map_df.empty:
    st.warning("Δεν υπάρχουν διαθέσιμα δεδομένα τοποθεσίας για τον χάρτη.")
else:

    map_df["listing_info"] = (
        "Area: " + map_df["area"].astype(str)
        + "<br>Price: " + map_df["price"].round(2).astype(str)
        + "<br>Rating: " + map_df["rating"].round(2).astype(str)
        + "<br>Reviews: " + map_df["reviews"].astype(int).astype(str)
        + "<br>Guests: " + map_df["guests"].astype(str)
        + "<br>Beds: " + map_df["beds"].astype(str)
        + "<br>Bedrooms: " + map_df["bedrooms"].astype(str)
        + "<br>Baths: " + map_df["baths"].astype(str)
        + "<br>Superhost: " + map_df["superhost"].astype(str)
        + "<br>Guest Favourite: " + map_df["favourite"].astype(str)
        + "<br>Parking: " + map_df["parking"].astype(str)
        + "<br>View: " + map_df["view"].astype(str)
        + "<br>Self Check-in: " + map_df["self_checkin"].astype(str)
    )

    fig = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        color="rating",
        size="price",
        hover_name="area",
        hover_data={
            "latitude": False,
            "longitude": False,
            "price": True,
            "rating": True,
            "reviews": True,
            "guests": True,
            "beds": True,
            "bedrooms": True,
            "baths": True,
            "superhost": True,
            "favourite": True,
            "parking": True,
            "view": True,
            "self_checkin": True
        },
        custom_data=["listing_info"],
        zoom=11,
        height=600
    )

    fig.update_traces(
        marker=dict(opacity=0.75),
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, use_container_width=True)

    # Προαιρετικά συνοδευτικά stats κάτω από τον χάρτη
    st.markdown("### Quick Map Stats")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Listings on map", len(map_df))

    with col2:
        st.metric("Average price", round(map_df["price"].mean(), 2))

    with col3:
        st.metric("Average rating", round(map_df["rating"].mean(), 2))




#ML
# =========================
# PRICE PREDICTION
# =========================
st.subheader("Price Prediction")

st.write("Enter the property characteristics to estimate the rental price.")

col1, col2 = st.columns(2)

with col1:
    guests = st.number_input("Guests", min_value=1, max_value=20, value=2)
    beds = st.number_input("Beds", min_value=1, max_value=20, value=1)
    bedrooms = st.number_input("Bedrooms", min_value=0, max_value=20, value=1)
    baths = st.number_input("Baths", min_value=0.0, max_value=20.0, value=1.0, step=0.5)

with col2:
    superhost = st.selectbox("Superhost", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
    favourite = st.selectbox("Guest Favourite", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
    parking = st.selectbox("Parking", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
    view = st.selectbox("View", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
    self_checkin = st.selectbox("Self Check-in", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")

st.write("Select Area")
pred_area = st.selectbox("Area", ["Ampelokipoi-Menemeni", "Evosmos", "Stavroupoli"])

input_data = {
    "guests": guests,
    "beds": beds,
    "bedrooms": bedrooms,
    "baths": baths,
    "superhost": superhost,
    "favourite": favourite,
    "parking": parking,
    "view": view,
    "self_checkin": self_checkin,
    "area_Ampelokipoi-Menemeni": 1 if pred_area == "Ampelokipoi-Menemeni" else 0,
    "area_Evosmos": 1 if pred_area == "Evosmos" else 0,
    "area_Stavroupoli": 1 if pred_area == "Stavroupoli" else 0,
}

input_df = pd.DataFrame([input_data])

for col in feature_columns:
    if col not in input_df.columns:
        input_df[col] = 0

input_df = input_df[feature_columns]

if st.button("Predict Price"):
    prediction = model.predict(input_df)[0]
    st.success(f"Estimated price: €{prediction:.2f}")