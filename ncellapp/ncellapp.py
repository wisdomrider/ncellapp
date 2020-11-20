import requests
from base64 import (b64encode, b64decode)
from ast import literal_eval
from datetime import datetime

from ncellapp.aescipher import AESCipher

class NcellApp():
    def __init__(self):
        self.baseUrl = 'http://ssa.ncell.com.np:8080/mc/selfcare/v2/proxy' 
        self.aes = AESCipher()
        self.headers = {
            'X-MobileCare-AppClientVersion': 'SHn7MOIW3T/R/OL8LsAvxw==',
            'Cache-Control': 'no-cache',
            'X-MobileCare-PreferredLocale': 'cAsAM2g0t7oB6OSJKH1ptQ==',
            'Content-Type': 'application/xml',
            'X-MobileCare-APIKey': 'ABC_KEY',
            'X-MobileCare-AppResolution': 'iRRhXh87ipDTZpyEWGWteg==',
            'X-MobileCare-AppPlatformVersion': 'QJ2ZR3DKpuBfBr7GuTQh7w==',
            'ACCEPT': 'application/json',
            'X-MobileCare-AppPlatformName': 'yEHXRN3mrQMvwG4bfE2ApQ==',
            'Host': 'ssa.ncell.com.np:8080',
            'Connection': 'Keep-Alive',
        }
  
