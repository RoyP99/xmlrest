'''
Created on Nov 24, 2020

@author: robert
'''
import socket
import select
import time
import xml.etree.ElementTree as ET

class XmlGatewayErrorSocket(Exception):
    # when there is a socket error
    pass

class XmlGatewayErrorTimeout(Exception):
    # when no data is received
    pass

class XmlGatewayErrorConnect(Exception):
    # when no connection can be made
    pass

class XmlGatewayErrorDataNotOk(Exception):
    # when the gateway doesn't respond with a Ok
    pass


class XmlGatewayImpl(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    def mysend(self, msg):
        totalsent = 0
        msglen = len(msg)
        while totalsent < msglen:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise XmlGatewayErrorSocket("socket connection broken")
            totalsent = totalsent + sent
            
    def myReceive(self):
        foundStart = False
        searchStart = False
        Start = b''
        searchTag = False
        Tag = b''
        foundXml = False
        xml = b''
        while foundXml == False:
            try:
                readable, writeable, exce = select.select([self.sock], [], [self.sock], 10.0)
                if self.sock in readable:
                    rec = self.sock.recv(1)
            except:
                time.sleep(50)
                raise XmlGatewayErrorTimeout("no data received")
            
            xml = xml + rec
            if foundStart == False and rec == b'<':
                searchStart = True
                searchTag = True
            elif searchStart == True:
                if rec != b' ' and rec != b'>':
                    Start = Start + rec
                else:
                    searchStart = False
                    foundStart = True
            if searchTag == True:
                Tag = Tag + rec
                if rec == b'>':
                    searchTag = False
                    if Tag[-2] == ord('/'):
                        foundXml = True
            if foundStart == True:
                if rec == b'>':
                    if xml.find(b'</'+Start+b'>') != -1:
                        foundXml = True
        return xml
    
    def testResponseOk(self, recv):
        root = ET.fromstring(recv)
        if root.tag == 'request-response':
            if root.attrib['result'] != 'Ok':
                raise XmlGatewayErrorDataNotOk(root.attrib['result'])
        else:
            raise XmlGatewayErrorDataNotOk("No reponse:",recv.decode())
        
    def connect(self, url):
#        socket.setdefaulttimeout(15.0)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.settimeout(5.0)
        try:
            self.sock.connect((url, 8080))
            print('connected')
        except:
            raise XmlGatewayErrorConnect("No connection")

        self.mysend(b'<application-authentication-request xml-protocol="2.0" response-level="Always"><name>XmlGateway</name></application-authentication-request>')
        recv = self.myReceive()
        #print(recv)
        self.testResponseOk(recv)
        recv = self.myReceive()
    
    def disconnect(self):
        self.sock.close()
        
    def getDevices(self):
        devices = []
        self.mysend(b'<device-information-request response-level="Always"></device-information-request>')
        recv = self.myReceive()
        self.testResponseOk(recv)
        recv = self.myReceive()
        root = ET.fromstring(recv)
        if root.tag == 'device-information-indication':
            for device in root.findall('device'):
                name = device.find('name')
                functype = device.find('type')
                sessionId = device.find('sessionid')
                if name != None and functype != None and sessionId != None:
                    deviceDict = { 'name' : name.text, 'type' : functype.text.lower(), 'sessionid' : sessionId.text }
                    devices.append(deviceDict)
        return devices
     
    def getFunctionInformation(self, sessionId, functionId):
        function = str(functionId)
        self.mysend(b'<function-information-request response-level="Always"><device><sessionid>' + sessionId.encode() + b'</sessionid>' + \
                    b'<function id="' + function.encode() + b'" /></device></function-information-request>')
        recv = self.myReceive()
        #print(recv)
        self.testResponseOk(recv)
        recv = self.myReceive()
        root = ET.fromstring(recv)
        functionValue = ''
        if root.tag == 'function-information-indication':
            for device in root.findall('device'):
                for function in device.findall('function'):
                    options = []
                    for option in function.iter('option'):
                        tOption = option.attrib;
                        tOption['value'] = int(option.text)
                        options.append(tOption)
                    functype = function.find('type')
                    name = function.find('name')
                    value = function.find('value')
                    if functype != None and name != None and value != None:
                        functionValue = { 'type' : functype.text.lower(), 'name' : name.text, 'value' : value.text, 'options' : options }        
        return functionValue
    
    def getAllFunctionInformation(self, sessionId):
        self.mysend(b'<function-information-request response-level="Always"><device><sessionid>' + sessionId.encode() + b'</sessionid>' + \
                    b'</device></function-information-request>')
        recv = self.myReceive()
        self.testResponseOk(recv)
        recv = self.myReceive()
        root = ET.fromstring(recv)
        functionValue = ''
        functionValues = []
        if root.tag == 'function-information-indication':
            for device in root.findall('device'):
                for function in device.findall('function'):
                    fid = 0
                    if 'id' in function.attrib:
                        fid = int(function.attrib['id'])
                    options = []
                    for option in function.iter('option'):
                        tOption = option.attrib;
                        if len(tOption):
                            tOption['value'] = int(option.text)
                            options.append(tOption)
                    functype = function.find('type')
                    name = function.find('name')
                    value = function.find('value')
                    if functype != None and name != None and value != None:
                        functionValue = { 'id' : fid, 'type' : functype.text.lower(), 'name' : name.text, 'value' : value.text, 'options' : options }
                        functionValues.append(functionValue)
        return functionValues
    
    def optionsNameToValue(self, options, name):
        for option in options:
            if option['name'] == name:
                return option['value']
        return None
    
    def optionsValueToName(self, options, value):
        for option in options:
            if option['value'] == value:
                return option['name']
        return None
    
    def getFunctionValue(self, sessionId, functionId):
        function = str(functionId)
#        self.mysend(b'<function-information-request response-level="ErrorOnly"><device><sessionid>' + sessionId.encode() + b'</sessionid>' + \
#                    b'<function id="' + function.encode() + b'" /></device></function-information-request>')
        self.mysend(b'<function-value-request response-level="Always"><device><sessionid>' + sessionId.encode() + b'</sessionid>' + \
                   b'<function id="' + function.encode() + b'" /></device></function-value-request>')
        recv = self.myReceive()
        #print(recv)
        self.testResponseOk(recv)
        recv = self.myReceive()
        root = ET.fromstring(recv)
        functionValue = ''
        if root.tag == 'function-value-indication':
            for device in root.findall('device'):
                for function in device.findall('function'):
                    value = function.find('value')
                    if value != None:
                        functionValue = value.text        
        return functionValue
    
    def setFunctionValue(self, sessionId, functionId, value, isRelative = False):
        function = str(functionId)
        if type(value) is int:
            functionValue = str(value)
        else:
            functionValue = value
        if isRelative == True:
            relativeStr = b' relative="true"'
        else:
            relativeStr = b''
        self.mysend(b'<function-value-change response-level="Always"><device><sessionid>' + sessionId.encode() + b'</sessionid>' + \
                   b'<function id="' + function.encode() + b'"><value' + relativeStr + b'>' + functionValue.encode() + \
                   b'</value></function></device></function-value-change>')
        recv = self.myReceive()
        self.testResponseOk(recv)

    