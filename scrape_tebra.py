import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urlparse, parse_qs, urlunparse

# Base URL for scraping specialties
BASE_URL = "https://www.tebra.com/care/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

async def fetch_page(session, url):
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()

async def scrape_specialties():
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, BASE_URL)
        soup = BeautifulSoup(html, "html.parser")
        
        specialties = {}
        specialty_elements = soup.select(".overlay-specialty")
        content_elements = soup.select(".browse-overlay-content")

        for specialty, content in zip(specialty_elements, content_elements):
            specialty_name = specialty.text.strip()
            specialties[specialty_name] = None
            
            ol = content.select_one("ol")
            if ol:
                first_li = ol.select_one("li a")
                if first_li:
                    full_url = first_li["href"]
                    cleaned_url = re.sub(r"/[^/]+/$", "/", full_url)
                    specialties[specialty_name] = cleaned_url

        return specialties

def clean_provider_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params.pop('lid', None)
    clean_query = "&".join(f"{k}={v[0]}" for k, v in query_params.items())
    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, clean_query, parsed_url.fragment))
    return new_url

def fetch_phone_numbers(provider_url):
    provider_url = clean_provider_url(provider_url)
    response = requests.get(provider_url, headers=HEADERS)
    if response.status_code != 200:
        return ["N/A"]

    soup = BeautifulSoup(response.text, "html.parser")
    phone_buttons = soup.select('button[data-phone]')
    phone_numbers = [btn["data-phone"].strip() for btn in phone_buttons if btn.has_attr("data-phone")]

    return phone_numbers if phone_numbers else ["N/A"]

def fetch_location_addresses(provider_url):
    provider_url = clean_provider_url(provider_url)
    response = requests.get(provider_url, headers=HEADERS)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    addresses = []

    location_sections = soup.find_all('div', class_='row mb-5')
    for section in location_sections:
        address_tag = section.select_one('.practice-address')
        if address_tag:
            address = " ".join(address_tag.stripped_strings)
        else:
            address = "N/A"
        addresses.append(address)

    return addresses

def fetch_provider_details(search_url):
    """Fetch providers from a specialty search page"""
    start = 0
    PER_PAGE = 18
    TOTAL_PROVIDERS = 100  # Can be updated dynamically

    providers = []
    
    while start < TOTAL_PROVIDERS:
        print(f"Fetching providers from {search_url} (start={start})")
        response = requests.get(f"{search_url}?&start={start}", headers=HEADERS)

        if response.status_code != 200:
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        provider_list = soup.select("article.search-results__providers-provider")

        if not provider_list:
            break

        for provider in provider_list:
            try:
                name = provider.select_one(".provider-name")
                name = name.text.strip() if name else "N/A"

                company = provider.select_one(".provider-specialty")
                company = company.text.strip() if company else "N/A"

                website_tag = provider.select_one("a.article-link")
                website = website_tag["href"] if website_tag else "N/A"
                
                if website.startswith("/"):
                    website = f"https://www.tebra.com{website}"

                addresses = fetch_location_addresses(website)
                phone = fetch_phone_numbers(website)

                providers.append({
                    "Provider Name": name,
                    "Company Name": company,
                    "Number of Locations": len(addresses),
                    "Location Address": addresses,
                    "Phone Number": phone,
                    "Website Link": website
                })
            except Exception as e:
                print(f"Error extracting provider info: {e}")

        start += PER_PAGE
        time.sleep(2)

    return providers

async def main():
    specialties = await scrape_specialties()
    
    all_data = {}

    for specialty, search_url in specialties.items():
        if not search_url:
            continue

        print(f"Scraping providers for {specialty}...")
        providers = fetch_provider_details(search_url)
        all_data[specialty] = providers

    with open("providers_data.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4, ensure_ascii=False)

    print(f"Scraping complete! Data saved to 'providers_data.json'")

asyncio.run(main())
