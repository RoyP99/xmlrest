'''
Created on Jan 29, 2021

@author: robert
'''

from flask import Flask, jsonify, request, make_response, abort
import socket
import xmlGw

app = Flask(__name__)
ipaddr = '0.0.0.0'
isConnected = False

xmlgw = xmlGw.XmlGatewayImpl()

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'not found'}), 404)

@app.route('/', methods=['GET'])
def index():    
    return jsonify([ 'ip/', 'device/' ])

@app.route('/ip', methods=['GET', 'POST'])
def ip():
    global ipaddr, isConnected
    if request.method == 'POST': 
        if not request.json or not 'address' in request.json:
            abort(400)
        try:
            taddr = request.json['address']
            socket.inet_aton(taddr)
            if ipaddr != taddr and isConnected == True:
                xmlgw.disconnect()
                isConnected = False
            ipaddr = taddr            
        except:
            return make_response(jsonify({'error': 'invalid ip address'}), 404)
    return jsonify({ 'address' : ipaddr})

@app.route('/device/', methods=['GET'])
@app.route('/device/<devtype>/', methods=['GET'])
@app.route('/device/<devtype>/<devname>', methods=['GET'])
@app.route('/device/<devtype>/<devname>/<int:funcid>', methods=['GET'])
def device(devtype=None, devname=None, funcid = None):
    global ipaddr, isConnected
    if isConnected == False:
        try:
            xmlgw.connect(ipaddr)
            isConnected = True
        except:
            return make_response(jsonify({'error': 'connect error to '+ipaddr}), 404)
    try:
        devices = xmlgw.getDevices()
    except:
        return make_response(jsonify({'error': 'no devices'}), 404)
    if devtype == None:
        devTypes = []
        for device in devices:
            if device['type']+'/' not in devTypes:
                devTypes.append(device['type']+'/')        
        return jsonify(devTypes)
    elif devname == None:        
        devnames = []
        for device in devices:
            if device['type'] == devtype:
                devnames.append(device['name'])
        return jsonify(devnames)
    elif funcid == None:
        funcids = []
        sessionId = None
        for device in devices:
            if device['type'] == devtype and device['name'] == devname:
                sessionId = device['sessionid']
                break
        if sessionId == None:
            return make_response(jsonify({'error': 'device not found'}), 404)
        try:
            funcInfos = xmlgw.getAllFunctionInformation(sessionId)
        except:
            return make_response(jsonify({'error': 'device not found'}), 404)
        for funcInfo in funcInfos:
            funcids.append(str(funcInfo['id'])+'/')
        return jsonify(funcids)
    else:
        for device in devices:
            if device['type'] == devtype and device['name'] == devname:
                sessionId = device['sessionid']
                break
        if sessionId == None:
            return make_response(jsonify({'error': 'device not found'}), 404)
        try:
            funcInfo = xmlgw.getFunctionInformation(sessionId, funcid)
        except:
            return make_response(jsonify({'error': 'device not found'}), 404)
        return jsonify(funcInfo)
    
@app.route('/device/<devtype>/<devname>/<int:funcid>', methods=['POST'])
def devicePut(devtype=None, devname=None, funcid = None):
    global ipaddr, isConnected
    if devtype != None and devname != None and funcid != None:
        if not request.json or not 'value' in request.json:
            abort(400)
            
        if isConnected == False:
            try:
                xmlgw.connect(ipaddr)
                isConnected = True
            except:
                return make_response(jsonify({'error': 'connect error to '+ipaddr}), 404)
        try:
            devices = xmlgw.getDevices()
        except:
            return make_response(jsonify({'error': 'no devices'}), 404)
        
        for device in devices:
            if device['type'] == devtype and device['name'] == devname:
                sessionId = device['sessionid']
                break
        if sessionId == None:
            return make_response(jsonify({'error': 'device not found'}), 404)
        try:
            xmlgw.setFunctionValue(sessionId, funcid, request.json['value'])
        except:
            return make_response(jsonify({'error': 'device not found'}), 404)
        return ('', 204)
    else:
        return make_response(jsonify({'error': 'function not found'}), 404)
        
if __name__ == '__main__':
    app.run()
    