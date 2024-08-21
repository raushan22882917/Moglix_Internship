from flask import Flask, request, send_file, redirect, url_for, render_template, make_response,abort,Response,flash
from rembg import remove
from PIL import Image, ImageEnhance
import os
import numpy as np
import csv
import requests
from io import BytesIO, StringIO
import zipfile
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import re
from werkzeug.utils import secure_filename
import unicodedata
import io
import camelot
import secrets
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/remove')
def index():
    return render_template('backgroundremove.html')

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
##########################################################background remove####################################################
processed_images = set()

@app.route('/process_csv', methods=['POST'])
def process_csv():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    option = request.form.get('option')

    if file and option:
        csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(csv_path)
        
        with open(csv_path, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)  # Skip the header row
            for row in csvreader:
                if row:  # Make sure the row is not empty
                    image_url = row[0]
                    image_name = row[1]
                    process_image_from_url(image_url, image_name, option)
        
        # Create a zip file of all processed images
        zip_filename = "processed_images.zip"
        zip_path = os.path.join(PROCESSED_FOLDER, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(PROCESSED_FOLDER):
                for file in files:
                    if file != zip_filename:
                        zipf.write(os.path.join(root, file), file)

        # Clean up processed images directory
        clean_processed_images()

        return redirect(url_for('download_file', filename=zip_filename))

def process_image_from_url(url, name, option):
    global processed_images
    response = requests.get(url)
    if response.status_code == 200:
        input_image = Image.open(BytesIO(response.content))
        
        if option == 'original':
            output_image = input_image
        
        elif option == 'background_remove':
            # Enhance image quality before background removal
            input_image = enhance_image_quality(input_image)
            # Remove background
            output_image = remove(input_image)
        
        elif option == 'resize':
            # Resize image to 500x500
            output_image = input_image.resize((500, 500), Image.LANCZOS)
            # Enhance image quality after resizing
            output_image = enhance_image_quality(output_image)
        
        elif option == 'background_remove_resize':
            # Enhance image quality before background removal
            input_image = enhance_image_quality(input_image)
            # Remove background
            output_image = remove(input_image)
            # Resize image to 500x500
            output_image = output_image.resize((500, 500), Image.LANCZOS)
            # Enhance image quality after resizing
            output_image = enhance_image_quality(output_image)
        
        # Handle transparency and save as JPEG
        if output_image.mode in ("RGBA", "LA") or (output_image.mode == "P" and "transparency" in output_image.info):
            # Create a white background image
            white_background = Image.new("RGB", output_image.size, (255, 255, 255))
            white_background.paste(output_image, mask=output_image.split()[3])  # 3 is the alpha channel
            output_image = white_background
        else:
            output_image = output_image.convert("RGB")
        
        # Save the processed image as JPG
        output_filename = f"{name}.jpg"
        if output_filename not in processed_images:  # Avoid duplicates
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            output_image.save(output_path, 'JPEG')
            processed_images.add(output_filename)

def enhance_image_quality(image):
    # Enhance image quality
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(1)  # Increase contrast by 50%
    return enhanced_image

def clean_processed_images():
    for filename in os.listdir(PROCESSED_FOLDER):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            os.remove(os.path.join(PROCESSED_FOLDER, filename))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)

####################################################################################Brand Checking###################################

e_commerce_sites = [
    "amazon", "ebay", "flipkart", "walmart", "indiamart", "industrybuying",
    "bajajmall", "gadgets360", "gloriaexports", "surginatal", "industrylots",
    "shakedeal", "loytec", "lpsupports", "arihanthelmets", "cazander", "justdeal",
    "georgee", "luminX", "Rbimart", "Exapro", "instrukart", "jiomart",
    "Biomedsuppliers", "laxmiusedmachine", "m5stack", "Maanyaboilers",
    "dentalexpress", "toolworld", "machcity", "macons", "madhavententerprise",
    "madrabbit", "kittal-tool", "3idea", "magiclights", "mahakoshalrefractories",
    "maharajawhiteline", "bigbasket", "maheklite", "makemytrip", "tools",
    "malavales", "meesho", "jugalindia", "mallcom", "llemanufacturing", "mamta",
    "exparo", "generatorsource", "hilcoindustrial", "dsatec", "usedmachineindia",
    "exapro", "margacipta", "tradeindia", "cogliandro", "jlwforce", "madeinchina",
    "marlefans", "martor", "offimart", "masiasmaquinaria", "masimo"
]

