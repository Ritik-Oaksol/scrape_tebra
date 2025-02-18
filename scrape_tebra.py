import requests
from bs4 import BeautifulSoup
import time
import json

# Base URL with pagination parameter
BASE_URL = "https://www.tebra.com/care/search?neighborhood=&city=None&state=None&zip=&lat=&lng=&type=specialty&keyword=Physical+Therapist&lookup=&start={}"

# Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# Function to fetch page data
def fetch_page_data(start):
    url = BASE_URL.format(start)
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch page {start} (Status: {response.status_code})")
        return None
    
    return response.text

# Function to extract provider info
def extract_provider_info(html):
    soup = BeautifulSoup(html, "html.parser")
    providers = []

    for provider in soup.select("article.search-results__providers-provider"):  # Adjust selector if needed
        try:
            name = provider.select_one(".provider-name").text.strip() if provider.select_one(".provider-name") else "N/A"
            company = provider.select_one(".provider-specialty").text.strip() if provider.select_one(".provider-specialty") else "N/A"
            locations = provider.select(".provider-location")
            num_locations = len(locations)
            address = locations[0].text.strip() if locations else "N/A"
            phone = provider.select_one(".provider-phone").text.strip() if provider.select_one(".provider-phone") else "N/A"
            website = provider.select_one("a.article-link")["href"] if provider.select_one("a.article-link") else "N/A"
            
            providers.append({
                "Provider Name": name,
                "Company Name": company,
                "Number of Locations": num_locations,
                "Location Address": address,
                "Phone Number": phone,
                "Website Link": f"https://www.tebra.com{website}" if website.startswith("/") else website
            })
        except Exception as e:
            print(f"Error extracting provider info: {e}")

    return providers

# Start Scraping from Page 0
start = 0
all_providers = []
TOTAL_PROVIDERS = 3200
PER_PAGE = 18

while start < TOTAL_PROVIDERS:
    print(f"Fetching page {start}...")
    html = fetch_page_data(start)
    
    if not html:
        break  # Stop if request fails
    
    providers = extract_provider_info(html)

    if not providers:
        print("No more providers found. Scraping complete!")
        break
    
    all_providers.extend(providers)
    start += PER_PAGE  # Move to next page
    time.sleep(2)  # Respectful delay to avoid blocking

# Save Data to JSON file
with open("providers_data.json", "w", encoding="utf-8") as file:
    json.dump(all_providers, file, indent=4, ensure_ascii=False)

print(f"Total Providers Scraped: {len(all_providers)} (Saved to 'providers_data.json')")
