import pandas as pd
import boto3
import os
# Configuration des paramètres S3
bucketName = 'sygma-global-data-storage'
inputFolder = 'car-damage-detection/scrappedImages/'

# Créer un client S3
s3Client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
                region_name='eu-west-3')
def checkImgsInS3(filename):
    try:
        s3Client.head_object(Bucket=bucketName, Key=f"{inputFolder}{filename}")
        return True
    except s3Client.exceptions.ClientError as e:
        return False

def cleanDf(df):
    # Vérifier chaque image et supprimer les lignes pour les images non trouvées
    df['image_exists'] = df['nomImage'].apply(checkImgsInS3)
    cleanedDf = df[df['image_exists']]
    del cleanedDf['image_exists']  
    return cleanedDf

df = pd.read_csv('combinedDf.csv')

cleanedDf = cleanDf(df)

cleanedDf.to_csv('cleaned_combinedDf.csv', index=False)

print("Nettoyage terminé. Les données filtrées sont sauvegardées dans 'cleaned_combinedDf.csv'.")