# Function to search for a brand on Google and return the search results
def search_google(brand_name):
    search_url = f"https://www.google.com/search?q={brand_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print("Failed to fetch search results.")
        return None

# Function to extract e-commerce links from Google search results
def extract_ecommerce_links(search_results):
    if search_results is None:
        return {}

    soup = BeautifulSoup(search_results, 'html.parser')
    links = soup.find_all('a')
    ecommerce_links = {}

    for link in links:
        href = link.get('href')
        if href:
            for site in e_commerce_sites:
                if site in href:
                    if site not in ecommerce_links:
                        ecommerce_links[site] = href
                        break

    return ecommerce_links

# Function to check if a given brand is available on any of the e-commerce platforms
def check_brand_on_ecommerce(brand_name):
    search_results = search_google(brand_name)
    ecommerce_links = extract_ecommerce_links(search_results)

    if ecommerce_links:
        return "Available", ecommerce_links
    else:
        return "Not Available", {}

def process_csv(file):
    brand_names = []
    try:
        csv_data = file.stream.read().decode("utf-8")
        csv_reader = csv.DictReader(StringIO(csv_data))
        if 'Brand Name' not in csv_reader.fieldnames:
            print("Error: CSV file does not contain 'Brand Name' column.")
            return None
        for row in csv_reader:
            brand_names.append(row['Brand Name'])
        return brand_names
    except Exception as e:
        print("Error processing CSV:", e)
        return None


@app.route('/avability', methods=['GET', 'POST'])
def csvfile():
    if request.method == 'POST':
        file = request.files['csv_file']
        if file.filename == '':
            return render_template('brand.html', availability=None)

        brand_names = process_csv(file)
        if brand_names:
            results = []
            for brand_name in brand_names:
                availability, links = check_brand_on_ecommerce(brand_name)
                if links:
                    for site, link in links.items():
                        results.append([brand_name, site, link, availability])
                else:
                    results.append([brand_name, '', '', availability])

            csv_output = StringIO()
            writer = csv.writer(csv_output)
            writer.writerow(['Brand Name', 'E-commerce Site', 'Link', 'Availability'])
            writer.writerows(results)
            csv_output.seek(0)
            return render_template('brand.html', availability="Results Ready", csv_file="data:text/csv;charset=utf-8," + csv_output.getvalue())
        else:
            return render_template('brand.html', availability="Error processing CSV file", csv_file=None)

    return render_template('brand.html', availability=None, csv_file=None)



    
####################################################################Scrap Industry Bining############################################################################ 

def scrape_industrybuying_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.HTTPError as http_err:
        print(f"An error occurred while scraping {url}: {http_err}")  # Handle HTTP errors
        return None
    except Exception as err:
        print(f"An error occurred while scraping {url}: {err}")  # Handle other errors
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    product_data = {}

    # Product Title
    product_title_elem = soup.find('span', class_='productTitle')
    if product_title_elem and product_title_elem.find('h1'):
        product_title = product_title_elem.find('h1').get_text(strip=True)
        product_data['Title'] = product_title
    else:
        product_data['Title'] = None

    # Price
    price_elem = soup.find('span', class_='AH_PricePerPiece')
    if price_elem:
        price = price_elem.get_text(strip=True)
        product_data['Price'] = price
    else:
        product_data['Price'] = None

    # Features
    features_table = soup.find('tbody')
    if features_table:
        features = {}
        for row in features_table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) == 2:
                feature_name = columns[0].get_text(strip=True).replace(" :", "")
                feature_value = columns[1].get_text(strip=True)
                features[feature_name] = feature_value
        product_data['Features'] = features
    else:
        product_data['Features'] = None

    # Detailed Description
    description_section = soup.find('div', id='description')
    if description_section:
        description = ' '.join(p.get_text(strip=True) for p in description_section.find_all('p'))
        product_data['Description'] = description
    else:
        product_data['Description'] = None

    # Product Image
    image_elem = soup.find('a', class_='AH_MultipleImageList')
    if image_elem and image_elem.find('img'):
        image_url = image_elem.find('img')['data-zoom-image']
        product_data['Image URL'] = f"https:{image_url}"
    else:
        product_data['Image URL'] = None

    # Additional Specifications
    specifications = {}
    specifications_container = soup.find('div', id='famSpec')
    if specifications_container:
        for spec in specifications_container.find_all('div', class_='filterRow'):
            feature_name = spec.find('div', class_='featureNamePr').get_text(strip=True)
            feature_value = spec.find('div', class_='featureValuePr').get_text(strip=True).replace(": ", "")
            specifications[feature_name] = feature_value
        product_data['Specifications'] = specifications
    else:
        product_data['Specifications'] = None

    return product_data

