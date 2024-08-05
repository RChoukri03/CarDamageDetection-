import os
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import concurrent.futures
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import certifi
import io
from PIL import Image
import boto3
from googleapiclient.http import MediaIoBaseUpload

# Authenticate Google Drive API
def authenticateDrive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/drive.file']
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

# Authenticate AWS S3
def autheticateS3():
    s3Client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
        region_name='eu-west-3'
    )
    return s3Client

# Setup Selenium WebDriver with headless option
def setupWebdriver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

# Scrape car links from a given page
def scrapeCarLinks(driver, pageUrl):
    driver.get(pageUrl)
    carLinks = [item.get_attribute('href') for item in driver.find_elements(By.CSS_SELECTOR, ".vehicle-model.display-6.font-weight-bolder")]
    return carLinks

# Scrape image links from a car link
def scrapeImageLinks(driver, carLink):
    driver.get(carLink)
    imageElements = driver.find_elements(By.CSS_SELECTOR, ".flex-grow-1.change_image")
    return [img.get_attribute('href') for img in imageElements]

session = requests.Session()

# Prepare image data for uploading
def prepareImageData(imageUrl):
    try:
        response = requests.get(imageUrl, stream=True, verify=certifi.where())
        if response.status_code == 200:
            imageStream = io.BytesIO(response.content)
            image = Image.open(imageStream)
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
def uploadImage(imageStream, driveService, folderId):
    try:
        if imageStream is not None:
            fileName = f"dldld{uuid.uuid4()}.jpg"
            file_metadata = {'name': fileName, 'parents': [folderId]}
            media = MediaIoBaseUpload(fd=imageStream, mimetype='image/jpeg', resumable=True)
            request = driveService.files().create(body=file_metadata, media_body=media, fields='id')
            response = None
            while response is None:
                _, response = request.next_chunk()
    except Exception as e:
        print(f"Error uploading image: {str(e)}")

# Upload image to AWS S3
def uploadImageS3(imageStream, s3Client):
    try:
        if imageStream is not None:
            folderName = "car-damage-detection/scrappedImages"
            bucketName = "sygma-global-data-storage"
            fileName = f"{folderName}/{uuid.uuid4()}.jpg"
            s3Client.upload_fileobj(imageStream, bucketName, fileName)
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Upload images to Google Drive
def uploadImages(imageUrls, driveService, folderId):
    for imageUrl in imageUrls:
        imageStream = prepareImageData(imageUrl)
        if imageStream:
            uploadImage(imageStream, driveService, folderId)

# Upload images to AWS S3
def uploadImagesS3(imageUrls, s3Client):
    for imageUrl in imageUrls:
        imageStream = prepareImageData(imageUrl)
        if imageStream:
            uploadImageS3(imageStream=imageStream, s3Client=s3Client)

# Main function to run the scraping and uploading process
def run(pages):
    try:
        driver = setupWebdriver()
        s3Client = autheticateS3()
        for page in pages:
            start = time.time()
            pageUrl = f'https://www.salvagereseller.com/cars-for-sale/quick-pick/salvage-cars?page={page}'
            carLinks = scrapeCarLinks(driver, pageUrl)
            for carLink in carLinks:
                imageUrls = scrapeImageLinks(driver, carLink)
                uploadImagesS3(imageUrls, s3Client)
            msg = ","
            if time.time() - start < (len(carLinks) + 2):
                msg = "ERROR"
            with open('pagesDone.txt', 'a') as file:
                file.write(str(page) + msg + '\n')
                print('page', page, 'processed')
    except Exception as e:
        print(f"Error in run: {e}")
    finally:
        driver.quit()

# Entry point of the script
def main():
    # authenticateDrive()
    max_page = 2600
    pages = range(1, max_page + 1)
    pageBatches = [pages[i:i + 50] for i in range(0, len(pages), 51) if i + 50 < len(pages)]
    workers = int(len(pageBatches))
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        _ = list(executor.map(run, pageBatches))

if __name__ == "__main__":
    main()
