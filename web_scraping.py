import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# =========================
# 1. ΡΥΘΜΙΣΕΙΣ
# =========================

areas = {
    "Ampelokipoi-Menemeni": "https://www.airbnb.gr/s/Ampelokipoi--Menemeni--Greece/homes",
    "Evosmos": "https://www.airbnb.gr/s/Evosmos--Thessaloniki--Greece/homes",
    "Stavroupoli": "https://www.airbnb.gr/s/Stavroupoli--Thessaloniki--Greece/homes"
}

MAX_PAGES_PER_AREA = 1
OUTPUT_CSV = "airbnb_listings.csv"

# =========================
# 2. SELENIUM SETUP
# =========================

chrome_options = Options()
# chrome_options.add_argument("--headless=new")  # αν θέλεις κρυφό browser, βγάλε το σχόλιο
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 15)


# =========================
# 3. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# =========================

def get_body_text():
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except:
        return ""


def normalize_room_url(url):
    """ if not url:
         return None
     clean = url.split("?")[0]
     if "/rooms/" in clean:
         return clean
     return None"""
    if not url:
        return None

    if "/rooms/" in url:
        return url.strip()

    return None


def click_cookie_if_exists():
    possible_xpaths = [
        "//button[contains(., 'Accept')]",
        "//button[contains(., 'Αποδοχή')]",
        "//button[contains(., 'Allow all')]",
        "//button[contains(., 'Να επιτραπούν όλα')]"
    ]
    for xp in possible_xpaths:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            return
        except:
            pass


def collect_links_from_current_page():
    page_links = set()

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/rooms/"]')

    for e in elements:
        try:
            href = e.get_attribute("href")
            clean_href = normalize_room_url(href)
            if clean_href:
                page_links.add(clean_href)
        except StaleElementReferenceException:
            continue

    return page_links


