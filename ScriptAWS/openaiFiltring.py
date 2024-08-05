import os
import gc  # Garbage Collector
import boto3
import concurrent.futures
import pandas as pd
import time
import logging
import random
import sys
from openai import OpenAI
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AllKeysInvalidException(Exception):
    pass

# Load the prompt and parts names from files
prompt = open('promptFr.txt', 'r', encoding="utf-8").read().split('Les pièces de voiture à considérer:')
promptPart1 = prompt[0] + "\n".join(open('pièces.txt', 'r', encoding="utf-8").read().split("\n"))
prompt = promptPart1 + prompt[1]

# Define columns for the output CSV
columns = ["nomImage", "carOrNot"] + [piece.capitalize() for piece in open('pièces.txt', 'r', encoding="utf-8").read().split("\n")]

# Safety settings for the generative model
safetySettings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

part, counter = 23, 0
records = []
inputFolder = 'car-damage-detection/scrappedImages/'

def get_image_pass_count():
    try:
        with open('image_pass_count.txt', 'r') as file:
            return int(file.read())
    except FileNotFoundError:
        return 0

def save_image_pass_count():
    global image_pass_count
    with open('image_pass_count.txt', 'w') as file:
        file.write(str(image_pass_count))
image_pass_count = get_image_pass_count()

class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.errors = {key: 0 for key in keys}

    def mark_error(self, key):
        self.errors[key] += 1
        if self.errors[key] >= 10:
            self.keys.remove(key)
            with open('invalid_keys.txt', 'a') as f:
                f.write(f"{key} was used {self.errors[key]} times and then failed.\n")
            logging.error(f"Key {key} has been removed after too many errors.")
            if not self.keys:
                raise AllKeysInvalidException("All API keys are invalid.")

    def get_valid_key(self):
        if not self.keys:
            logging.error(f"All API keys are invalid.")
            raise AllKeysInvalidException("All API keys are invalid.")
        return random.choice(self.keys)

def getProcessedImages(directory):
    """Retrieve all image names from processed CSV files that end with .jpg or .jpeg."""
    processedimages = set()
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                for line in file:
                    image_name = line.split(',')[0] 
                    if image_name.endswith(('.jpg', '.jpeg')):
                        processedimages.add(image_name)
    logging.warning("all processed Images length", len(processedimages))
    return processedimages

def retry_operation(func, image_url, imageName, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            result = func(image_url)
            return result
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed with error: {str(e)[:100]}")
            time.sleep(delay)
            if attempt == retries - 1:
                with open('failure.txt', 'a') as data:
                    data.write(f"{imageName} \n")
                logging.error("All attempts failed; raising the exception.")
                return None

def getLastContinuationToken():
    try:
        with open('lastToken.txt', 'r') as tokenFile:
            return tokenFile.read().strip()
    except FileNotFoundError:
        return None

def saveContinuationToken(token):
    with open('lastToken.txt', 'w') as tokenFile:
        tokenFile.write(token)

def fetchImagesFromS3(bucketName, s3Client, continuationToken=None, processedimages=None):
    paginator = s3Client.get_paginator('list_objects_v2')
    pageIterator = paginator.paginate(Bucket=bucketName, Prefix=inputFolder, PaginationConfig={'StartingToken': continuationToken, 'PageSize': 250})
    global image_pass_count
    for page in pageIterator:
        if 'Contents' in page:
            for item in page['Contents']:
                key = item['Key']
                if key.endswith(('.jpg', '.jpeg')) and key.split('/')[-1] not in processedimages:
                    image_pass_count += 1
                    url = s3Client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucketName, 'Key': key},
                        ExpiresIn=3600
                    )
                    yield url, key
        if 'NextContinuationToken' in page:
            saveContinuationToken(page['NextContinuationToken'])
        save_image_pass_count()

def append_to_csv():
    global records, part
    if records:
        df = pd.DataFrame(records)
        df.to_csv(f"csvData/processedImagesPart_{part}.csv", mode='a', header=not os.path.exists(f"csvData/processedImagesPart_{part}.csv"), index=False)
        records = []
        gc.collect()

def process_image_with_retry(image_url=None, imageName=None):
    global records, part, counter
    def process(image_url):
        openai_api_key = os.getenv('OPENAI_API_KEY')

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=300
        )

        # Extract and process the response
        response_content = response.choices[0].message.content
        return response_content.strip()

    text = retry_operation(process, image_url, imageName)
    if text is None:
        return
    toAppend = {"nomImage": imageName.split('/')[-1], "carOrNot": 0 if "not car" in text else 1}
    for line in text.split('\n'):
        if ' - ' in line:
            partName, severity = line.split(' - ')
            toAppend[partName.capitalize()] = int(severity) if partName.capitalize() in columns else 0
    records.append(toAppend)
    if len(records) >= 200:
        print(len(records))
        append_to_csv()

def main(bucketName):
    try:
        s3Client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name='eu-west-3'
        )
        lastToken = getLastContinuationToken()
        processedimages = getProcessedImages('/home/ubuntu/filtring/geminiFilter/ScriptAWS/csvData/') # to be modified
        imageGenerator = fetchImagesFromS3(bucketName, s3Client, continuationToken=lastToken, processedimages=processedimages)
        tasks = []
        max_tasks = 300
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for imgData, imgName in imageGenerator:
                if len(tasks) >= max_tasks:
                    concurrent.futures.wait(tasks, return_when=concurrent.futures.FIRST_COMPLETED)
                    tasks = [task for task in tasks if not task.done()]
                future = executor.submit(process_image_with_retry, imgData, imgName)
                tasks.append(future)
    except AllKeysInvalidException as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main("global-data-storage")