def read_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        urls = [row[0] for row in reader if row]  # Ensure the row is not empty
    return urls

def write_csv(data):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_csv = f"output_files/industry.csv"
    headers = ["Title", "Price", "Description", "Image URL", "Features", "Specifications", "URL"]
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for row in data:
            writer.writerow([
                row.get("Title"),
                row.get("Price"),
                row.get("Description"),
                row.get("Image URL"),
                row.get("Features"),
                row.get("Specifications"),
                row.get("URL")
            ])
    print(f"Output CSV file '{output_csv}' created successfully.")
    return output_csv

def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

@app.route('/industry', methods=['GET', 'POST'])
def industry():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            return render_template('industry.html', file_path=file_path)
        else:
            return "No file uploaded"
    return render_template('industry.html')

@app.route('/scrape', methods=['POST'])
def indscrape():
    file_path = request.form['file_path']
    urls = read_csv(file_path)
    product_details = []

    for url in urls:
        if is_valid_url(url):
            data = scrape_industrybuying_product(url)
            if data:
                data["URL"] = url
                product_details.append(data)
        else:
            print(f"Invalid URL: {url}")

    if product_details:
        output_file_path = write_csv(product_details)
        return send_file(output_file_path, as_attachment=True)
    else:
        return "No data scraped"

@app.route('/download', methods=['GET'])
def downloadind():
    directory = 'output_files'
    filename = 'industry.csv'
    file_path = os.path.join(directory, filename)
    
    response = make_response(send_file(file_path, as_attachment=True))
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

##############################################pdf splitter############################################
@app.route('/splitter')
def pdfspliter():
    return render_template('pdfsplitter.html')

@app.route('/split', methods=['POST'])
def split_pdf():
    file = request.files['file']
    start_page = int(request.form['start_page'])
    end_page = int(request.form['end_page'])

    if file.filename == '':
        return "No selected file"

    pdf_reader = PdfReader(file)
    output_pdf = PdfWriter()

    if end_page >= len(pdf_reader.pages):
        end_page = len(pdf_reader.pages) - 1

    for page_num in range(start_page - 1, end_page):
        output_pdf.add_page(pdf_reader.pages[page_num])

    output_filename = f"split_{start_page}-{end_page}.pdf"
    with open(output_filename, 'wb') as output_file:
        output_pdf.write(output_file)

    return send_file(output_filename, as_attachment=True)




##################################################################################################
@app.route('/pdftotable')
def upload_file():
    return render_template('pdf_table.html')

@app.route('/uploadxlsx', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    if file:
        # Save the uploaded PDF to a temporary file
        pdf_path = os.path.join("uploads", file.filename)
        file.save(pdf_path)
        
        # Read the PDF file using Camelot
        tables = camelot.read_pdf(pdf_path, pages='all')
        
        # Combine all tables into a single DataFrame
        combined_df = pd.concat([table.df for table in tables], ignore_index=True)
        
        # Save the DataFrame to a CSV file
        csv_path = os.path.join("outputs", file.filename.replace('.pdf', '.csv'))
        combined_df.to_csv(csv_path, index=False)
        
        # Remove the uploaded PDF after processing
        os.remove(pdf_path)
        
        return send_file(csv_path, as_attachment=True)
    
    return "File processing failed"


if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    app.run(debug=True)
