'''
Created on Jan 13, 2021

@author: robert
'''
try:
    import app.globals as globals
except:
    pass
import xmlgwimpl

class xmlGwErrorGeneric(Exception):
    pass

class xmlGwErrorDevNotFound(xmlGwErrorGeneric):
    def __init__(self, dev):
        self.dev = dev

class xmlGwErrorData(Exception):
    pass

class xmlGwErrorInvalidValue(xmlGwErrorData):
    def __init__(self, fid, val):
        self.fid = fid
        self.val = val

class xmlGwErrorUnknownFunction(xmlGwErrorData):
    def __init__(self, fid):
        self.fid = fid

class xmlGw(object):
    def __init__(self, testMode = False, xmlGwIpAddr = '192.168.1.18', type = 'camera', nr = 13):
        self.impl = xmlgwimpl.XmlGatewayImpl()
        self.isConnected = False
        self.devsInfo = []
        self.testMode = False
        if testMode == True:
            self.testMode = True
            devInfo = { 'type': type, 'nr': nr, 'sessionid': '' }
            self.devsInfo.append(devInfo)
            self.xmlGwIpAddr = xmlGwIpAddr
        else:
            for i in range(0, globals.getDeviceCount()):
                devInfo = { 'type': 'not used', 'nr': 1, 'sessionid': '' }
                self.devsInfo.append(devInfo)
            
    def scanDevices(self):
        '''
        get devices jnown at the xmlgw
        check if they match with local devices and if so copy sessionid
        '''
        if self.isConnected:
            try:
                devices = self.impl.getDevices()
                for i in range(0, len(self.devsInfo)):
                    devInfo = self.devsInfo[i]
                    devInfo['sessionid'] = ''
                    for device in devices:
                        if device['type'] == devInfo['type'] and int(device['name']) == devInfo['nr']:
                            devInfo['sessionid'] = device['sessionid']
                            break
                    self.devsInfo[i] = devInfo
            except:
                for i in range(0, len(self.devsInfo)):
                    devInfo = self.devsInfo[i]
                    devInfo['sessionid'] = ''
                    self.devsInfo[i] = devInfo
                
    def updateInfo(self):
        if self.isConnected:
            self.impl.disconnect()
        try:
            if self.testMode == True:
                self.impl.connect(self.xmlGwIpAddr)
            else:
                self.impl.connect(globals.getXmlGw())
            self.isConnected = True
        except:
            return

        for i in range(0, len(self.devsInfo)):
            devInfo = self.devsInfo[i]
            if self.testMode == False:
                device = globals.getDevice(i)
                devInfo['type'] = device['type']
                devInfo['nr'] = device['nr']
            devInfo['sessionid'] = ''
            self.devsInfo[i] = devInfo
        
        self.scanDevices()    
    
    def useDevice(self, index):
        if self.isConnected:
            devInfo = self.devsInfo[index]
            if len(devInfo['sessionid']) > 0:
                return
        raise xmlGwErrorDevNotFound(index)
    
    def handleDataNotOkException(self, e, fid, val):
        errStr = str(e).upper()
        if errStr == 'UNKNOWNFUNCTION':
            raise xmlGwErrorUnknownFunction(fid)
        if errStr == 'INVALIDVALUE':
            raise xmlGwErrorInvalidValue(fid, val)
        raise xmlGwErrorGeneric(str(e))
        
    def getFunctionInformation(self, dev, functionId):
        self.useDevice(dev)
        try:
            info = self.impl.getFunctionInformation(self.devsInfo[dev]['sessionid'], functionId)
            return info
        except xmlgwimpl.XmlGatewayErrorDataNotOk as e:
            self.handleDataNotOkException(e, functionId, -1)
        except Exception as e:
            raise xmlGwErrorGeneric(str(e))
        return info
    
    def getAllFunctionsInformation(self, dev):
        self.useDevice(dev)
        try:
            info = self.impl.getAllFunctionInformation(self.devsInfo[dev]['sessionid'])
            return info
        except xmlgwimpl.XmlGatewayErrorDataNotOk as e:
            self.handleDataNotOkException(e, -1, -1)
        except Exception as e:
            raise xmlGwErrorGeneric(str(e))
        return info
    
    def optionsNameToValue(self, options, name):
        return self.impl.optionsNameToValue(options, name)
    
    def optionsValueToName(self, options, value):
        return self.impl.optionsValueToName(options, value)
    
    def getFunctionValue(self, dev, functionId):
        self.useDevice(dev)
        try:
            val = self.impl.getFunctionValue(self.devsInfo[dev]['sessionid'], functionId)
            return val
        except xmlgwimpl.XmlGatewayErrorDataNotOk as e:
            self.handleDataNotOkException(e, functionId, -1)
        except Exception as e:
            raise xmlGwErrorGeneric(str(e))
        return ''
    
    def setFunctionValue(self, dev, functionId, value, isRelative = False):
        self.useDevice(dev)
        try:
            self.impl.setFunctionValue(self.devsInfo[dev]['sessionid'], functionId, value, isRelative)
        except xmlgwimpl.XmlGatewayErrorDataNotOk as e:
            self.handleDataNotOkException(e, functionId, value)
        except Exception as e:
            raise xmlGwErrorGeneric(str(e))
        
    
    