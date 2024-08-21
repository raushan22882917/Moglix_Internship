import json
import urllib.parse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
import csv
import time  # Import time module

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

def extract_image_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    image_tags = soup.select('ul.ZqtVYK li img._0DkuPH')
    return [img['src'] for img in image_tags]

def process_urls(api_token, urls, csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Flipkart URL', 'Image Links'])
        
        for url in urls:
            print(f"Processing URL: {url}")
            html_content = fetch_html_with_crawlbase(api_token, url)
            if html_content:
                thumbnail_links = extract_image_links(html_content)
                image_links_str = ', '.join(thumbnail_links)
                writer.writerow([url, image_links_str])
            else:
                print(f"Failed to fetch data for URL: {url}")
            
            time.sleep(5)  # Add a 5-second delay

# List of Flipkart URLs
flipkart_urls = [

]
api_token = 'kk1uwREBvvqR1G1LsCdQrw'
csv_filename = 'vishu.csv'

process_urls(api_token, flipkart_urls, csv_filename)
print(f"Data saved to {csv_filename}")
