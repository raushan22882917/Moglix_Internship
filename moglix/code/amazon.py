import json
import urllib.parse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import csv
import re
import unicodedata
from urllib.parse import urlparse

# Function to fetch HTML content using Crawlbase API
def fetch_html_with_crawlbase(api_token, product_url):
    encoded_url = urllib.parse.quote_plus(product_url)
    api_url = f'https://api.crawlbase.com/?token={api_token}&url={encoded_url}'
    request = Request(api_url)
    
    try:
        response = urlopen(request)
        response_data = response.read().decode('utf-8')
        try:
            data = json.loads(response_data)
            return data.get('body', '')
        except json.JSONDecodeError:
            print("Error: The response is not a valid JSON. Returning raw HTML content.")
            return response_data
    except HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URLError: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def scrape_product(api_token, urls, csv_filename):
    all_products = []

    for url in urls:
        o = {}
        specs_arr = []
        specs_obj = {}

        # Fetch HTML content using Crawlbase API
        html_content = fetch_html_with_crawlbase(api_token, url)
        if not html_content:
            print(f"Failed to fetch page for URL: {url}")
            continue

        soup = BeautifulSoup(html_content, 'html.parser')

        o["url"] = url
        
        # Extract ASIN from URL
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        asin = path_segments[-1] if path_segments[-1] != '' else path_segments[-2]  # Last segment of path
        o["asin"] = asin

        try:
            o["title"] = soup.find('h1', {'id': 'title'}).text.strip()
        except:
            o["title"] = None

        images = re.findall('"hiRes":"(.+?)"', html_content)
        o["images"] = ', '.join(images)  # Flatten image links into a single string

        try:
            o["price"] = soup.find("span", {"class": "a-price"}).find("span").text
        except:
            o["price"] = None

        try:
            o["rating"] = soup.find("i", {"class": "a-icon-star"}).text
        except:
            o["rating"] = None

        specs = soup.find_all("tr", {"class": "a-spacing-small"})

        for spec in specs:
            spanTags = spec.find_all("span")
            specs_obj[spanTags[0].text.strip()] = spanTags[1].text.strip()

        specs_arr.append(specs_obj)
        o["specs"] = json.dumps(specs_arr)  # Convert specs array to JSON string

        # Scrape technical details
        tech_details = {}
        table = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
        if table:
            for row in table.find_all('tr'):
                key = row.find('th', {'class': 'a-color-secondary'}).text.strip()
                value = row.find('td', {'class': 'a-size-base'}).text.strip()
                value = value.replace('\u200e', '')
                value = unicodedata.normalize("NFKD", value)
                tech_details[key] = value
        o["technical_details"] = json.dumps(tech_details)  # Convert tech details to JSON string

        # Scrape about item section
        about_item = []
        about_item_section = soup.find('div', {'id': 'feature-bullets'})
        if about_item_section:
            for li in about_item_section.find_all('li', {'class': 'a-spacing-mini'}):
                about_item.append(li.text.strip())
        o["about_item"] = ', '.join(about_item)  # Flatten about item list into a single string

        # Scrape what's in the box section
        in_the_box = []
        witb_dl = soup.find('li', {'class': 'postpurchase-included-components-list-item'})
        if witb_dl:
            witb_items = witb_dl.find_all('span', {'class': 'a-list-item'})
            for item in witb_items:
                in_the_box.append(item.text.strip())
        o["whats_in_the_box"] = ', '.join(in_the_box)  # Flatten what's in the box list into a single string

        # Scrape product description
        description = soup.find('div', {'id': 'productDescription'})
        if description:
            o["product_description"] = description.text.strip()
        else:
            o["product_description"] = ""
        
        # Scrape additional information
        additional_info = soup.find('div', {'id': 'productDetails_db_sections'})
        if additional_info:
            table = additional_info.find('table', {'id': 'productDetails_detailBullets_sections1'})
            if table:
                additional_data = {}
                for row in table.find_all('tr'):
                    th = row.find('th', {'class': 'a-color-secondary'})
                    td = row.find('td', {'class': 'a-size-base prodDetAttrValue'})
                    if th and td:
                        key = th.text.strip()
                        value = td.text.strip()
                        additional_data[key] = value
                o["additional_information"] = json.dumps(additional_data)  # Convert additional info to JSON string

        all_products.append(o)

    # Save to CSV
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        header = ['url', 'asin', 'title', 'images', 'price', 'rating', 'specs', 'technical_details', 'about_item', 'whats_in_the_box', 'product_description', 'additional_information']
        writer.writerow(header)
        
        for product in all_products:
            row = [
                product.get('url', ''),
                product.get('asin', ''),
                product.get('title', ''),
                product.get('images', ''),
                product.get('price', ''),
                product.get('rating', ''),
                product.get('specs', ''),
                product.get('technical_details', ''),
                product.get('about_item', ''),
                product.get('whats_in_the_box', ''),
                product.get('product_description', ''),
                product.get('additional_information', '')
            ]
            writer.writerow(row)

    print(f"Data saved to {csv_filename}")

# List of Amazon URLs
amazon_urls = [
"https://www.amazon.in/dp/B08ZNP7X91?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMMSYP?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMYKMY?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNLTSZ2?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN7JPP?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNM5BY4?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPVDRD?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNXDX8?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN5NLD?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMQ1TT?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNDCJT?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNRLC1R?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMWL23?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN92JK?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNNR1F4?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPT1KJ?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMCL3J?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPVSDX?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNF8DK?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNLFZ3X?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNLBSHY?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMXMD3?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMT9CV?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNP1MM5?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN2HHR?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMC8Z8?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN681D?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNGFPGV?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNLT9NT?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNM9YRH?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNNLC15?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNNF7TD?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPPB63?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNN4ZCX?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNLQHR?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN8D6G?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMMR3B?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN2T8N?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNM9DFX?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN48GM?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPTVK1?ref=myi_title_dp",
"https://www.amazon.in/dp/B09CQ2X6YM?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN7VN2?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNF3Y6?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNGWWBS?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN1NWH?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNRN2T?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNQ9KJ?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNLCQD9?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNMZDLQ?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNP3NF4?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNMTRK3?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNN29DG?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNNZT69?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNMJX5X?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNHFJV3?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNQDX8Z?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNRQ4ZV?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNN64RZ?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNLLSLQ?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNNDLM4?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNJTVB7?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B08ZNKYXH7?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNRS12M?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNVGZF?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNGF4S7?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNLY4D8?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNNCLZ3?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNQ531J?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPKMRK?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNPW4XW?ref=myi_title_dp",
"https://www.amazon.in/dp/B08ZNN1G5B?ref=myi_title_dp",
"https://www.amazon.in/dp/B0D6BTFYQF?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B0D6BV3K4C?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B0D6BYCSM4?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B0D6BX3TGR?ref=myi_title_dp&th=1",
"https://www.amazon.in/dp/B0D6BTKBRW?ref=myi_title_dp&th=1",


]

api_token = 'kk1uwREBvvqR1G1LsCdQrw'
scrape_product(api_token, amazon_urls, 'amazon_products1.csv')