def go_to_page(page_number):
    selectors = [
        (By.XPATH, f"//a[normalize-space()='{page_number}']"),
        (By.XPATH, f"//button[normalize-space()='{page_number}']"),
        (By.XPATH, f"//*[@aria-label='{page_number}']"),
        (By.XPATH, f"//a[contains(@aria-label, '{page_number}')]"),
        (By.XPATH, f"//button[contains(@aria-label, '{page_number}')]")
    ]

    for by, selector in selectors:
        try:
            elem = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((by, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", elem)
            time.sleep(5)
            return True
        except:
            continue

    return False


def close_dialog_if_open():
    close_selectors = [
        (By.XPATH, "//button[@aria-label='Close']"),
        (By.XPATH, "//button[@aria-label='Κλείσιμο']"),
        (By.XPATH, "//button[contains(., 'Close')]"),
        (By.XPATH, "//button[contains(., 'Κλείσιμο')]")
    ]

    for by, selector in close_selectors:
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((by, selector))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            return
        except:
            continue

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        time.sleep(1)
    except:
        pass


# =========================
# 4. PARSING ΣΤΟ ROOM PAGE
# =========================

def parse_host_name():
    """
    Θέλουμε το όνομα μετά το:
    Οικοδεσπότης: Polina
    ή
    Hosted by Maria
    """
    body_text = get_body_text()

    patterns = [
        r"Οικοδεσπότης:\s*([^\n\r]+)",
        r"Hosted by\s+([^\n\r]+)"
    ]

    for pattern in patterns:
        m = re.search(pattern, body_text, re.IGNORECASE)
        if m:
            host = m.group(1).strip()
            host = host.split("Superhost")[0].strip()
            host = host.split("·")[0].strip()
            return host

    return ""


def click_total_price():
    """
    Πατάει στη μεγάλη τιμή '€ XXX συνολικά'
    για να ανοίξει η Ανάλυση τιμής.
    """
    possible_xpaths = [
        "//*[contains(text(),'συνολικά') and contains(text(),'€')]",
        "//div[contains(text(),'συνολικά') and contains(text(),'€')]",
        "//span[contains(text(),'συνολικά') and contains(text(),'€')]",
        "//*[contains(text(),'total') and contains(text(),'€')]"
    ]

    for xp in possible_xpaths:
        try:
            elem = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", elem)
            time.sleep(2)
            return True
        except:
            continue

    return False


# ----------------------------------------------------------------------------------------------------------
def clean_price_value(text):
    if not text:
        return ""

    text = text.strip()
    text = text.replace("€", "").replace("\xa0", " ").strip()

    # κράτα μόνο αριθμούς, κόμμα, τελεία
    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not m:
        return ""

    return m.group(1).replace(",", ".")


# ------------------------------------------------------------------------------------------------------------
def parse_price_per_night():
    # 1. Πάτημα στη συνολική τιμή
    clicked = False
    total_price_xpaths = [
        "//*[contains(text(),'συνολικά') and contains(text(),'€')]",
        "//*[contains(text(),'total') and contains(text(),'€')]"
    ]

    for xp in total_price_xpaths:
        try:
            elems = driver.find_elements(By.XPATH, xp)
            for elem in elems:
                try:
                    if elem.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", elem)
                        clicked = True
                        time.sleep(2)
                        break
                except:
                    continue
            if clicked:
                break
        except:
            continue

    if not clicked:
        return ""

    # 2. Περίμενε να εμφανιστεί το popup
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Ανάλυση τιμής') or contains(text(),'Price breakdown')]")
            )
        )
        time.sleep(2)
    except:
        close_dialog_if_open()
        return ""

    # 3. Βρες το container που περιέχει τον τίτλο "Ανάλυση τιμής"
    containers = []
    try:
        headers = driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'Ανάλυση τιμής') or contains(text(),'Price breakdown')]"
        )

        for h in headers:
            try:
                # ανεβαίνουμε σε κοντινό parent container
                parent = h.find_element(By.XPATH, "./ancestor::*[self::div or self::section][1]")
                containers.append(parent)
            except:
                pass
    except:
        pass

    # 4. Δοκίμασε να πάρεις γραμμές από το container
    for container in containers:
        try:
            lines = [x.strip() for x in container.text.splitlines() if x.strip()]

            # ψάξε γραμμή με διανυκτερεύσεις ή nights
            for i, line in enumerate(lines):
                lower = line.lower()

                # περίπτωση Α: όλο σε μία γραμμή
                if ("διανυκτερεύ" in lower or "night" in lower) and "x" in line:
                    price = clean_price_value(line.split("x")[-1])
                    if price:
                        close_dialog_if_open()
                        return price

                # περίπτωση Β: label σε μία γραμμή, τιμή στην επόμενη
                if "διανυκτερεύ" in lower or "night" in lower:
                    if i + 1 < len(lines):
                        price = clean_price_value(lines[i + 1])
                        if price:
                            close_dialog_if_open()
                            return price
        except:
            continue

    # 5. Fallback: ψάξε σε όλα τα εμφανή στοιχεία του popup
    try:
        popup_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'διανυκτερεύ') or contains(text(),'nights') or contains(text(),'€')]"
        )

        visible_texts = []
        for el in popup_elements:
            try:
                if el.is_displayed():
                    txt = el.text.strip()
                    if txt:
                        visible_texts.append(txt)
            except:
                continue

        # debug
        print("VISIBLE POPUP TEXTS:", visible_texts)

        # πρώτα ψάξε γραμμή με x
        for txt in visible_texts:
            lower = txt.lower()
            if ("διανυκτερεύ" in lower or "night" in lower) and "x" in txt:
                price = clean_price_value(txt.split("x")[-1])
                if price:
                    close_dialog_if_open()
                    return price

        # μετά ψάξε pattern "διανυκτερεύσεις" και πάρε την επόμενη τιμή
        for idx, txt in enumerate(visible_texts):
            lower = txt.lower()
            if "διανυκτερεύ" in lower or "night" in lower:
                if idx + 1 < len(visible_texts):
                    price = clean_price_value(visible_texts[idx + 1])
                    if price:
                        close_dialog_if_open()
                        return price
    except:
        pass

    close_dialog_if_open()
    return ""


