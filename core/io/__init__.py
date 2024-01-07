
# IO related, application-wide singleton services

from .utils import *
from .os import os
from core.io.logger import LoggerFactory

logger, lf = LoggerFactory(__name__) 
