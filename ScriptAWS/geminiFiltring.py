import os
import gc  # Garbage Collector
from time import sleep
import boto3
import concurrent.futures
import pandas as pd
import PIL.Image
import base64
import time
import traceback
from io import BytesIO
import google.generativeai as genai
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the prompt and parts names from files
prompt = open('promptFr.txt', 'r', encoding="utf-8").read()
promptPart1 = prompt.split('Les pièces de voiture à considérer:')[0]
promptPart2 = prompt.split('Les pièces de voiture à considérer:')[1]
pieces = open('pièces.txt', 'r', encoding="utf-8").read().split("\n")
promptPart1 += "\n".join(pieces)
prompt = promptPart1 + promptPart2

# Define columns for the output CSV
columns = ["nomImage", "carOrNot"] + [piece.capitalize() for piece in pieces]

# Safety settings for the generative model
safetySettings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

part, counter = 22, 0
records = []

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
            raise Exception("All API keys are invalid.")

    def get_valid_key(self):
        if not self.keys:
            raise Exception("All API keys are invalid.")
        i = random.randint(0, len(self.keys) - 1)
        return self.keys[i]  # Return a random valid key

def retry_operation(func, imageName, retries=5, delay=0.5):
    failed_attempts = 0
    for attempt in range(retries):
        try:
            result = func()
            if failed_attempts > 0:
                logging.info(f"Success on attempt {attempt + 1} after {failed_attempts} failed attempts")
            return result
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed with error: {str(e)[:20]}")
            failed_attempts += 1
            time.sleep(delay)
            if attempt == retries - 1:
                with open('failure.txt', 'a') as data:
                    data.write(f"{imageName} \n")
                logging.error("All attempts failed; raising the exception.")

def getLastContinuationToken():
    try:
        with open('lastToken.txt', 'r') as tokenFile:
            return tokenFile.read().strip()
    except FileNotFoundError:
        return None

def saveContinuationToken(token):
    with open('lastToken.txt', 'w') as tokenFile:
        tokenFile.write(token)

def fetchImagesFromS3(bucketName, s3Client, continuationToken=None):
    try:
        paginator = s3Client.get_paginator('list_objects_v2')
        pageIterator = paginator.paginate(Bucket=bucketName, PaginationConfig={'StartingToken': continuationToken, 'PageSize': 30})

        for page in pageIterator:
            if 'Contents' in page:
                for item in page['Contents']:
                    key = item['Key']
                    if key.endswith('.jpg') or key.endswith('.jpeg'):
                        response = s3Client.get_object(Bucket=bucketName, Key=key)
                        imageData = response['Body'].read()
                        yield base64.b64encode(imageData).decode('utf-8'), key
            if 'NextContinuationToken' in page:
                saveContinuationToken(page['NextContinuationToken'])
    except Exception as e:
        logging.error(f'Error occurred: {e}')

def append_to_csv():
    global records, part
    if records:
        df = pd.DataFrame(records)
        df.to_csv(f"processedImagesPart_{part}.csv", mode='a', header=not os.path.exists(f"processedImagesPart_{part}.csv"), index=False)
        records = []
        gc.collect()  # Force garbage collection

def process_image_with_retry(imageBase64, imageName, geminiKey):
    global part, counter, records
    def process():
        image = PIL.Image.open(BytesIO(base64.b64decode(imageBase64)))
        genai.configure(api_key=geminiKey)
        model = genai.GenerativeModel('gemini-1.0-pro-vision-latest', safety_settings=safetySettings)
        return model.generate_content([prompt, image, "pièces endommagées: "]).text.strip()

    try:
        text = retry_operation(process, imageName)
        toAppend = {"nomImage": imageName.split('/')[-1], "carOrNot": 0 if "not car" in text else 1}
        for line in text.split('\n'):
            if ' - ' in line:
                partName, severity = line.split(' - ')
                toAppend[partName.capitalize()] = int(severity) if partName.capitalize() in columns else 0
        records.append(toAppend)
        if len(records) >= 200:
            print(len(records))
            append_to_csv()
        if counter % 10000 == 0:
            part += 1
        counter += 1
        gc.collect()
    except Exception as e:
        if not "ResourceExhausted" in str(e):
            logging.error(f"Failed to process {imageName}: {str(e)}")
        else:
            logging.error(f"Failed to process {imageName}: ResourceExhausted")

def main(bucketName, geminiKeys):
    s3Client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='eu-west-3'
    )
    lastToken = getLastContinuationToken()
    imageGenerator = fetchImagesFromS3(bucketName, s3Client, continuationToken=lastToken)
    s = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(geminiKeys)) as executor:
        futures = [executor.submit(process_image_with_retry, imgData, imgName, geminiKeys[i % len(geminiKeys)]) for i, (imgData, imgName) in enumerate(imageGenerator)]
        for future in concurrent.futures.as_completed(futures):
            sleep(0.2)
            if time.time() - s > 600:
                for i in range(100):
                    try:
                        _ = future.result()
                        s = time.time()
                    except Exception as e:
                        print('Error:', e)

if __name__ == "__main__":
    geminiKeys = [
        # Add your Gemini API keys here
    ]
    main("global-data-storage", geminiKeys)
