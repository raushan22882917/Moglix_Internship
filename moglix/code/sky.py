import csv
import requests
from bs4 import BeautifulSoup
from io import StringIO

def scrape_urls(urls):
    data = []

    for url in urls:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1', class_='sectionTitle').get_text(strip=True)
        specs = soup.find('div', class_='specification').find_all('li', class_='w-50 my-1')
        
        tech_details = {}
        for i in range(0, len(specs), 2):
            key = specs[i].get_text(strip=True)
            value = specs[i + 1].get_text(strip=True)
            tech_details[key] = value
        
        data.append({
            'url': url,
            'title': title,
            'tech_details': tech_details
        })

    return data

def generate_csv(data):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['URL', 'Title', 'Technical Details'])
    
    for item in data:
        tech_details_str = '; '.join([f'{key}: {value}' for key, value in item['tech_details'].items()])
        writer.writerow([item['url'], item['title'], tech_details_str])
    
    output.seek(0)
    return output

if __name__ == '__main__':
    urls = [
#add multiple urls here
    ]

    scraped_data = scrape_urls(urls)
    csv_data = generate_csv(scraped_data)
    
    with open('scraped_data1.csv', 'wb') as f:
        f.write(csv_data.getvalue().encode('utf-8'))
