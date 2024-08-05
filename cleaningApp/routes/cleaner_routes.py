
from flask import Blueprint, request, jsonify,Response
from utils.logger import getLogger as Logger
from services.CleanerValidator import CleanerValidator
from collections import OrderedDict

API_ERROR = 100
cleaner = Blueprint('cleaner', __name__)

logger = Logger('API-cleaner')

validator = CleanerValidator()

orderedDataKeys = [
            "Aile avant droit", "Porte avant droite", "Porte arriere droite", "Aile arriere droit",
            "Feux avant droit", "Feux arriere droit", "Feux avant gauche", "Feux arriere gauche",
            "Aile avant gauche", "Porte avant gauche", "Porte arriere gauche", "Aile arriere gauche",
            "Pare-choc", "Plaque d'immatriculation avant", "Pare-choc arriere", "Plaque d'immatriculation arrière",
            "Pare-brise avant", "Pare-brise arriere", "Capot", "Malle","Rejet","carOrNot","nomImage", "validatorName"
        ]

@cleaner.route('/updateInitialTree', methods=['GET'])
def updateInitialTree():
    data = validator.updateInitialTrieWithNewCsv()
    return jsonify({'status': 'success', 'addedFilePaths': data}), 200


@cleaner.route('/getDataFromInitial', methods=['POST'])
def getDataFromInitial():
    data = request.get_json()
    imageName = data.get('imageName')
    if not imageName:
        return jsonify({'status': 'error', 'message': 'Missing imageName parameter'}), 400
    data = validator.getDataFromInitial(imageName)
    if data:
        newData = OrderedDict()
        for k in orderedDataKeys:
            try:
                newData[k] = int(data.get(k, 0))
            except ValueError:
                newData[k] = 0 

        # Ajouter les clés non converties en int
        nonConvertedKeys = ["nomImage"]
        for key in nonConvertedKeys:
            if key in data:
                newData[key] = data[key]
        # Ajoutez le nom de l'image à la fin
        if "Plaque d'immatriculation avant" in newData:
            newData["Plaque d'immat avant"] = newData.pop("Plaque d'immatriculation avant")

        if "Plaque d'immatriculation arrière" in newData:
            newData["Plaque d'immat arriere"] = newData.pop("Plaque d'immatriculation arrière")
        return jsonify({'status': 'success', 'data': newData}), 200
    else:
        return jsonify({'status': 'error', 'message': 'No data found'}), 404


@cleaner.route('/getDataFromPending', methods=['POST'])
def getDataFromPending():
    data = request.get_json()
    imageName = data.get('imageName')
    if not imageName:
        return jsonify({'status': 'error', 'message': 'Missing imageName parameter'}), 400
    data = validator.getDataFromPending(imageName)
    if data:
        # Nouvelle structure de données ordonnée
        
        newData = OrderedDict()
        for k in orderedDataKeys:
            try:
                newData[k] = int(data.get(k, 0))
            except ValueError:
                newData[k] = 0 

        # Ajouter les clés non converties en int
        nonConvertedKeys = ["nomImage", "validatorName"]
        for key in nonConvertedKeys:
            if key in data:
                newData[key] = data[key]
        if "Plaque d'immatriculation avant" in newData:
            newData["Plaque d'immat avant"] = newData.pop("Plaque d'immatriculation avant")

        if "Plaque d'immatriculation arrière" in newData:
            newData["Plaque d'immat arriere"] = newData.pop("Plaque d'immatriculation arrière")
        return jsonify({'status': 'success', 'data': newData}), 200
    else:
        return jsonify({'status': 'error', 'message': 'No data found'}), 404

@cleaner.route('/getDataFromValidated', methods=['POST'])
def getDataFromValidated():
    data = request.get_json()
    imageName = data.get('imageName')
    if not imageName:
        return jsonify({'status': 'error', 'message': 'Missing imageName parameter'}), 400
    data = validator.getDataFromValidated(imageName)
    if data:
        newData = OrderedDict()
        for k in orderedDataKeys:
            try:
                newData[k] = int(data.get(k, 0))
            except ValueError:
                newData[k] = 0 

        # Ajouter les clés non converties en int
        nonConvertedKeys = ["nomImage", "validatorName"]
        for key in nonConvertedKeys:
            if key in data:
                newData[key] = data[key]
        # Vérifier d'abord si les anciennes clés existent avant de renommer
        if "Plaque d'immatriculation avant" in newData:
            newData["Plaque d'immat avant"] = newData.pop("Plaque d'immatriculation avant")

        if "Plaque d'immatriculation arrière" in newData:
            newData["Plaque d'immat arriere"] = newData.pop("Plaque d'immatriculation arrière")

        return jsonify({'status': 'success', 'data': newData}), 200
    else:
        return jsonify({'status': 'error', 'message': 'No data found'}), 404
    
@cleaner.route('/updateImageInInitial', methods=['POST'])
def updateImageInInitial():
    data = request.json
    imageName = data['imageName']
    newData = data['newData']
    validator.updateImageInInitial(imageName, newData)
    return jsonify({'status': 'success', 'message': 'Image data updated in initial trie.'}), 200

