# AirBnB Data Analysis with Selenium, Beautiful Soup & Python

An end-to-end data pipeline that scrapes AirBnB listing data, cleans and stores it, analyzes it, and uses it to train a machine learning model for price prediction — wrapped in an interactive Streamlit web app.

> **Disclaimer:** This project was created for educational purposes only. When scraping any real platform, always respect its `robots.txt` and Terms of Service.

## 📋 Overview

This project builds a complete data pipeline:

1. **Web scraping** AirBnB listings with Selenium + Beautiful Soup
2. **Storage** of raw and cleaned data in MongoDB
3. **Data cleaning & preprocessing** with Pandas
4. **Exploratory data analysis** with Seaborn, Matplotlib and Plotly
5. **Machine learning** price prediction model (scikit-learn)
6. **Interactive web app** built with Streamlit

The data covers listings from three areas of Thessaloniki, Greece: **Stavroupoli**, **Ampelokipoi-Menemeni**, and **Evosmos**.

## 🗂️ Repository Structure

```
├── web_scraping.py              # Scrapes AirBnB listings and produces airbnb_listings.csv (raw data)
├── app.py                       # Streamlit web app (price prediction + visualizations)
├── Project1_Web_Scraping.ipynb  # Notebook: data cleaning, EDA, and ML model training
├── airbnb_listings.csv          # Raw scraped data
├── airbnb_clean_data.csv        # Cleaned, model-ready dataset
└── airbnb_model.pkl             # Trained ML model (Random Forest Regressor)
```

## 🛠️ Tech Stack

- **Scraping:** Selenium, Beautiful Soup, webdriver-manager
- **Data processing:** Pandas, NumPy
- **Database:** MongoDB (via MongoDB Compass)
- **Machine Learning:** scikit-learn (Linear Regression, Random Forest, Gradient Boosting)
- **Visualization:** Matplotlib, Seaborn, Plotly Express
- **Web app:** Streamlit
- **Model persistence:** joblib

## ⚙️ Installation

Install the required packages:

```bash
pip install selenium beautifulsoup4 pandas requests webdriver-manager
pip install scikit-learn streamlit joblib plotly matplotlib seaborn numpy
```

## 🚀 Usage

### 1. Scrape the data

```bash
python web_scraping.py
```

This navigates the AirBnB search results (10 pages per area, across the three target areas), collects listing links, visits each listing page, and extracts the relevant fields — producing `airbnb_listings.csv` with the raw, unprocessed data.

### 2. Explore, clean and train the model

Open and run `Project1_Web_Scraping.ipynb`. This notebook performs the data cleaning steps described below, the exploratory analysis, and trains/evaluates the ML model, saving it as `airbnb_model.pkl`.

### 3. Run the web app

```bash
streamlit run app.py
```

This launches the interactive app for price prediction and data visualization.

## 📊 Data Collected

For each listing, the following features were extracted:

| Category | Fields |
|---|---|
| Pricing | `price` (per night) |
| Capacity & structure | `guests`, `beds`, `bedrooms`, `baths` |
| Quality & reviews | `superhost`, `guest favourite`, `rating`, `reviews` |
| Text data | host name, `characteristics` (e.g., parking, view, self check-in) |
| Location | `latitude`, `longitude`, listing URL |

## 🧹 Data Cleaning Pipeline

1. **Deduplication:** Removed 260 duplicate records (overlapping areas), leaving 280 listings. Dropped `host_name` and `room_url` columns as they added no analytical value.
2. **Missing values:** Filled empty `bedrooms` (studios) with 0; filled missing `rating` with the column mean; filled missing `reviews` with 0.
3. **Text parsing:** Parsed the free-text `characteristics` column into 3 binary features — `parking`, `view`, and `self_checkin` — based on keyword matching, then dropped the original column.
4. **One-hot encoding:** Encoded the `area` feature into `area_Ampelokipoi-Menemeni`, `area_Evosmos`, and `area_Stavroupoli`.
5. **Binary encoding:** Converted `Superhost`/`Favourite` Yes/No values to 1/0.
6. **Outlier removal:** Removed 10 price outliers to improve model training.

