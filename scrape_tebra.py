import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urlparse, parse_qs, urlunparse

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

def clean_provider_url(url):
    """Remove the 'lid' query parameter from the URL"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Remove 'lid' if exists
    query_params.pop('lid', None)

    # Reconstruct URL without 'lid'
    clean_query = "&".join(f"{k}={v[0]}" for k, v in query_params.items())
    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, clean_query, parsed_url.fragment))
    
    return new_url

def fetch_phone_numbers(provider_url):
    """Extract all phone numbers from the provider's page"""
    provider_url = clean_provider_url(provider_url)  # Remove 'lid'
    
    response = requests.get(provider_url, headers=HEADERS)
    if response.status_code != 200:
        return "N/A"

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all phone numbers from 'data-phone' attributes in <button> elements
    phone_buttons = soup.select('button[data-phone]')
    phone_numbers = [btn["data-phone"].strip() for btn in phone_buttons if btn.has_attr("data-phone")]

    return phone_numbers if phone_numbers else ["N/A"]

def fetch_location_addresses(provider_url):
    """Extract all location addresses from a provider's page with debug logs."""
    provider_url = clean_provider_url(provider_url)  # Removed 'lid' from provider's url

    response = requests.get(provider_url, headers=HEADERS)

    if response.status_code != 200:
        print("Failed to fetch location addresses.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    addresses = []

    # Find all location sections
    location_sections = soup.find_all('div', class_='row mb-5')

    for section in location_sections:
        address_tag = section.select_one('.practice-address')
        if address_tag:
            address = " ".join(address_tag.stripped_strings)
        else:
            address = "N/A"
        addresses.append(address)

    print(f"Final Extracted Addresses: {addresses}")
    return addresses


# Function to extract provider info
def extract_provider_info(html):
    soup = BeautifulSoup(html, "html.parser")
    providers = []

    for provider in soup.select("article.search-results__providers-provider"):  
        try:
            name = provider.select_one(".provider-name")
            name = name.text.strip() if name else "N/A"

            company = provider.select_one(".provider-specialty")
            company = company.text.strip() if company else "N/A"

            website_tag = provider.select_one("a.article-link")
            website = website_tag["href"] if website_tag else "N/A"

            # locations = provider.select(".provider-location")
            # address = [loc.text.strip() for loc in locations if loc and loc.text.strip()] if locations else "N/A"

            if website.startswith("/"):
                website = f"https://www.tebra.com{website}"

            addresses = fetch_location_addresses(website)
            phone = fetch_phone_numbers(website)
            
            providers.append({
                "Provider Name": name,
                "Company Name": company,
                "Number of Locations": len(addresses) if isinstance(addresses, list) else 0,
                "Location Address": addresses,
                "Phone Number": phone,
                "Website Link": website
            })
        except Exception as e:
            print(f"Error extracting provider info: {e}")

    return providers

# Start Scraping
start = 0
all_providers = []
TOTAL_PROVIDERS = 3200
PER_PAGE = 18

while start < TOTAL_PROVIDERS:
    print(f"Fetching page {start}...")
    html = fetch_page_data(start)
    
    if not html:
        break  
    
    providers = extract_provider_info(html)

    if not providers:
        print("No more providers found. Scraping complete!")
        break
    
    all_providers.extend(providers)
    start += PER_PAGE  
    time.sleep(2)  

# Save Data to JSON file
with open("providers.json", "w", encoding="utf-8") as file:
    json.dump(all_providers, file, indent=4, ensure_ascii=False)

print(f"Total Providers Scraped: {len(all_providers)} (Saved to 'providers.json')")
