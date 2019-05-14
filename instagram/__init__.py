import os
import logging

from instagram.application import create_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

configuration = os.environ['APPLICATION_CONFIG_FILE']

application = create_application(configuration=configuration)

logger.info("Hello world")