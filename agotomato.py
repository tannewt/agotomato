import threading
import time

import agoclient
import socket

import re
import json
 
import requests

CLIENT = agoclient.AgoConnection("tomato")

MIN_RSSI = -80

def message_handler(internal_id, content):
  print(internal_id, content)

CLIENT.add_handler(message_handler)

SERVER = agoclient.get_config_option("tomato", "server", "192.168.1.1")
USERNAME = agoclient.get_config_option("tomato", "username", "admin")
PASSWORD = agoclient.get_config_option("tomato", "password", "")
TOKEN = agoclient.get_config_option("tomato", "token", "")
 
def get_tomato_info(host, username, password, http_id):
    req = requests.post('http://{}/update.cgi'.format(host),
                        data={'_http_id':http_id, 'exec':'devlist'},
                        auth=requests.auth.HTTPBasicAuth(username, password))
 
    tomato = {param: json.loads(value.replace("\'",'\"'))
             for param, value in re.findall(r"(?P<param>\w*) = (?P<value>.*);", req.text)
             if param != "dhcpd_static"}
 
    req = requests.get('http://{}/wireless.jsx?_http_id={}'.format(host, http_id),
                        auth=requests.auth.HTTPBasicAuth(username, password))
 
    tomato.update({param: json.loads(value.replace("'",'"'))
                    for param, value in re.findall(r"(?P<param>\w*) = (?P<value>.*);", req.text)
                    if param != 'u'})
 
    return tomato

def get_devices():
    i = get_tomato_info(SERVER, USERNAME, PASSWORD, TOKEN)

    mac_to_name = {}
    for entry in i["dhcpd_lease"]:
        mac_to_name[entry[2]] = entry[0]
    current = set()    
    for entry in i["arplist"]:
        if entry[1] in mac_to_name:
            current.add(mac_to_name[entry[1]])
        else:
            current.add(entry[1])
    for entry in i["wldev"]:
        if entry[2] <= MIN_RSSI:
            continue
        if entry[1] in mac_to_name:
            current.add(mac_to_name[entry[1]])
        else:
            current.add(entry[1])
    return current

#    CLIENT.add_device(shade_id, "drapes")
#    CLIENT.emit_event(shade_id, "event.device.statechanged", state, "")
class readTomato(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)
        self.devices = {}

    def run(self):
        while True:
            current = get_devices()
            for device in current:
                if device not in self.devices:
                    CLIENT.add_device(device, "binarysensor")
                elif self.devices[device] == "present":
                    continue
                self.devices[device] = "present"
                print device, "was found"
                CLIENT.emit_event(device, "event.device.statechanged", 1, "")
            for device in self.devices:
                if self.devices[device] == "present" and device not in current:
                    print device, "went missing"
                    CLIENT.emit_event(device, "event.device.statechanged", 0, "")
                    self.devices[device] = "missing"
            time.sleep(30)

background = readTomato()
background.setDaemon(True)
background.start()

CLIENT.run() #blocks

