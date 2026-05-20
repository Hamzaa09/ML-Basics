import requests
from bs4 import BeautifulSoup
import csv
import time
import json
import re
import pandas as pd

# Step 1: Settings

URL = "https://www.pakwheels.com/used-cars/old/430603"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}

# Step 2: Scrape from one page

def scrape_one_page(page_number):
    
    url = f"{URL}?page={page_number}"
    print(f"\nFetching page {page_number}...")

    response = requests.get(url, headers=HEADERS, timeout=15)

    if response.status_code != 200:
        print(f"Error! Status code: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # data lies in <script type="application/ld+json">
    script_tags = soup.find_all("script", type="application/ld+json")

    data_list = []

    i = 0
    for tag in script_tags:
        try:
            data = json.loads(tag.string)
        except:
            continue

        if data.get("@type") not in (["Product"], "Product"):
            continue

        # extract data
        brand        = data.get("manufacturer", "")
        fuel_type    = data.get("fuelType", "")
        transmission = data.get("vehicleTransmission", "")

        # Mileage: "258,000 km" → sirf number chahiye
        mileage_raw  = data.get("mileageFromOdometer", "")
        mileage_km   = re.sub(r"[^\d]", "", mileage_raw)  # sirf digits

        # Engine: "1800cc" → sirf number
        engine_raw   = data.get("vehicleEngine", {}).get("engineDisplacement", "")
        engine_cc    = re.sub(r"[^\d]", "", engine_raw)

        # Price
        price_pkr    = data.get("offers", {}).get("price", "")

        # City
        parent = tag.parent
        city         = parent.find("ul", class_="search-vehicle-info").li.text.strip() if parent.find("ul", class_="search-vehicle-info") else None
        model        = parent.find("ul", class_="search-vehicle-info-2").li.text.strip() if parent.find("ul", class_="search-vehicle-info-2") else None
        
        name = parent.h3.text.strip() if parent.h3 else None
        
        time = parent.find('div', class_='dated').text.strip() if parent.find('div', class_='dated') else None
    
        data_list.append([name, brand, model, mileage_km, fuel_type, transmission, engine_cc, city, price_pkr, time])
        i += 1
        print(f"  ✅ {brand} {model} | {city} | PKR {price_pkr}")

    print(f"{i} cars found on page {page_number}")
    return data_list

# Step 3: CSV

def save_to_csv(all_cars, filename="pakwheels_data.csv"):
    """First make panda frame, then save to CSV"""

    columns = ["name", "brand", "model", "mileage_km", "fuel_type",
               "transmission", "engine_cc", "city", "price_pkr", "time"]
    
    df = pd.DataFrame(all_cars, columns=columns)
    df.to_csv(f"./used_cars_price_predictor_project/data/{filename}", index=False)

    print(f"\n✅ Data saved to {filename} | Total cars: {len(df)}")


# Step 4: Main program

def main():
    PAGES_TO_SCRAPE = 1000
    DELAY_SECONDS   = 0
    OUTPUT_FILE     = "pakwheels_data.csv"

    print("Scraping Started...")
    print(f"Pages: {PAGES_TO_SCRAPE} | Delay: {DELAY_SECONDS}s\n")

    cars = {
        "name":         [],
        "brand":        [],
        "model":        [],
        "mileage_km":   [],
        "fuel_type":    [],
        "transmission": [],
        "engine_cc":    [],
        "city":         [],
        "price_pkr":    [],
        "time":         []
    }

    for page in range(1, PAGES_TO_SCRAPE + 1):
        car_data = scrape_one_page(page)

        for i in range(len(car_data)):
            for key, value in zip(cars.keys(), car_data[i]):
                cars[key].append(value)     
        time.sleep(DELAY_SECONDS)  
        
    save_to_csv(cars, OUTPUT_FILE)
    print("\n✅ Scraping complete!")


if __name__ == "__main__":
    main()