@cleaner.route('/updateImageInPending', methods=['POST'])
def updateImageInPending():
    data = request.json
    imageName = data['imageName']
    newData = data['newData']
    validator.updateImageInPending(imageName, newData)
    return jsonify({'status': 'success', 'message': 'Image data updated in pending trie.'}), 200

@cleaner.route('/updateImageInValidated', methods=['POST'])
def updateImageInValidated():
    data = request.json
    imageName = data['imageName']
    newData = data['newData']
    validator.updateImageInValidated(imageName, newData)
    return jsonify({'status': 'success', 'message': 'Image data updated in validated trie.'}), 200

@cleaner.route('/moveImageToPending', methods=['POST'])
def moveImageToPending():
    data = request.json
    imageName = data['imageName']
    validator.moveImageToPending(imageName)
    return jsonify({'status': 'success', 'message': 'Image moved to pending.'}), 200

@cleaner.route('/moveImageToValidated', methods=['POST'])
def moveImageToValidated():
    data = request.json
    imageName = data['imageName']
    validator.moveImageToValidated(imageName)
    return jsonify({'status': 'success', 'message': 'Image moved to validated.'}), 200

@cleaner.route('/getKeysInInitial', methods=['GET'])
def getKeysInInitial():
    keys = validator.keysInInitial()
    return jsonify({'status': 'success', 'keys': keys}), 200

@cleaner.route('/getKeysInPending', methods=['GET'])
def getKeysInPending():
    keys = validator.keysInPending()
    return jsonify({'status': 'success', 'keys': keys}), 200

@cleaner.route('/getKeysInValidated', methods=['GET'])
def getKeysInValidated():
    keys = validator.keysInValidated()
    return jsonify({'status': 'success', 'keys': keys}), 200


@cleaner.route('/getnextKeyInInitial', methods=['GET'])
def getnextKeysInInitial():
    key = validator.nextInitialKey()
    if key:
        return jsonify({'status': 'success', 'key': key}), 200
    else:
        return jsonify({'status': 'empty', 'message': 'No more keys in pending.'}), 200

@cleaner.route('/getnextKeyInPending', methods=['GET'])
def getnextKeysInPending():
    key = validator.nextPendingKey()
    if key:
        return jsonify({'status': 'success', 'key': key}), 200
    else:
        return jsonify({'status': 'empty', 'message': 'No more keys in pending.'}), 200

@cleaner.route('/getnextKeyInValidated', methods=['GET'])
def getnextKeysInValidated():
    key = validator.nextValidatedKey()
    if key:
        return jsonify({'status': 'success', 'key': key}), 200
    else:
        return jsonify({'status': 'empty', 'message': 'No more keys in pending.'}), 200

@cleaner.route('/getStatus', methods=['GET'])
def getTriesStatus():
    keysInValidated = validator.keysInValidated()
    keysInInitial = validator.keysInInitial()
    keysInPending = validator.keysInPending()
    return jsonify({'status': 'success','AllCleanedImages':validator.totalCleanedImages,'NotverifiedImages': len(keysInInitial), 'PendingImages':len(keysInPending),'validatedImages' : len(keysInValidated)}), 200

import traceback

@cleaner.route('/incrementValidatorCount', methods=['POST'])
def incrementValidatorCount():
    data = request.get_json()
    try:
        validatorName = data.get('validatorName')
        if validatorName:
            if validatorName :
                validator.updateValidationCount(validatorName)
                return jsonify({'status': 'success'}), 200  
            else:
                return jsonify({'status': 'error', 'message': 'Validator not found'}), 404
        return jsonify({'status': 'error', 'message': 'Validator name is required'}), 400  
    except Exception as e:
        traceback.print_exc()
        logger.error(e)


@cleaner.route('/getValidatorCount', methods=['POST'])
def getValidatorCount():
    data = request.get_json()
    validatorName = data.get('validatorName')
    if validatorName:
        return jsonify({'status': 'success','count': validator.validatorInfo[validatorName]['count']})
    else:
        return jsonify({'status': 'error', 'message': 'Validator not found'}), 404



@cleaner.route('/getAllValidatorCounts', methods=['GET'])
def getAllValidatorsCounts():
    results = []
    messages = []
    for validatorName, info in validator.validatorInfo.items():
        if 'total_count' in info and 'count' in info:
            message = f"For validator {validatorName}, the total images processed are {info['total_count']}, with a progress of {info['count']} images."
            messages.append(message)
            results.append({
                'validatorName': validatorName,
                'total_count': info['total_count'],
                'count': info['count'],
                'message': message
            })
        else:
            results.append({
                'validatorName': validatorName,
                'error': 'Missing count details'
            })
            messages.append(f"Error: Missing count details for validator {validatorName}.")
    if messages:
        formattedResponse = "<br>".join(messages)
        return Response(formattedResponse, mimetype='text/html')