import pandas as pd
import os
import time
from utils.singleton import Singleton
from utils.logger import getLogger as Logger
import datrie
import string
import numpy as np
import json
from datetime import datetime, timedelta
import threading
import traceback
import warnings
warnings.filterwarnings('ignore')

class CleanerValidator(metaclass = Singleton):
    additionalColumns= ['validatorName', "Rejet"]
    columnsToRead = [
        'nomImage', 'carOrNot', 'Plaque d\'immatriculation avant', 'Pare-choc',
        'Feux avant droit', 'Feux avant gauche', 'Capot', 'Pare-brise avant',
        'Aile avant droit', 'Aile avant gauche', 'Porte avant droite', 'Porte avant gauche',
        'Porte arrière droite', 'Porte arrière gauche', 'Aile arrière droit',
        'Aile arrière gauche', 'Pare-brise arriere', 'Malle', 'Feux arrière droit',
        'Feux arrière gauche', 'Pare-choc arriere', 'Plaque d\'immatriculation arrière'
    ]
    def __init__(self):
        self.logger = Logger('Cleaner')
        self.folderPath = "csvData/"
        self.combinedDf = pd.DataFrame()
        self.trieInitial = datrie.Trie(string.ascii_letters + string.digits + '_.-')
        self.triePending = datrie.Trie(string.ascii_letters + string.digits + '_.-')
        self.trieValidated = datrie.Trie(string.ascii_letters + string.digits + '_.-')
        self.includedFileNames = []
        self._running = False
        self.totalCleanedImages = 0
        self.logger.info('Initializing Tries from csv Files')
        self.initializeTries()
        self.logger.info('loadStatusTries ...')
        self.loadStatusTries()
        self.logger.info('Create Data Generators ...')
        self.generatorInitial = self.createGeneratorInitial()
        self.generatorPending = self.createGeneratorPending()
        self.generatorValidated = self.createGeneratorValidated()
        self.keep_running = True
        self.validatorInfo = {}

        self.reset_thread = None
        self.start()
        self.loadValidatorInfo()

    def start(self):
        if not self._running:
            self._running = True
            self.reset_thread = threading.Thread(target=self.schedule_reset)
            self.reset_thread.daemon = True
            self.reset_thread.start()

    def stop(self):
        self._running = False

    def stopAndJoin(self):
        if self._running:
            self.stop()
            if self.reset_thread.is_alive():
                self.reset_thread.join()

    def schedule_reset(self):
        """ Planifier la réinitialisation des compteurs toutes les 15 minutes """
        while self._running:
            time.sleep(900)  # Attendre 15 minutes
            self.check_and_reset_counts()
        print("Reset thread has finished execution.")

    def loadValidatorInfo(self):
        try:
            with open(os.path.join(self.folderPath, 'validatorsInfo.json'), 'r') as file:
                validators_list = json.load(file)
                self.validatorInfo = {}
                for item in validators_list:
                    validator_name = item.pop('validatorName')
                    validator_name = validator_name.upper()
                    item['last_reset'] = datetime.strptime(item['last_reset'], '%Y-%m-%d %H:%M:%S')
                    self.validatorInfo[validator_name] = item
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load or parse validators info: {e}")
            self.validatorInfo = {}


    def saveValidatorInfo(self):
        with open(os.path.join(self.folderPath, 'validatorsInfo.json'), 'w') as file:
            # Préparation des données pour la sauvegarde
            save_list = []
            for k, v in self.validatorInfo.items():
                v_copy = v.copy()
                v_copy['validatorName'] = k.upper()
                v_copy['last_reset'] = v_copy['last_reset'].strftime('%Y-%m-%d %H:%M:%S')
                save_list.append(v_copy)
            # Écrire la liste complète en JSON dans le fichier
            json.dump(save_list, file, indent=4) 


    def updateValidationCount(self, validatorName):
        """ Mettre à jour et gérer le compteur de validations pour un validateur donné """
        validatorName = validatorName.upper()
        try :
            if validatorName not in self.validatorInfo:
                self.validatorInfo[validatorName] = {
                    'count': -800,
                    'last_reset': datetime.now(),
                    'total_count': 0  
                }
            info = self.validatorInfo[validatorName]
            info['count'] += 1
            info['total_count'] += 1 
            self.saveValidatorInfo()
        except Exception as e:
            traceback.print_exc()
            self.logger.error(e)


    def check_and_reset_counts(self):
        """ Vérifier et réinitialiser les compteurs si nécessaire toutes les 24 heures """
        now = datetime.now()
        for validator, info in self.validatorInfo.items():
            if now - info['last_reset'] >= timedelta(days=1):
                info['count'] -= 1000
                info['last_reset'] = now
        self.saveValidatorInfo()

    def __del__(self):
        self.stopAndJoin()


    def initializeTries(self):
        # Load combined DataFrame from all CSVs first
        def modifyValues(value):
            try:
                value = int(value)
                if value == 0:
                    return 0
                elif value >= 4:
                    return 3
                elif value == 3:
                    return 2
                elif value < 3:
                    return 1
            except ValueError:
                return value

        all_data = []
        for filename in os.listdir(self.folderPath):
            if filename.endswith('.csv') and filename not in ['validated.csv','pending.csv']:

                filePath = os.path.join(self.folderPath, filename)
                df = pd.read_csv(filePath, usecols=self.columnsToRead,low_memory=False)
                df.fillna(0, inplace=True)
                for col in df.columns:
                    if col != 'nomImage':
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                self.combinedDf = pd.concat([self.combinedDf, df]).drop_duplicates(subset='nomImage', keep='last')
                df = df.applymap(modifyValues, na_action='ignore')  
                all_data.append(df)
                self.includedFileNames.append(filename)
        self.combinedDf = pd.concat(all_data).drop_duplicates(subset='nomImage', keep='last')
        self.combinedDf['Rejet'] = 0
        self.totalCleanedImages = len(self.combinedDf)

        # TODO : to be modified
        # smallImgsPath = os.path.join(self.folderPath, '/mnt/r/PROJECTS/Car-Damage-Detection/Apps/cleaningApp/smallImgs.txt')
        
        smallImgsPath = os.path.join(self.folderPath, '/home/ubuntu/Work/cleaningApp/smallImgs.txt')
        try :
            with open(smallImgsPath, 'r') as file:
                small_images = file.read().splitlines()
        except:
            small_images = []
        self.combinedDf = self.combinedDf[~self.combinedDf['nomImage'].isin(small_images)]
        #self.combinedDf.to_csv('combinedDf.csv', index=False)
        self.combinedDf = self.combinedDf[self.combinedDf.carOrNot != 0]
        for _, row in self.combinedDf.iterrows():
            self.trieInitial[row['nomImage']] = row.to_dict()
    def loadTrieFromCsv(self, fileName, trie):
        filePath = os.path.join(self.folderPath, fileName)

        if os.path.exists(filePath):
            columns = self.columnsToRead + self.additionalColumns
            df = pd.read_csv(filePath, usecols=columns,low_memory=False)
            df.fillna(0, inplace=True)
            df = df.map(lambda x: int(x) if isinstance(x, float) else x)

            for _, row in df.iterrows():
                trie[row['nomImage']] = row.to_dict()

    def loadStatusTries(self):
        self.logger.info('Synchronizing pending & validated Trees')
        # Load pending and validated CSVs if they exist
        self.loadTrieFromCsv('pending.csv', self.triePending)
        self.loadTrieFromCsv('validated.csv', self.trieValidated)
        # Remove duplicates from tries
        start = time.time()

        # Convert trie keys to sets
        pending_keys = set(self.triePending.keys())
        validated_keys = set(self.trieValidated.keys())
        initial_keys = set(self.trieInitial.keys())

        # Identify keys to remove
        pending_in_initial = pending_keys.intersection(initial_keys)
        validated_in_pending = validated_keys.intersection(pending_keys)

        # Remove duplicates based on identified keys
        for key in pending_in_initial:
            del self.trieInitial[key]

        for key in validated_in_pending:
            del self.triePending[key]
        self.logger.warn(f'time to load status {time.time()-start}')



    def updateInitialTrieWithNewCsv(self):
        allFiles= os.listdir(self.folderPath)
        addedPaths = []
        allAdded  = 0
        for filePath in allFiles:
            if filePath.endswith('.csv') and filePath not in self.includedFileNames and filePath not in ['validated.csv','pending.csv']:
                df = pd.read_csv(os.path.join(self.folderPath,filePath), usecols=self.columnsToRead,low_memory=False)
                addedPaths+=len(df)
                for index, row in df[df.carOrNot != 0].iterrows():
                    if row['nomImage'] not in self.triePending.keys() and row['nomImage'] not in self.trieValidated.keys():
                        self.trieInitial[row['nomImage']] = row.to_dict()
                self.includedFileNames.append(filePath)
                self.logger.info(f'adding file {filePath} to inital Trie')
                addedPaths.append(filePath)
        self.totalCleanedImages+=allAdded
        return(addedPaths)

    def updateDataInTrie(self, trie, imageName, newData):

        if imageName in trie.keys():
            # Update the data with new data
            if "validatorName" in newData:
                newData["validatorName"] = newData["validatorName"].upper()
            trie[imageName].update(newData)


    def updateImageInInitial(self, imageName, newData):
        self.logger.info(f'Updating Initial Tree')
        self.updateDataInTrie(self.trieInitial, imageName, newData)

        # self.persistData(imageName, 'initial')

    def updateImageInPending(self, imageName, newData):
        self.logger.info(f'Updating Pending Tree')
        self.updateDataInTrie(self.triePending, imageName, newData)
        # self.persistData(imageName, 'pending')

    def updateImageInValidated(self, imageName, newData):
        self.logger.info(f'Updating Validated Tree')
        self.updateDataInTrie(self.trieValidated, imageName, newData)
        # self.persistData(imageName, validated')

    def moveImageToPending(self, imageName):
        self.logger.info(f'moving {imageName} to pending Trie')
        if imageName in self.trieInitial.keys():
            data = self.trieInitial[imageName]
            del self.trieInitial[imageName]
            self.triePending[imageName] = data
            self.persistData(imageName, 'pending')

    def moveImageToValidated(self, imageName):
        self.logger.info(f'moving {imageName} to validated Trie')
        if imageName in self.triePending:
            data = self.triePending[imageName]
            del self.triePending[imageName]
            self.trieValidated[imageName] = data
            self.persistData(imageName, 'validated')

    def persistData(self, imageName, status):
        data = self.triePending[imageName] if status == 'pending' else self.trieValidated[imageName]
        df = pd.DataFrame([data])
        csvPath = os.path.join(self.folderPath, f'{status}.csv')
        if not os.path.exists(csvPath):
            df.to_csv(csvPath, index=False, mode='w', header=True)
        else:
            df.to_csv(csvPath, index=False, mode='a', header=False)

    def ensureDirectories(self):
        os.makedirs(self.folderPath, exist_ok=True)

    def createGeneratorInitial(self):
        while True:
            keys = self.trieInitial.keys()
            if not keys:
                break
            for key in keys:
                yield key

    def createGeneratorPending(self):
        while True:
            keys = self.triePending.keys()
            if not keys:
                break
            for key in keys:
                yield key

    def createGeneratorValidated(self):
        while True:
            keys = self.trieValidated.keys()
            if not keys:
                break
            for key in keys:
                yield key


    def nextInitialKey(self):
        return next(self.generatorInitial, None)

    def nextPendingKey(self):
        return next(self.generatorPending, None)

    def nextValidatedKey(self):
        return next(self.generatorValidated, None)

    def keysInInitial(self):
        return self.trieInitial.keys()

    def keysInPending(self):
        return self.triePending.keys()

    def keysInValidated(self):
        return self.trieValidated.keys()

    def getDataFromInitial(self, imageName):
        return self.trieInitial.get(imageName, None)

    def getDataFromPending(self, imageName):
        return self.triePending.get(imageName, None)

    def getDataFromValidated(self, imageName):
        return self.trieValidated.get(imageName, None)

