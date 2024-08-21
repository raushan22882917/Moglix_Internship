import os
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def download_images_from_csv(csv_file_path, save_directory):
    # Check if the CSV file exists
    if not os.path.isfile(csv_file_path):
        print(f"The file {csv_file_path} does not exist.")
        return

    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return
    
    # Check if 'IMAGE_1' and 'Image Name' columns exist in the DataFrame
    if 'Image link' not in df.columns:
        print("'IMAGE_1' column not found in the CSV file.")
        return
    if 'Mat Code' not in df.columns:
        print("'Image Name' column not found in the CSV file.")
        return

    # Ensure the save directory exists
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    
    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        url = row['Image link']
        image_name = row['Mat Code']  # Get the image name from the 'Image Name' column
        
        # Check if the URL is valid
        if pd.notna(url) and pd.notna(image_name):
            if is_valid_url(url):
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        # Open the image from the response content
                        image = Image.open(BytesIO(response.content))
                        
                        # Convert the image to RGB mode (to handle RGBA issues with JPEG)
                        rgb_image = image.convert('RGB')
                        
                        # Save the image with the specified name in the save directory
                        rgb_image.save(os.path.join(save_directory, f"{image_name}.jpg"), "JPEG")
                        print(f"Image '{image_name}' downloaded and saved successfully.")
                    else:
                        print(f"Failed to download image from URL: {url}")
                except Exception as e:
                    print(f"Error occurred while downloading image from URL: {url}\n{e}")
            else:
                print(f"Invalid URL: {url}. Skipping this URL.")
        else:
            print("URL or image name is missing for one or more rows.")

if __name__ == "__main__":
    csv_file_path = input("Enter the path to the CSV file (including the file name and extension, e.g., C:\\path\\to\\file.csv): ")
    save_directory = input("Enter the directory to save the images: ")
    
    download_images_from_csv(csv_file_path, save_directory)
