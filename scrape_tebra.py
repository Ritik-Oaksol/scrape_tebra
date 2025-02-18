import requests
import json
from bs4 import BeautifulSoup

# URL of the search results page
url = 'https://www.tebra.com/care/search?neighborhood=&city=None&state=None&zip=&lat=&lng=&type=specialty&keyword=Physical+Therapist&lookup='

# Headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Send GET request
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all providers
    providers = soup.find_all('article', class_='search-results__providers-provider')

    extracted_data = []

    for provider in providers:
        name = provider.find('span', class_='provider-name d-block')
        specialty = provider.find('span', class_='provider-specialty d-block py-2')
        address = provider.find('span', class_='provider-location d-block')
        rating = provider.find('span', class_='ratings__rating')
        review_count = provider.find('span', class_='ratings__count')

        provider_data = {
            "name": name.text.strip() if name else "N/A",
            "specialty": specialty.text.strip() if specialty else "N/A",
            "address": address.text.strip() if address else "N/A",
            "rating": rating.text.strip() if rating else "N/A",
            "review_count": review_count.text.strip() if review_count else "N/A"
        }

        extracted_data.append(provider_data)

    # Save data to JSON
    with open("tebra_providers.json", "w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, indent=4, ensure_ascii=False)

    print("✅ Data extraction complete! Saved as 'tebra_providers.json'")

else:
    print(f"❌ Failed to fetch data. Status Code: {response.status_code}")
