import os
import sys
sys.path.append('../dacbrowser')
from appleaccountprocessor import AppleAccountProcessor
import unittest
import mock


class Response(object):
    
    def __init__(self, response_string):
        self.response_string = response_string

    def read(self):
        return self.response_string

def mock_dacbrowser_post():
    pass