# ----------------------------------------------------------επόμενος κώδικας-------------------------------------
def parse_guests_beds_bedrooms_baths():
    """
    Π.χ.
    6 επισκέπτες · 2 υπνοδωμάτια · 3 κρεβάτια · 1 μπάνιο
    ή
    1 ιδιωτικό μπάνιο
    """
    body_text = get_body_text()

    def find_first(patterns):
        for p in patterns:
            m = re.search(p, body_text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    guests = find_first([
        r"(\d+)\s+επισκέπτες",
        r"(\d+)\s+guests"
    ])

    bedrooms = find_first([
        r"(\d+)\s+υπνοδωμάτια",
        r"(\d+)\s+υπνοδωμάτιο",
        r"(\d+)\s+bedrooms?",
        r"(\d+)\s+bedroom"
    ])

    beds = find_first([
        r"(\d+)\s+κρεβάτια",
        r"(\d+)\s+κρεβάτι",
        r"(\d+)\s+beds?",
        r"(\d+)\s+bed"
    ])

    baths = find_first([
        r"(\d+(?:[.,]\d+)?)\s+ιδιωτικό\s+μπάνιο",
        r"(\d+(?:[.,]\d+)?)\s+ιδιωτικά\s+μπάνια",
        r"(\d+(?:[.,]\d+)?)\s+μπάνια",
        r"(\d+(?:[.,]\d+)?)\s+μπάνιο",
        r"(\d+(?:[.,]\d+)?)\s+private\s+bath",
        r"(\d+(?:[.,]\d+)?)\s+private\s+baths",
        r"(\d+(?:[.,]\d+)?)\s+baths?",
        r"(\d+(?:[.,]\d+)?)\s+bathroom"
    ])

    return guests, beds, bedrooms, baths


def parse_review_info():
    """
    Θέλουμε:
    review_index = 4,9
    number_of_reviews = 126
    """
    body_text = get_body_text()

    patterns = [
        r"([0-5][\.,]\d{1,2}).{0,30}?(\d+)\s+Κριτικές",
        r"([0-5][\.,]\d{1,2}).{0,30}?(\d+)\s+κριτικές",
        r"([0-5][\.,]\d{1,2}).{0,30}?(\d+)\s+Reviews",
        r"([0-5][\.,]\d{1,2}).{0,30}?(\d+)\s+reviews"
    ]

    for pattern in patterns:
        m = re.search(pattern, body_text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip(), m.group(2).strip()

    return "", ""


def open_amenities_modal():
    """
    Πατάει το κουμπί:
    Εμφάνιση και των 30 παροχών
    ή
    Show all 43 amenities / benefits
    """
    possible_xpaths = [
        "//button[contains(., 'Εμφάνιση και των')]",
        "//a[contains(., 'Εμφάνιση και των')]",
        "//button[contains(., 'Show all')]",
        "//a[contains(., 'Show all')]",
        "//button[contains(., 'amenities')]",
        "//button[contains(., 'benefits')]"
    ]

    for xp in possible_xpaths:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            return True
        except:
            continue

    return False


def parse_characteristics():
    """
        Παίρνει ΜΟΝΟ τους τίτλους των highlights κάτω από τον οικοδεσπότη.
        Δεν κρατά labels/headers όπως:
        - Δυνατά σημεία καταχώρησης
        - Στοιχεία εγγραφής
        - Περισσότερα
        """

    body_text = get_body_text()
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]

    # Βρίσκουμε από πού να ξεκινήσουμε: μετά τον οικοδεσπότη
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Οικοδεσπότης:") or line.lower().startswith("hosted by"):
            start_idx = i + 1
            break

    if start_idx is None:
        return ""

    # Βρίσκουμε πού να σταματήσουμε: πριν από άλλο section
    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        lower = lines[i].lower()
        if (
                lower.startswith("τι προσφέρει αυτός ο χώρος")
                or lower.startswith("what this place offers")
                or lower.startswith("ορισμένες πληροφορίες έχουν μεταφραστεί")
                or lower.startswith("some information has been automatically translated")
        ):
            end_idx = i
            break

    block = lines[start_idx:end_idx]

    blacklist_exact = {
        "Δυνατά σημεία καταχώρησης",
        "Listing highlights",
        "Στοιχεία εγγραφής",
        "More",
        "Περισσότερα",
        "Επιλογή επισκεπτών",
        "Guest favorite",
        "Guest favourite",
        "Superhost",
        "Κριτικές",
        "Reviews"
    }

    blacklist_contains = [
        "οικοδεσπότης:",
        "hosted by",
        "χρόνια εμπειρίας ως οικοδεσπότης",
        "years hosting",
        "ένα από τα πιο αγαπημένα καταλύματα",
        "according to guests",
        "σύμφωνα με τους επισκέπτες",
        "οι superhost είναι",
        "superhosts are",
        "πρόσφατοι επισκέπτες",
        "οι επισκέπτες που έμειναν εδώ",
        "οι επισκέπτες λένε",
        "απολαύστε τη θέα",
        "ολοκληρώστε την άφιξή σας",
        "αυτό είναι ένα από τα λίγα μέρη",
        "αυτό το κατάλυμα έχει υψηλή βαθμολογία",
        "δυνατά σημεία καταχώρησης",
        "στοιχεία εγγραφής",
        "περισσότερα"
    ]

    wanted_keywords = [
        "check-in",
        "superhost",
        "θέα",
        "ηρεμία",
        "πάρκινγκ",
        "καφές",
        "τοποθεσία",
        "άφιξης",
        "self check-in",
        "great location",
        "quiet",
        "parking",
        "coffee"
    ]

    results = []

    for line in block:
        lower = line.lower()

        if line in blacklist_exact:
            continue

        if any(bad in lower for bad in blacklist_contains):
            continue

        # αγνόησε καθαρές περιγραφές / μακροσκελείς γραμμές
        if len(line) > 45:
            continue

        # αγνόησε αριθμούς / ratings
        if re.fullmatch(r"[\d\.,]+", line):
            continue

        # κράτα μόνο τίτλους που μοιάζουν με πραγματικά characteristics
        if any(keyword in lower for keyword in wanted_keywords):
            results.append(line)

    # αφαίρεση διπλοτύπων με διατήρηση σειράς
    cleaned = []
    seen = set()

    for item in results:
        if item not in seen:
            seen.add(item)
            cleaned.append(item)

    return " | ".join(cleaned)


def parse_lat_lng():
    page_source = driver.page_source

    patterns = [
        r'"lat"\s*:\s*([0-9]+\.[0-9]+).*?"lng"\s*:\s*([0-9]+\.[0-9]+)',
        r'"latitude"\s*:\s*([0-9]+\.[0-9]+).*?"longitude"\s*:\s*([0-9]+\.[0-9]+)',
        r'center=([0-9]+\.[0-9]+)%2C([0-9]+\.[0-9]+)',
        r'location=([0-9]+\.[0-9]+),([0-9]+\.[0-9]+)'
    ]

    for p in patterns:
        m = re.search(p, page_source, re.DOTALL)
        if m:
            return m.group(1), m.group(2)

    return "", ""


def scrape_listing(area_name, room_url):
    driver.get(room_url)
    time.sleep(6)

    body_text = get_body_text().lower()

    price_per_night = parse_price_per_night()
    print("PRICE FOUND:", price_per_night, "| URL:", room_url)
    guests, beds, bedrooms, baths = parse_guests_beds_bedrooms_baths()
    review_index, number_of_reviews = parse_review_info()
    host_name = parse_host_name()
    characteristics = parse_characteristics()
    print("CHARACTERISTICS:", characteristics)
    latitude, longitude = parse_lat_lng()

    superhost = "Yes" if "superhost" in body_text else "No"
    guest_favourite = "Yes" if (
            "επιλογή επισκεπτών" in body_text or
            "guest favorite" in body_text or
            "guest favourite" in body_text
    ) else "No"

    return {
        "area": area_name,
        "room_url": room_url,
        "price_per_night": price_per_night,
        "guests": guests,
        "beds": beds,
        "bedrooms": bedrooms,
        "baths": baths,
        "superhost": superhost,
        "guest_favourite": guest_favourite,
        "review_index": review_index,
        "number_of_reviews": number_of_reviews,
        "host_name": host_name,
        "characteristics": characteristics,
        "latitude": latitude,
        "longitude": longitude
    }


# =========================
# 5. ΣΥΛΛΟΓΗ LINKS ΑΝΑ ΠΕΡΙΟΧΗ
# =========================

def collect_room_links_for_area(area_name, area_url, max_pages=10):
    print(f"\n===== {area_name} =====")
    driver.get(area_url)
    time.sleep(8)
    click_cookie_if_exists()

    area_links = set()

    first_page_links = collect_links_from_current_page()
    area_links.update(first_page_links)
    print(f"Σελίδα 1 -> {len(first_page_links)} links")

    for page_num in range(2, max_pages + 1):
        moved = go_to_page(page_num)
        if not moved:
            print(f"Δεν μπόρεσα να πάω στη σελίδα {page_num}. Σταματάω εδώ.")
            break

        time.sleep(4)
        page_links = collect_links_from_current_page()
        area_links.update(page_links)
        print(f"Σελίδα {page_num} -> {len(page_links)} links | σύνολο μέχρι τώρα: {len(area_links)}")

    return sorted(area_links)


# =========================
# 6. ΚΥΡΙΟ ΜΕΡΟΣ
# =========================

all_room_links = []

for area_name, area_url in areas.items():
    links = collect_room_links_for_area(area_name, area_url, MAX_PAGES_PER_AREA)
    for link in links:
        all_room_links.append((area_name, link))

print(f"\nΣυνολικά room links: {len(all_room_links)}")

rows = []
counter = 1

for area_name, room_url in all_room_links:
    print(f"[{counter}/{len(all_room_links)}] Scraping -> {room_url}")
    try:
        row = scrape_listing(area_name, room_url)
        rows.append(row)
    except Exception as e:
        print("Σφάλμα στο listing:", room_url)
        print("Error:", e)
    counter += 1

driver.quit()

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\nΟλοκληρώθηκε. Αποθηκεύτηκε το αρχείο: {OUTPUT_CSV}")