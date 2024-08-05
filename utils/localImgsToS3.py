import os
import boto3
import uuid
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import logging
from botocore.config import Config

# Create a custom configuration that increases the max pool connections
my_config = Config(
    max_pool_connections=100  
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Authenticate AWS S3 using environment variables for credentials
def authenticateS3():
    s3Client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='eu-west-3'
    )
    return s3Client

# Upload a file to S3
def uploadFileToS3(s3Client, filePath, bucketName, s3Directory, transferredLog, depthPath):
    # Check if the file has already been transferred
    if isAlreadyTransferred(filePath, transferredLog):
        logging.info(f"Skipping {filePath} as it is already transferred.")
        return

    try:
        # Generate a unique file name and construct the S3 path
        file_name = 'SSS' + str(uuid.uuid4()) + ".jpg"
        s3_path = os.path.join(s3Directory, file_name)
        # Upload the file to S3
        s3Client.upload_file(filePath, bucketName, s3_path)
        # Record the successful transfer
        recordTransfert(filePath, transferredLog)
        logging.info(f"Successfully uploaded {filePath} to {s3_path}")
    except Exception as e:
        logging.error(f"Failed to upload {filePath} to S3: {e}")

# Check if a file is an image based on its MIME type
def isImage(filePath):
    type, _ = mimetypes.guess_type(filePath)
    return type and type.startswith('image')

# Check if the file has already been transferred by reading the log
def isAlreadyTransferred(filePath, transferredLog):
    try:
        with open(transferredLog, 'r') as file:
            transferred_files = file.read().splitlines()
        return filePath in transferred_files
    except FileNotFoundError:
        logging.warning(f"{transferredLog} not found. Creating new log file.")
        open(transferredLog, 'w').close()  
        return False

# Record the file transfer in the log
def recordTransfert(filePath, transferredLog):
    with open(transferredLog, 'a') as file:
        file.write(filePath + '\n')
    logging.info(f"Recorded transfer of {filePath}")

# Process the local directory and create tasks for uploading files
def process_directory(directory, bucketName, s3Directory, s3Client, transferredLog):
    tasks = []
    for root, dirs, files in os.walk(directory):
        depthPath = os.path.relpath(root, start=directory)
        for file in files:
            filePath = os.path.join(root, file)
            if isImage(filePath):
                tasks.append((s3Client, filePath, bucketName, s3Directory, transferredLog, depthPath))
    logging.info(f"Number of tasks generated: {len(tasks)}")
    return tasks

# Main function to initiate the upload process
def main():
    bucketName = "sygma-global-data-storage"  # S3 bucket name
    s3Directory = 'car-damage-detection/scrappedImages/'  # S3 directory
    localDirectory = '/mnt/r/PROJECTS/driveData/new/extracted/'  # Local directory to scan
    transferredLog = '/mnt/r/PROJECTS/Car-Damage-Detection/Newtransferred_files.txt'  # Log file for transferred files
    s3Client = authenticateS3()  # Authenticate S3 client
    
    tasks = process_directory(localDirectory, bucketName, s3Directory, s3Client, transferredLog)
    batch_size = 50  # Batch size for processing tasks
    task_batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]

    # Use ThreadPoolExecutor to upload files in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        for batch in task_batches:
            for task in batch:
                executor.submit(uploadFileToS3, *task)

if __name__ == "__main__":
    main()
