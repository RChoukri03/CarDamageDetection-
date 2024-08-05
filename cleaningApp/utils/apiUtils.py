

import importlib
import os




def getBoolFromUrl(req, argName, default=None):
    val = req.args.get(argName)
    if val:
        return val.lower() == 'true'
    return default


def getIntFromUrl(req, argName, default=None):
    try:
        val = req.args.get(argName)
        if val:
            return int(val)
        if default is not None:
            return default
        else:
            return None
    except:
        if default is not None:
            return default
        else:
            return None


def getStrFromUrl(req, argName, default=None):
    try:
        val = req.args.get(argName)
        if val:
            return val
        if default is not None:
            return default
        else:
            return None
    except:
        if default is not None:
            return default
        else:
            return None


def loadBlueprints():
    blueprints = []
    current_directory = os.path.dirname("routes/")
    for filename in os.listdir(current_directory):
        if filename.endswith('_routes.py'):
            # Deduce the service name from the filename
            service_name = filename.split('_routes.py')[0]
            imported_module = importlib.import_module(
                '.' + service_name + '_routes', package='routes',
            )
            # Add the blueprint to the list
            blueprints.append(getattr(imported_module, service_name))
    return blueprints
