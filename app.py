import streamlit as st
import pandas as pd
import joblib

# load model
model = joblib.load("airbnb_model.pkl")

st.title("Airbnb Price Predictor")

# --- INPUTS από χρήστη ---
guests = st.number_input("Guests", min_value=1, value=2)
beds = st.number_input("Beds", min_value=0, value=1)
bedrooms = st.number_input("Bedrooms", min_value=0, value=1)
baths = st.number_input("Baths", min_value=0.0, value=1.0)

# Boolean/Κατηγορικές μεταβλητές (Ναι/Όχι)
superhost = st.checkbox("Superhost")
favourite = st.checkbox("Guest Favourite")

# Βαθμολογία και Κριτικές
rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=5.0, step=0.1)
reviews = st.number_input("Reviews", min_value=0, value=10)

# Τοποθεσία (Συντεταγμένες)
latitude = st.number_input("Latitude", format="%.6f", value=40.6401)
longitude = st.number_input("Longitude", format="%.6f", value=22.9444)

# Περιοχές (One-Hot Encoded)
st.write("Area")
area_Ampelokipoi_Menemeni = st.checkbox("Ampelokipoi-Menemeni")
area_Evosmos = st.checkbox("Evosmos")
area_Stavroupoli = st.checkbox("Stavroupoli")

# Παροχές
parking = st.checkbox("Parking")
view = st.checkbox("View")
self_checkin = st.checkbox("Self Check-in")


# button
if st.button("Predict Price"):
    input_data = pd.DataFrame({
        "guests": [guests],
        "beds": [beds],
        "bedrooms": [bedrooms],
        "baths": [baths],
        "superhost": [superhost],
        "favourite": [favourite],
        "rating": [rating],
        "reviews": [reviews],
        "latitude": [latitude],
        "longitude": [longitude],
        "area_Ampelokipoi-Menemeni": [area_Ampelokipoi_Menemeni],
        "area_Evosmos": [area_Evosmos],
        "area_Stavroupoli": [area_Stavroupoli],
        "parking": [parking],
        "view": [view],
        "self_checkin": [self_checkin]
    })

    prediction = model.predict(input_data)

    st.success(f"Estimated Price: {prediction[0]:.2f} €")