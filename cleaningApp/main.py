
import os 
from waitress.server import create_server
import signal
from utils.logger import getLogger as Logger
from services.api import api

from services.CleanerValidator import CleanerValidator

logger = Logger('main')
host = "0.0.0.0"
port = 4000
validator = CleanerValidator()
def main():
    

    def handleSig(sig):
        print("\n")
        logger.info(f"Got signal {sig}, now gracefull terminate server ...")
        s.close()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGHUP):
        signal.signal(sig, handleSig)

    try:
        logger.info('initiating validator instance ... ')
        s = create_server(api, host=host, port=port, threads=8)
        logger.info(f"Run server on {host}:{port}")
        s.run()
    except OSError as e:
        if e.errno == 98:
            logger.error(
                f"Cannot bind server to {host}:{port} : Address already in use"
            )
        elif e.errno == 13:
            logger.error(f"Cannot bind server to {host}:{port} : Persmission denied")
        elif e.errno == 9:
            logger.info(f"Server ended")
        else:
            logger.error(f"Unexepted error {e}")
    except:
        logger.error(f"Unexepted error {e}")



if __name__ == "__main__":
    main()