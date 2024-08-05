import time

from flask import Flask,render_template,request,g
from flask_cors import CORS
from utils.apiUtils import loadBlueprints
from utils.logger import getLogger as Logger
api = Flask(__name__,template_folder='templates', static_folder='static')
app = Flask(__name__, )
# Dynamically register all blueprints
for blueprint in loadBlueprints():
    api.register_blueprint(blueprint)


# Configure CORS
CORS(api)
logger = Logger('API')
@api.route('/')
def home():
    return render_template('index.html')

@api.before_request
def start_timer():
    g.start = time.time()


@api.after_request
def log_request(response):
    if hasattr(g, 'start'):
        elapsed = time.time() - g.start
        logger.info(f"{request.method}|{request.path}|ExecTime {elapsed:.2f}s |{response.status_code}")
    return response


@api.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {str(error)}")
    return str(error), 500

