
import boto3
from PIL import Image
import io
import imagehash
import os
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import pytesseract

s3Client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
                region_name='eu-west-3')
bucketName = 'sygma-global-data-storage'
inputFolder = 'car-damage-detection/scrappedImages/'
outputFolder = 'car-damage-detection/flaggedImages/'
deleteFolder = 'car-damage-detection/imageToDelete/'
hashesFile = 'imageHashes.txt'

def loadImageHashes():
    if os.path.exists(hashesFile):
        with open(hashesFile, 'r') as file:
            return set(json.load(file))
    return set()

def saveImageHashes(hashes):
    with open(hashesFile, 'w') as file:
        json.dump(list(hashes), file)

imageHashes = loadImageHashes()
def saveLastProcessedKey(last_key):
    with open('last_key.txt', 'w') as file:
        file.write(last_key)

def readLastProcessedKey():
    if os.path.exists('last_key.txt'):
        with open('last_key.txt', 'r') as file:
            return file.read().strip()
    return None

def processImage(data):
    image, image_key = data
    left = 100
    top = 100
    right = image.width - 100
    bottom = image.height - 100
    e = None
    # Crop l'image
    copySource = {'Bucket': bucketName, 'Key': image_key}
    if image.width < 450 or image.height < 450:
        s3Client.copy_object(Bucket=bucketName, CopySource=copySource, Key=f"{deleteFolder}{image_key[len(inputFolder):]}")
        s3Client.delete_object(Bucket=bucketName, Key=image_key)
        return 'SmallImg deleted'
    try:
        image = image.crop((left, top, right, bottom))
    except Exception as e:
        print(f"Erreur de rognage : {e}. Utilisation de l'image originale.")
    
    currentHash = str(imagehash.average_hash(image))
    if currentHash in imageHashes:
        s3Client.copy_object(Bucket=bucketName, CopySource=copySource, Key=f"{deleteFolder}{image_key[len(inputFolder):]}")
        s3Client.delete_object(Bucket=bucketName, Key=image_key)
        return "Deleted duplicate"
    imageHashes.add(currentHash)
    saveImageHashes(imageHashes)

    text = pytesseract.image_to_string(image)
    if len(text) > 30:
        
        s3Client.copy_object(Bucket=bucketName, CopySource=copySource, Key=f"{outputFolder}{image_key[len(inputFolder):]}")
        s3Client.delete_object(Bucket=bucketName, Key=image_key)
        return "Moved flagged image"
    return "Processed"

def main():
    with ThreadPoolExecutor(max_workers=100) as executor:
        paginator = s3Client.get_paginator('list_objects_v2')
        start_after = readLastProcessedKey()
        page_iterator = paginator.paginate(Bucket=bucketName, Prefix=inputFolder, PaginationConfig={'StartingToken': start_after, 'PageSize': 600})
        for page in tqdm(page_iterator):
            futures = []
            for item in page.get('Contents', []):
                key = item['Key']
                if key.endswith(('.jpg', '.jpeg')):
                    response = s3Client.get_object(Bucket=bucketName, Key=key)
                    image_data = response['Body'].read()
                    image = Image.open(io.BytesIO(image_data))
                    futures.append(executor.submit(processImage, (image, key)))
            for future in futures:
                print(future.result())
            if 'NextContinuationToken' in page:
                saveLastProcessedKey(page['NextContinuationToken'])
            print('Go to next Page')

if __name__ == "__main__":
    main()