The final cleaned dataset (`airbnb_clean_data.csv`) contains **280 listings** with the following columns:

| Column | Type | Description |
|---|---|---|
| `price` | Float | Price per night |
| `guests`, `beds`, `bedrooms`, `baths` | Float/Int | Property structure |
| `superhost`, `favourite` | Int (0/1) | Host/listing badges |
| `rating`, `reviews` | Float | Rating and review count |
| `latitude`, `longitude` | Float | Coordinates |
| `area_Ampelokipoi-Menemeni`, `area_Evosmos`, `area_Stavroupoli` | Int (0/1) | One-hot encoded area |
| `parking`, `view`, `self_checkin` | Int (0/1) | Amenities parsed from text |

## 🗄️ MongoDB Storage & Queries

Both the raw dataset (`Raw_Data_243_244`) and the cleaned dataset (`Clean_Data_243_244`) were uploaded to a remote MongoDB instance to simulate a real production environment. Four aggregation queries were run via MongoDB Compass:

1. Overall average `price` across all listings
2. Average `rating` grouped by area (Stavroupoli, Ampelokipoi-Menemeni, Evosmos)
3. Listing counts grouped into price buckets (e.g., 0–50, 50–100, …)
4. Top-4 listings sorted by rating and review count (`$sort` + `$limit`)

> **Note:** If you plan to run this yourself, use your own MongoDB connection string and credentials rather than hard-coding them — do not commit connection strings with embedded passwords to a public repository.

## 📈 Exploratory Data Analysis

The notebook answers several analytical questions:

1. **Correlation matrix** between price and property structure (`beds`, `baths`, `bedrooms`, `guests`), visualized as a heatmap.
2. **Top-10 / bottom-10 rated stays**, using a weighted score (`rating * log(1 + reviews)`) to balance rating against review volume, filtered to listings with at least 5 reviews.
3. **Most important features correlated with rating**, comparing structural and qualitative features (`reviews`, `superhost`, `favourite`, `parking`, `view`, `self_checkin`), visualized as a bar chart and heatmap.
4. **Summary statistics per area** (average price, rating, reviews, beds, bedrooms, baths, guests).
5. **Interactive map** of listings (Plotly `scatter_mapbox`), colored by rating and sized by price.

## 🤖 Machine Learning Model

Three regression models were trained and compared for price prediction:

- Linear Regression
- Random Forest
- Gradient Boosting

**Random Forest** was selected as the final model based on MAE and RMSE performance:

```
MAE:  12.34
RMSE: 17.03
```

A key finding: **dataset quality (e.g., outlier removal) had a bigger impact on model performance than tuning the model itself.**

## 🖥️ Streamlit Web App

The app (`app.py`) offers:

- **Price Prediction:** Users input listing characteristics (guests, beds, bedrooms, baths, superhost, favourite, parking, view, self check-in, area) and get an estimated nightly price from the trained model.
- **Visualizations:** A sidebar lets users filter charts by area — "All", "Ampelokipoi-Menemeni", "Evosmos", or "Stavroupoli".

## 🧾 Key Takeaways

1. **Data cleaning is 80% of the work** — turning messy raw text into usable binary features is what lets a model make sense of the data.
2. **NoSQL flexibility is ideal for web scraping** — MongoDB's schema-less design allowed raw, messy scraped data to be stored as-is, leaving structuring for the Pandas stage.
3. **Data quality beats model tuning** — dataset improvements (like outlier removal) mattered more than hyperparameter tuning for the Random Forest model.
4. **A model only creates value once it's accessible** — wrapping the trained model in a Streamlit app turns it into a usable tool rather than just a notebook exercise.
5. **A complete pipeline** — Selenium scrapes, Pandas cleans, MongoDB stores flexibly, and Streamlit delivers the final value to the user.

## 👥 Team

- Konstantina Marina Bletsa (AEM 243)
- Maria Karlaki (AEM 244)

## 🔗 Links

- GitHub repository: [Web-Scraping-Project-Selenium-Beautiful-Soup-Streamlit](https://github.com/kbletsa/Web-Scraping-Project-Selenium-Beautiful-Soup-Streamlit)
