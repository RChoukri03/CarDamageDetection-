import boto3
from botocore.exceptions import NoCredentialsError
from utils.singleton import Singleton
from utils.logger import getLogger as Logger
from PIL import Image
import io
import cv2
import numpy as np
import os
import requests
class AwsManager(metaclass=Singleton):
    def __init__(self):
        self.logger = Logger('Aws-S3')
        self.s3Client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
                region_name='eu-west-3')
        
        self.bucketName = "sygma-global-data-storage"
        self.logger.info(f'Conncted to s3 Bucket {self.bucketName}')
        self.s3Directory = "car-damage-detection/scrappedImages/"
    
    def listFileInBucket(self, ):
        try:
            response = self.s3Client.list_objects_v2(Bucket=self.bucketName)
            return [item['Key'] for item in response.get('Contents', [])]
        except NoCredentialsError as e:
            self.logger.error("Erreur : Vérifiez vos credentials AWS.")
            raise e
        except Exception as e:
            return str(e)

    def getImageUrl(self, objectName, expiresIn=3600):
        try:
            # Générer l'URL signée
            url = self.s3Client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucketName, 'Key': f"{self.s3Directory}{objectName}"},
                ExpiresIn=expiresIn
            )

            # Récupérer les données de l'image
            response = requests.get(url)
            if response.status_code == 200:
                image_data = np.frombuffer(response.content, dtype=np.uint8)
                img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

                if img is None:
                    with open(f"smallImgs.txt", 'a') as file:
                        file.write(objectName + '\n')
                    self.logger.error("L'image ne peut pas être décodée.")
                    return False

                # Vérifier les dimensions de l'image
                image_height, image_width = img.shape[:2]
                if image_width < 450 or image_height < 450:
                    with open(f"smallImgs.txt", 'a') as file:
                        file.write(objectName + '\n')
                    self.deleteImage(objectName)
                    return False

                return url
            else:
                with open(f"smallImgs.txt", 'a') as file:
                        file.write(objectName + '\n')
                return False 
        except NoCredentialsError as e:
            self.logger.error("Erreur : Vérifiez vos credentials AWS.")
            raise e
        except Exception as e:
            return {'error': str(e)}  
    
    def downloadFile(self, objectName, localFileName):
        """Télécharge un fichier spécifique depuis S3 vers un chemin local."""
        try:
            self.s3Client.download_file(self.bucketName, objectName, localFileName)
        except NoCredentialsError:
            return "Erreur : Vérifiez vos credentials AWS."
        except Exception as e:
            return str(e)

    

    def rotateImage(self, imageName, rotationDegrees):
        
        objectName = f"{self.s3Directory}{imageName}"
        response = self.s3Client.get_object(Bucket=self.bucketName, Key=objectName)
        imageContent = response['Body'].read()
        
        image = Image.open(io.BytesIO(imageContent))
        rotated_image = image.rotate(-rotationDegrees, expand=True)  
        
        in_mem_file = io.BytesIO()
        rotated_image.save(in_mem_file, format=image.format)
        in_mem_file.seek(0)
        
        self.s3Client.put_object(Bucket=self.bucketName, Key=objectName, Body=in_mem_file)
        self.logger.info(f"Image {imageName} rotated by {rotationDegrees} and replaced successfully.")
        

    def deleteImage(self, imageName):
        objectName = f"{self.s3Directory}{imageName}"
        try:
            response = self.s3Client.delete_object(Bucket=self.bucketName, Key=objectName)
            self.logger.info(f"Image {imageName} successfully deleted from S3.")
            return response
        except NoCredentialsError as e:
            self.logger.error("Error: Check your AWS credentials.")
            raise e
        except Exception as e:
            self.logger.error(f"Error deleting image {imageName}: {str(e)}")
            return str(e)
