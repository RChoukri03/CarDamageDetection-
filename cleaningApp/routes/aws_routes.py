
from flask import Blueprint, request, jsonify
from utils.logger import getLogger as Logger
from services.awsManager import AwsManager
API_ERROR = 100
aws = Blueprint('aws', __name__)

logger = Logger('API-aws')

awsManager = AwsManager()




@aws.route('/getImgUrl/<imageName>', methods=['GET'])
def getImgUrl(imageName):
    url = awsManager.getImageUrl(imageName)
    if url:
        return jsonify({'status': 'success', 'url': url}), 200
    return jsonify({'status': 'error'}), 400

@aws.route('/deleteImage/<imageName>', methods=['GET'])
def deleteImg(imageName):
    url = awsManager.deleteImage(imageName)
    return jsonify({'status': 'success', 'url': url}), 200

@aws.route('/validateRotation', methods=['POST'])
def validateRotation():
    # Extrait les données JSON envoyées par le client
    data = request.get_json()
    imageName = data.get('imageName')
    rotationDegrees = data.get('rotationDegrees')

    # Vérifie que les données nécessaires sont présentes
    if not imageName or rotationDegrees is None:
        return jsonify({'status': 'error', 'message': 'Missing imageName or rotationDegrees'}), 400

    # Utilise AwsManager pour effectuer la rotation
    try:
        result = awsManager.rotateImage(imageName, rotationDegrees)
        return jsonify({'status': 'success', 'message': result}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500