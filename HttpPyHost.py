import socket
import sys
import threading
import queue
import time
import datetime
import multiprocessing
import os
import json
from typing import Any, cast


class HttpRequest:
    _splitCr = '\r'
    _splitNewLine = '\n'
    _splitQuery = '?'
    _splitAnd = '&'
    _splitEqual = '='
    _splitSpeace = ' '
    _splitSlash = '/'
    _splitColon = ':'
    httpVersion = ""
    method = ""
    header = ""
    body = ""
    url = ""
    urlParam = ""
    urlFull = ""
    raw: str

    def ToJson(self):
        return json.dumps({
            "httpVersion": self.httpVersion,
            "header": self.header,
            "body": self.body,
            "method": self.method,
            "url": self.url,
            "urlParam": self.urlParam,
            "urlFull": self.urlFull,
            "raw": self.raw
        })
    
    def __init__(self, strReceived=""):
        self.raw = strReceived
        self.__parse(strReceived)

    def __parse(self, strReceived):
        if strReceived=="": return
        # parse your received string
        lines = strReceived.split(self._splitNewLine)
        firstLine = lines[0].split(self._splitSpeace)
        self.httpVersion = firstLine[2].strip(self._splitCr).strip(
            self._splitNewLine).strip(self._splitSpeace)
        self.urlFull = firstLine[1]
        urlParams = self.urlFull.split(self._splitQuery)
        self.url = urlParams[0]
        self.urlParam = urlParams[1] if len(urlParams) > 1 else ""
        self.method = firstLine[0].lower()
        beginBody = 0
        linesCount = len(lines)
        for i in range(1, linesCount):
            l = lines[i].strip(self._splitCr).strip(self._splitNewLine)
            self.header = self.header + l+"\n"
            if(not l):
                beginBody = i
                break

        for i in range(beginBody, linesCount):
            self.body = self.body + lines[i]+"\n"

        self.body = self.body.strip(self._splitCr).strip(self._splitNewLine)
        return self


class HttpResponse:
    header = ""
    body = ""
    httpStatus = ""
    _request: HttpRequest

    def __init__(self, request: HttpRequest=Any):
        self.header: str
        self.body: str
        self.httpStatus = "200"
        self._request = cast(HttpRequest, request) if isinstance(request, HttpRequest) else  HttpRequest()

    def JsonContent(self, obj):
        self.body = json.dumps(obj)
        self.httpStatus = "200"
        return self

    def NotFound404(self, request: HttpRequest):
        self.httpStatus = "404"
        self.body = request.ToJson()
        return self

    def ToJson(self):
        return json.dumps({
            "header": self.header,
            "body": self.body,
            "httpStatus": self.httpStatus
        })

class RoutingHandle:
    def __init__(self):
        self.__routing = {}
        self.__routing[""] = self.Index
        self.__routing["/"] = self.Index

    def Index(self, request: HttpRequest):

        return HttpResponse().JsonContent({"name": "nguyen phan du"})

    def Handle(self, request: HttpRequest):
        if (request.url in self.__routing):
            return self.__routing[request.url](request)

        return HttpResponse().NotFound404(request)


def socketHandleRequest(conn: socket.socket, clientAddress):
    try:
        requestData = []
        while True:
            temp = conn.recv(4096000000, 0)
            #if not temp:
            #    break
            requestData.append(temp)
            break

        # process requestData
        requestInString = ''.join(map(lambda x: str(x, "utf-8"), requestData))

        objRequest = HttpRequest(requestInString)
        
        print('Request:\r\n')
        print(requestInString)

        objResponse = RoutingHandle().Handle(objRequest)

        # process response
        if not objResponse:
            objResponse = HttpResponse().NotFound404(objRequest)

        bodyInBytes = bytes(objResponse.body, "utf-8")

        objResponse.header = objResponse.header + objRequest.httpVersion+" "+objResponse.httpStatus+"\r\n"
        objResponse.header = objResponse.header+"Server: HttpPyHost-v1\r\n"
        objResponse.header = objResponse.header+"Content-Type: application/json\r\n"
        objResponse.header = objResponse.header+"Connection: close\r\n"
        objResponse.header = objResponse.header + f"Content-Length: {len(bodyInBytes)}\r\n\r\n"

        try:
            print('Response:\r\n')
            print(objResponse.header)
            print(objResponse.body)
            conn.sendall(bytes(objResponse.header, "utf-8"), 0)
            conn.sendall(bodyInBytes, 0)
        except Exception as e:
            print(json.dumps({"code": "0", "message": f"{e}"}))
    except Exception as ex:
        print(f"{ex}")
    finally:         
        conn.close()

_hostOrDomain="localhost"
_port=8081

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (_hostOrDomain, _port)
sock.bind(server_address)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
sock.listen(1)
sock.settimeout(120)

print(f"Listening {server_address}")

_isStopListenter=False

def socketWorker (currentSock:socket.socket):   
    while not _isStopListenter:
        try:
            client_conn, client_address = currentSock.accept()  # wait next request comming
            print(f"Connected Client address: {client_address}")
            # process current request
            currentConnectThread=threading.Thread(target=socketHandleRequest, args=(client_conn,client_address,))
            currentConnectThread.daemon=True
            currentConnectThread.start()

        except Exception as ell:
            print(json.dumps({"code": "0", "message": f"{ell}"}))
        
"""
# can not do multiprocessing
_socketWorkers=[]
for in in range(10)
    sw = multiprocessing.Process(target=socketWorker, args=(sock,))
    _socketWorkers.append(sw)

for sw in _socketWorkers:
    sw.daemon=True
    sw.start()
"""
mainThread=threading.Thread(target=socketWorker, args=(sock,) , daemon=True)
mainThread.start()

while True:
    cmd = input()
    if cmd =="quit":               
        break
    else :
        time.sleep(1)

_isStopListenter=True

def _selfCallStop():
    try:
        print("Call to stop socket listener")
        callToClose = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        callToClose.connect((_hostOrDomain,_port))    


_selfCallStop()

mainThread.join()

sock.close()   

print("Stoped socket")
