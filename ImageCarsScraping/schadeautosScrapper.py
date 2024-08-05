from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
import concurrent.futures
import io
import os
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import concurrent.futures
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import certifi

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

# Scrape car links from a given page
def scrapeCarLinks(driver, pageUrl):
    driver.get(pageUrl)
    carLinks = [item.get_attribute('href') for item in driver.find_elements(By.CSS_SELECTOR, '.car-inner.flexinner a')]
    return carLinks

# Scrape image links from a car link
def scrapeImageLinks(driver, carLink):
    driver.get(carLink)
    imageElements = driver.find_elements(By.CSS_SELECTOR, '.thumbs img')
    return [img.get_attribute('src') for img in imageElements]

# Prepare image data for uploading
def prepareImageData(imageUrl):
    try:
        response = requests.get(imageUrl, stream=True, verify=certifi.where())
        if response.status_code == 200:
            imageStream = io.BytesIO(response.content)
            imageStream.seek(0)
            return imageStream
    except Exception as e:
        print(f"Error downloading image from {imageUrl}: {str(e)}")
        return None

# Upload image to Google Drive
def uploadImage(imageStream, driveService, folderId):
    try:
        if imageStream is not None:
            file_name = f"bnbnb{uuid.uuid4()}.jpg"
            file_metadata = {'name': file_name, 'parents': [folderId]}
            media = MediaIoBaseUpload(fd=imageStream, mimetype='image/jpeg', resumable=True)
            request = driveService.files().create(body=file_metadata, media_body=media, fields='id')
            response = None
            while response is None:
                _, response = request.next_chunk()
    except Exception as e:
        print(f"Error uploading image: {str(e)}")

# Upload multiple images to Google Drive
def uploadImages(imageUrls, driveService, folderId):
    for imageUrl in imageUrls:
        imageStream = prepareImageData(imageUrl)
        if imageStream:
            uploadImage(imageStream, driveService, folderId)

# Main script to run scraping and uploading processes
def run_script(start_page, end_page):
    try:
        driver = setupWebdriver()
        driveService = authenticateDrive()
        folderId = '10733ZPlqCtkI2zo9TTQNdX3f4MgHfI9u'  # Google Drive folder ID

        for page in range(start_page, end_page + 1):
            pageUrl = f"https://www.schadeautos.nl/en/search/damaged/passenger-cars/1/1/0/0/0/0/1/{page}"
            carLinks = scrapeCarLinks(driver, pageUrl)
            for carLink in carLinks:
                imageUrls = scrapeImageLinks(driver, carLink)
                uploadImages(imageUrls, driveService, folderId)
    except Exception as e:
        print(f"Error in run_script: {e}")
    finally:
        driver.quit()

# Entry point of the script
def main():
    max_page = 632
    pages = range(1, max_page + 1)
    pageBatches = [(pages[i], pages[i + 50]) for i in range(0, len(pages), 51) if i + 50 < len(pages)]
    workers = int(len(pageBatches))
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        _ = list(executor.map(run_script, *zip(*pageBatches)))

if __name__ == "__main__":
    main()
