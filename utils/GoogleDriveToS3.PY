import os
import io
import boto3
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import concurrent.futures

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

# Authenticate AWS S3 using environment variables for credentials
def authenticateS3():
    s3Client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='eu-west-3'
    )
    return s3Client

# Read the list of already transferred files
def readTransferredFiles(transferredFiles):
    if os.path.exists(transferredFiles):
        with open(transferredFiles, 'r') as file:
            return set(file.read().splitlines())
    return set()

# Process a single file transfer task
def process_file(task):
    service, fileId, fileName, bucketName, transferredFiles, failedFiles, transferredSet = task
    if fileId in transferredSet:
        return  # Skip already transferred files

    s3Client = authenticateS3() 
    try:
        s3_directory = 'car-damage-detection/scrappedImages/' 
        fileName = os.path.join(s3_directory, os.path.basename(fileName))
        request = service.files().get_media(fileId=fileId)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        s3Client.upload_fileobj(fh, bucketName, fileName)
        fh.close()
        # Record the fileId of successfully transferred file
        with open(transferredFiles, 'a') as f:
            f.write(fileId + '\n')
    except Exception as e:
        # Record the fileId and fileName of failed transfers
        with open(failedFiles, 'a') as f:
            f.write(fileId + ', ' + fileName + '\n')

# Transfer files from Google Drive to S3
def transfer_files(service, folderId, bucketName, transferredFiles, failedFiles, workers=25):
    transferredSet = readTransferredFiles(transferredFiles)
    tasks = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folderId}' in parents",
            spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageToken=page_token,
        ).execute()
        
        items = response.get('files', [])
        if not items:
            print('No files found.')
            break

        # Create tasks for each file to be transferred
        tasks.extend([(service, item['id'], item['name'], bucketName, transferredFiles, failedFiles, transferredSet) for item in items])
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    print(f"Starting transfer of {len(tasks)} files with {workers} workers...")
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for i, _ in enumerate(executor.map(process_file, tasks), 1):
            if i % 50000 == 0:  
                print(f"Processed {i} files...")

if __name__ == '__main__':
    driveService = authenticateDrive()
    folderId = '10733ZPlqCtkI2zo9TTQNdX3f4MgHfI9u'  # Google Drive folder ID
    bucketName = "sygma-global-data-storage"  # S3 bucket name
    transferredFiles = 'transferredFiles.txt'
    failedFiles = 'failedFiles.txt'
    transfer_files(driveService, folderId, bucketName, transferredFiles, failedFiles)
