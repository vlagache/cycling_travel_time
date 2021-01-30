import logging
import uvicorn

from prediction.infrastructure.webservice import app


if __name__ == "__main__":


    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.DEBUG)

    uvicorn.run(app, port=8090, host='0.0.0.0', log_level='debug')



