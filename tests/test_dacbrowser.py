import os
import sys
#sys.path.append('../dac/dacbrowser')
#sys.path.append('dac')
from dac.dacbrowser.dacbrowser import DACBrowser, FormNotFoundError
import unittest
import mock

cookiesfile = os.path.join(os.path.expanduser('~'), '.dacconnectorcookies.lwp')
useragent = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'

valid_username = 'valid_username'
valid_password = 'valid_password'

username = 'valid_username'
password = 'valid_password'

invalid_username = 'invalid_username'
invalid_password = 'invalid_password'

add_device_response_data_str =  '''{
      "responseId": "697f445a-b4ca-4b8b-8357-d3a4750be75a",
      "resultCode": 35,
      "isAgent": true,
      "isAdmin": true,
      "isMember": false,
      "resultString": "There were errors in the data supplied. Please correct and re-submit.",
      "userString": "A device with number '2687f1b52857a536ac692197bca5eacc4fd14205' already exists on this team.",
      "validationMessages": 
      [
        {
          "validationKey":"deviceNumber",
          "validationUserMessage":"A device with number '2687f1b52857a536ac692197bca5eacc4fd14205' already exists on this team."
        }
      ],
      "creationTimestamp": "2014-08-11T13:22:21Z",
      "protocolVersion": "QH65B2",
      "requestId": "b45d9414-0913-44ec-bce7-5cf550776efb",
      "userLocale": "en_US",
      "requestUrl": "http:\/\/developer.apple.com\/services-developerportal\/QH65B2\/account\/ios\/device\/validateDevice.action?content-type=text\/x-url-arguments&accept=application\/json&requestId=b45d9414-0913-44ec-bce7-5cf550776efb&userLocale=en_US&teamId=B39FE245A7"
    }'''

class FormControl(object):
    def __init__(self, value=None):
        self.value = value

class Form(object):
    def __init__(self, name=None):
        self.name = name
        self.controls = list()

class Response(object):

    def __init__(self, response_headers, response_data=None):
        self.response_headers = response_headers
        self.response_data = response_data
    
    def info(self):
        return self.response_headers
    
    def read(self):
        return self.response_data

    def get_data(self):
        return self.response_data


def mock_mechanize_browser_open(self, url):
    url_required_auth = False
    url_parts = url.split('/')

    if 'account' in url_parts:
        url_required_auth = True
    
    response = Response(response_headers = {}) 
    if url_required_auth and self.credentials_actual == False:
            response = Response(response_headers = {'x-frame-options' : 'DENY'}) 
    return response

def mock_mechanize_browser_select_form(self, name):
    self.name = 'appleConnectForm'
    self.form = {'appleId' : '', 'accountPassword' : ''}
    #if name == 'deviceSave' and self.permissions_enough:
    if name == 'deviceSave':
        if self.permissions_enough == True:
            self.name = 'deviceSave'
            form = Form(name='deviceSave')
            form.controls.append(FormControl())
            form.controls.append(FormControl())
            form.controls.append(FormControl())
            self.form = form
        else:
            raise FormNotFoundError('Form with name deviceSave not found')

def mock_mechanize_browser_submit(self, nr=0):
    response = Response(response_headers = {'x-frame-options' : 'DENY'}) 
    if self.name == 'appleConnectForm':
        if self.form['appleId'] == valid_username and self.form['accountPassword'] == valid_password:
            response = Response(response_headers = {})
            self.credentials_actual = True
    elif self.name == 'deviceSave':
        if self.permissions_enough == True:
            response = Response(response_headers = {}, response_data = add_device_response_data_str)
        else:
            response = Response(response_headers = {}, response_data = '')
    else:
        response = Response(response_headers = {}, response_data = '')

    return response


@mock.patch('dac.dacbrowser.dacbrowser.Browser.open', mock_mechanize_browser_open)
@mock.patch('dac.dacbrowser.dacbrowser.Browser.select_form', mock_mechanize_browser_select_form)
@mock.patch('dac.dacbrowser.dacbrowser.Browser.submit', mock_mechanize_browser_submit)
class Test(unittest.TestCase):
    def setUp(self):
        if os.path.exists(cookiesfile):
            os.remove(cookiesfile)

    def tearDown(self):
        if os.path.exists(cookiesfile):
            os.remove(cookiesfile)

    def access_denied(self, request_result):
        return (request_result == None) or (request_result != None and request_result.info().get('x-frame-options') == 'DENY')
    
    def test_wrong_password_with_not_required_auth_url(self):
        browser = DACBrowser(invalid_username, invalid_password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = False
        request_result = browser.get('https://developer.apple.com/technologies/')
        self.assertEqual(self.access_denied(request_result), False)

    def test_wrong_password_with_required_auth_url_less_credentials(self):
        browser = DACBrowser(invalid_username, invalid_password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = False
        request_result = browser.get('https://developer.apple.com/account/ios/device/deviceList.action')
        self.assertEqual(self.access_denied(request_result), True)
    
    def test_right_password_with_required_auth_url_less_credentials(self):
        browser = DACBrowser(username, password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = False
        request_result = browser.get('https://developer.apple.com/account/ios/device/deviceList.action')
        self.assertEqual(self.access_denied(request_result), False)

    def test_wrong_password_with_required_auth_url_present_credentials(self):
        browser = DACBrowser(invalid_username, invalid_password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = True
        request_result = browser.get('https://developer.apple.com/account/ios/device/deviceList.action')
        self.assertEqual(self.access_denied(request_result), False)

    def test_right_password_with_several_urls_required_auth(self):
        browser = DACBrowser(username, password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = False
        request_result = browser.get('https://developer.apple.com/account')
        self.assertEqual(self.access_denied(request_result), False)
        request_result = browser.get('https://developer.apple.com/membercenter/')
    
    def test_add_device_with_permissions_not_enough(self):
        browser = DACBrowser(username, password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = True
        browser.browser.permissions_enough = False
        result_message = browser.add_device('https://developer.apple.com/account/ios/device/deviceCreate.action', 'Valid device name', '2687f1b52857a536ac692197bca5eacc4fd14205')
        self.assertEqual(result_message == 'Add device form not found. Probably your permissions not enough to add device. Try change login or/and password', True)

    def test_add_device_with_permissions_enough(self):
        browser = DACBrowser(username, password, useragent = useragent, cookiesfile = cookiesfile)
        browser.browser.credentials_actual = True
        browser.browser.permissions_enough = True
        result_message = browser.add_device('https://developer.apple.com/account/ios/device/deviceCreate.action', 'Valid device name', '2687f1b52857a536ac692197bca5eacc4fd14205')
        self.assertEqual(result_message.find('device with number') != -1, True)
