import os
import uuid
import requests
import io
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from selenium.webdriver.common.by import By
from PIL import Image

from tqdm import tqdm
import urllib3

# Disable warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Authenticate Google Drive API
def authenticateDrive():
    creds = None
    # Check if token.json exists to load saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    # If there are no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/drive.file']
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

# Setup Selenium WebDriver with headless option
def setupWebdriver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

# Prepare image data for uploading
def prepareImageData(imageUrl):
    try:
        # Make a request to get the image
        response = requests.get(imageUrl, stream=True, verify=False)
        if response.status_code == 200:
            imageStream = io.BytesIO(response.content)
            image = Image.open(imageStream)
            # Resize image if it is larger than 800x800 pixels
            if image.width > 800 or image.height > 800:
                image = image.resize((800, 800), Image.LANCZOS)
            
            newImageStream = io.BytesIO()
            image.save(newImageStream, format='JPEG')
            newImageStream.seek(0)
            return newImageStream
    except Exception as e:
        print(f"Error downloading image from {imageUrl}: {str(e)}")
        return None

# Upload image to Google Drive
def uploadImage(imageStream, drive_service, folder_id):
    try:
        if imageStream is not None:
            file_name = f"YZTX{uuid.uuid4()}.jpg"
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            media = MediaIoBaseUpload(fd=imageStream, mimetype='image/jpeg', resumable=True)
            request = drive_service.files().create(body=file_metadata, media_body=media, fields='id')
            response = None
            while response is None:
                _, response = request.next_chunk()
    except Exception as e:
        print(f"Error uploading image: {str(e)}")

# Upload images from a list of URLs in a file
def uploadImagesFromFile(file_path, drive_service, folder_id):
    with open(file_path, 'r') as file:
        imageUrls = file.readlines()

    # Creating a tuple of arguments for each call to prepareAndUpload
    args = ((imageUrl.strip(), drive_service, folder_id) for imageUrl in imageUrls)

    # Using ProcessPoolExecutor with map
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        # Wrapping the executor.map in tqdm for a progress bar
        _ = list(tqdm(executor.map(lambda p: prepareAndUpload(*p), args), total=len(imageUrls)))

# Prepare image data and upload it
def prepareAndUpload(imageUrl, drive_service, folder_id):
    imageStream = prepareImageData(imageUrl)
    if imageStream:
        uploadImage(imageStream, drive_service, folder_id)

# Main function to initiate the process
def main():
    drive_service = authenticateDrive()
    folder_id = '1mr0G3nnGs0Na24xxeC8TlB4iGV5xvzAg'  # Google Drive folder ID
    image_file_path = 'Scraping_Yazid/finalData.txt'  # Path to file containing image URLs
    uploadImagesFromFile(image_file_path, drive_service, folder_id)

if __name__ == "__main__":
    main()