class register(NcellApp): 
      
    def __init__(self, msidn):
        NcellApp.__init__(self)
        self.msidn = msidn
    
    def sendOtp(self):
        '''[Send OTP to the number for registration]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/register'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><serviceInstance>{self.msidn}</serviceInstance></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']
        
        try:
            self.deviceClientId = self.aes.encrypt(response.ncellResponse['deviceClientId'])
        except KeyError:
            self.deviceClientId = None
        
        return response
    
    def getToken(self, otp):
        '''[Send the OTP to the Ncell server and return the token if successful]

        Args:
            otp ([string]): [OTP sent in the phone number]

        Returns:
            [dict]: [response from the Ncell server with token]
        '''
        self.headers.update({
            'X-MobileCare-DeviceClientID':  self.deviceClientId,
            'X-MobileCare-MSISDN': self.msidn,          
        })
        
        url = self.baseUrl + '/register'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><otp>{otp}</otp></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']
        
        if response.ncellResponse['opStatus'] == '0':
            token = b64encode(str({'msidn':self.msidn, 'deviceClientId':self.deviceClientId}).encode()).decode()
            response.token = token
            
        return response
         
class ncell(NcellApp):
    
    def __init__(self, token):
        NcellApp.__init__(self)
        self.token = token
        
    def login(self):
        '''[Extract the msidn and client ID from the token and login]

        Returns:
            [dict]: [returns opStatus=0 if successful]
        '''
        try:
            self.msidn = literal_eval(b64decode(self.token).decode())['msidn']
            self.deviceClientId = literal_eval(b64decode(self.token).decode())['deviceClientId']
        except Exception:
            self.msidn = self.deviceClientId = None
            return {'opStatus': 'invalid', 'errorMessage': 'The token you provided is not valid.'}
        
        self.headers.update({
            'X-MobileCare-DeviceClientID': self.deviceClientId,
            'X-MobileCare-MSISDN': self.msidn,          
        })
        
        profile = self.viewProfile().ncellResponse
        
        try:
            self.name = profile['myProfile']['name']
            self.status = profile['myProfile']['status']
            self.partyID = profile['myProfile']['partyID']
            self.accountId = profile['myProfile']['accountID']
            self.serviceFlag = profile['myProfile']['serviceFlag']
            self.currentPlan = profile['myProfile']['currentPlan']
            self.secureToken = profile['myProfile']['secureToken']
            self.hubID = profile['myProfile']['hubID']
            return {'opStatus': '0', 'errorMessage': 'SUCCESS'}
            
        except KeyError:
            self.name = self.status = self.partyID = self.accountId = self.serviceFlag = self.currentPlan = self.secureToken = self.hubID = None
            return {'opStatus': 'expired', 'errorMessage': 'The token you provided has expired.'}
            
    def viewProfile(self):
        '''[View the profile of the account]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/viewMyProfile'

        data = "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData /></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']
        
        return response
    
    def sendSms(self, destination, message, schedule=None):
        '''[Send SMS with the currentPlan]

        Args:
            destination ([int]): [MSIDN of the destination]
            message ([String]): [Message to send]
            schedule ([int], optional): [Schedule date in order of YYYYMMDDHHMMSS format, eg.20201105124500]. Defaults to None.

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        schedule = schedule or datetime.now().strftime("%Y%m%d%H%M%S")

        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><userId>{schedule}</userId><problemDesc>{message}</problemDesc><serviceId>SENDSMS</serviceId><accountId>{self.accountId}</accountId><code>{destination}</code><offerId>yes</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']
        
        return response
    
    def sendFreeSms(self, destination, message, schedule=None):
        '''[Send free 10 SMS]

        Args:
            destination ([int]): [MSIDN of the destination]
            message ([String]): [Message to send]
            schedule ([int], optional): [Schedule date in order of YYYYMMDDHHMMSS format, eg.20201105124500]. Defaults to None.

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        schedule = schedule or datetime.now().strftime("%Y%m%d%H%M%S")

        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><userId>{schedule}</userId><problemDesc>{message}</problemDesc><serviceId>SENDSMS</serviceId><accountId>{self.accountId}</accountId><code>{destination}</code><offerId>no</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']
        
        return response
        
    def viewBalance(self):
        '''[View the current balance]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/myBalance'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><code>{self.accountId}</code><accountId>{self.accountId}</accountId><offerId>{self.hubID}</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def selfRecharge(self, rpin):
        '''[Recharging the current account]

        Args:
            rpin ([int]): [16 digit PIN of the recharge card]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><alternateContactNumber></alternateContactNumber><contractId></contractId><customerId></customerId><serviceId>RECHARGENOW</serviceId><code>{rpin}</code></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def recharge(self, destination, rpin):
        '''[Recharging other's account]

        Args:
            destination ([int]): [MSIDN of the destination]
            rpin ([int]): [16 digit PIN of the recharge card]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><alternateContactNumber>{destination}</alternateContactNumber><contractId></contractId><customerId></customerId><serviceId>RECHARGENOW</serviceId><code>{rpin}</code></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def rechargeHistory(self):
        '''[latest balance transfer history]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/rechargeHistory'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><userId>TransferHistory</userId><accountId>{self.accountId}</accountId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def balanceTransfer(self, destination, amount):
        '''[Initiate the balance transformation to the destination number]

        Args:
            destination ([int]): [MSIDN of the destination]
            amount ([int]): [Amount of balance to transfer]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><alternateContactNumber>{destination}</alternateContactNumber><contractId></contractId><customerId></customerId><action>NEW</action><serviceId>BALANCETRANSFER</serviceId><code>{amount}</code></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def confirmBalanceTransfer(self, otp):
        '''[Confirm the balance transfer]

        Args:
            otp ([int]): [OTP sent in phone number]

        Returns:
            [type]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><password>{otp}</password><contractId></contractId><customerId></customerId><action>NEW</action><serviceId>BALANCETRANSFER</serviceId><offerId>validate</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def viewTransaction(self, transactionsFrom, transactionsTo):
        '''[Initiate to view call history]

        Args:
            transactionsFrom ([int]): [From date in YYYYMMDDHHMMSS order]
            transactionsTo ([int]): [To date in YYYYMMDDHHMMSS order]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/viewTransactions'
        
        self.transactionsFrom = transactionsFrom
        self.transactionsTo = transactionsTo
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>prepaid</lob><userId>{self.transactionsFrom}</userId><code>GET</code><accountId>{self.accountId}</accountId><offerId>{self.transactionsTo}</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def confirmViewTransaction(self, otp):
        '''[Confirm to view call history]

        Args:
            otp ([int]): [OTP sent in phone number]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/viewTransactions'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>prepaid</lob><action>{otp}</action><userId>{self.transactionsFrom}</userId><code>VALIDATE</code><accountId>{self.accountId}</accountId><offerId>{self.transactionsTo}</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def viewService(self, serviceCategory=''):
        '''[View the list of available services to activate]

        Args:
            serviceCategory ([str], optional): [Category of the service]. Defaults to None.

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/viewMyService'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><code>R3027</code><serviceCategory>{serviceCategory}</serviceCategory><accountId>{self.accountId}</accountId><offerId>{self.hubID}</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def activateService(self, serviceId):
        '''[Activate the certain service]

        Args:
            serviceId ([int]): [Service ID found in isMandatory field of viewService()]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><serviceId>SUBSCRIBEAPRODUCT</serviceId><code>{serviceId}</code></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def viewOffer(self):
        '''[View the available offer for the account]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/viewOffers'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><customerId></customerId><lob>{self.serviceFlag}</lob><accountId>{self.accountId}</accountId><contractId></contractId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def activateOffer(self, offerId):
        '''[Activate the certain offer]

        Args:
            offerId ([int]): [offer ID found in offerID field of viewOffer()]

        Returns:
            [type]: [description]
        '''
        url = self.baseUrl + '/updateServiceRequest'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><serviceId>SUBSCRIBEAPRODUCT</serviceId><code>{offerId}</code></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response
    
    def view3gPlans(self):
        '''[View available plans for 3G]

        Returns:
            [dict]: [response from the Ncell server]
        '''
        url = self.baseUrl + '/view3gPlans'
        
        data = f"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><mAppData><userOperationData><lob>{self.serviceFlag}</lob><contractId></contractId><customerId></customerId><code>{self.accountId}</code><accountId>{self.accountId}</accountId><offerId>{self.hubID}</offerId></userOperationData></mAppData>"
        data = self.aes.encrypt(data)
        
        response = requests.post(url, headers=self.headers, data=data)
        
        response.ncellResponse = literal_eval(self.aes.decrypt(response.text))['businessOutput']

        return response