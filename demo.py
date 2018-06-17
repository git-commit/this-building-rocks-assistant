#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import requests
import json
import time

import logging
import platform
import subprocess
import sys

import aiy.assistant.auth_helpers
from aiy.assistant.library import Assistant
import aiy.audio
import aiy.voicehat
import aiy.assistant.grpc
from google.assistant.library.event import EventType
from google.assistant.library.event import Event

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def power_off_pi():
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi():
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

def humidity_info(humidity):
    aiy.audio.say('The humidity is at ' + str(humidity) + ' percent! Can I open up the window for you?')

def window_request(url,headers):
    time.sleep(.5)
    responder = aiy.assistant.grpc.get_assistant()
    with aiy.audio.get_recorder():
        while True:
            text, audio = responder.recognize()
            if text:
                if "yes" in text:
                        open = 1
                        r = requests.patch(url + window_id, data=json.dumps({'custom':{'open':True}}), headers=headers)
                else:
                        open = 0
                break;
    if open:
        aiy.audio.say("Ok, I am opening the window!")
    else: 
        aiy.audio.say("Sure thing.")

def process_event(assistant, event, humidity, window_id, url, headers):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')
        
    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        print('You said:', event.args['text'])
        text = event.args['text'].lower()
        if text == 'power off':
            assistant.stop_conversation()
            power_off_pi()
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()
        elif 's the humidity inside' in text:
            assistant.stop_conversation()
            humidity_info(humidity)
            window_request(url, headers)
        
    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
          or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
          or event.type == EventType.ON_NO_RESPONSE):
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def main():
    indoor_id = 'cffbf07c-4789-4762-9895-c23f0298a495'
    url1 = 'https://api.preview.oltd.de/v1/devices/'
    url2 = '/state'
    endpoint_indoor = url1 + indoor_id + url2
    headers = {"Authorization":"Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJNRWo4QkVEaWZnSnBfTzB3OEJCbEYxU05TNElmdlMyLWhERFBWTDRaTDYwIn0.eyJqdGkiOiIwMWUyMjgzMy1mZTdkLTQ0YjUtYTkzNS03YjE5YjE5ZjgwMzIiLCJleHAiOjE1MzAwMjMxMDEsIm5iZiI6MCwiaWF0IjoxNTI5MTU5MTAxLCJpc3MiOiJodHRwczovL2FwaS5wcmV2aWV3Lm9sdGQuZGUvYXV0aC9yZWFsbXMvb2x0IiwiYXVkIjoib2x0X3BvcnRhbCIsInN1YiI6ImMzZThhYjZmLTA3MDYtNDVhNC05Y2U1LWMyY2IwMDYyMmMzNyIsInR5cCI6IkJlYXJlciIsImF6cCI6Im9sdF9wb3J0YWwiLCJub25jZSI6IkUxWHFta0N4ZGd5ZGs3UGhFcmNZQ2VVQmd4ZmFGYXg4NVVwb3ZZT0giLCJhdXRoX3RpbWUiOjE1MjkxNTkxMDEsInNlc3Npb25fc3RhdGUiOiI2NDQ1MDVmMS04NTg2LTQyNjYtOWFmYy0yMDc4NDVlMGQ0OWUiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbXSwicmVzb3VyY2VfYWNjZXNzIjp7fSwiZW1haWxfdmVyaWZpZWQiOnRydWUsInByZWZlcnJlZF91c2VybmFtZSI6Im9zci1vbHQtZ2F0ZXdheS1lazkxNjBAbWFpbGluYXRvci5jb20iLCJnaXZlbl9uYW1lIjoiT0xUIEdhdGV3YXkgIiwiZmFtaWx5X25hbWUiOiJFSzkxNjAiLCJlbWFpbCI6Im9zci1vbHQtZ2F0ZXdheS1lazkxNjBAbWFpbGluYXRvci5jb20iLCJ0ZW5hbnQiOiI5YzRkMDhjMS1hNmRmLTQyZmQtYWQ0MS1mNzZjYjRhY2Y5M2UifQ.lqzYoQzzRNavIbDvdYVWF-0DhsxMfxTwlDlEh6icuA5YrhFk83-ntT6jgEuu2n-1EKvptihgafrIUxfCTCMFkXsbHNMoPmd9tG0REyLLVMqY5uwzCrIQYL7jNyKlpsttV-sBU2ZLbRtu_DV0Iu550gZuYBuTGpoXvEiZ1ArdlDuHkDykrRHPAixZXe_9yeXspJ2OBp8F3URt83vYc1e8HCWOaNT_9iEnZSWVmlADjt85BAhBpjBG81IO6V4FVXwQbjo8I3acLldqG82O9LDlzgLdjLNMyFGJ2Gm1Ooxa3yRPNvI1z9xgoOUdOvDvKdEEwG1kywsvECmoCvp6U9QL1A"}
    
    headers2 = {"Authorization":"Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJNRWo4QkVEaWZnSnBfTzB3OEJCbEYxU05TNElmdlMyLWhERFBWTDRaTDYwIn0.eyJqdGkiOiJlNjU2M2Y4ZS1lMzc0LTRkZWEtODFkMy05NjQwYTVlNWIxZWYiLCJleHAiOjE1Mjk5NDc2NzEsIm5iZiI6MCwiaWF0IjoxNTI5MDk2OTYyLCJpc3MiOiJodHRwczovL2FwaS5wcmV2aWV3Lm9sdGQuZGUvYXV0aC9yZWFsbXMvb2x0IiwiYXVkIjoib2x0X3BvcnRhbCIsInN1YiI6ImIwNzc1Yjc0LWExYjAtNDAzOS1hMzcxLTg4N2Y1ZjIxZTJmYyIsInR5cCI6IkJlYXJlciIsImF6cCI6Im9sdF9wb3J0YWwiLCJub25jZSI6IlVIeElWVkdET1ZzbjhZbkdEU1o1QWdlTWl5YW1PQUFrVE83SjFqU3UiLCJhdXRoX3RpbWUiOjE1MjkwODM2NzEsInNlc3Npb25fc3RhdGUiOiJmZTFlYWJiMC1mMGVhLTQ5ZjEtYTNjNC1jODZhMThjNGIyNGEiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbXSwicmVzb3VyY2VfYWNjZXNzIjp7fSwiZW1haWxfdmVyaWZpZWQiOnRydWUsInByZWZlcnJlZF91c2VybmFtZSI6ImJlcmdlci5tYXhpbWlsaWFuQGdteC5kZSIsImdpdmVuX25hbWUiOiJNYXhpbWlsaWFuIiwiZmFtaWx5X25hbWUiOiJCZXJnZXIiLCJlbWFpbCI6ImJlcmdlci5tYXhpbWlsaWFuQGdteC5kZSIsInRlbmFudCI6IjgwNWM0NDIwLTQxNjEtNGI0ZC1iZDI4LTNkMzNmNjkxZjI0MSJ9.jJqDQ4Y2srcJjUMY98F7u4EXVhBlTInLND6UFs5b1cF6iUczMedn_bK-hcNIzPnBAtEO8330vZ4pnYED5Kr5Whuwl6Z1_hVfa7d_zQ2I01prCpPZX7syQZqX-fvPqUDjpXITPUyAli03Eo6VVhZVI7HpHj5sh1qEa4Xr2qitRXAHqUgC5jw8WOPOL7Mwpmy9UmoKZVdTOrhYsuM1tIeShkQNOjBy2iYbi7OBHn2Gl74zPwqcqnL1jUgYeLjsYNKbTB-VB2VUtzIJXC_jeYraJLNWoqBQpgBUgr-YgkeXgG2kB9PmEHeXW2f6AeLtf3uHSLMqnFixK2SAhtej3-DQGA"}
    window_id = 'a2394935-749c-4783-b159-097a83a5a32b'
    
    r = requests.patch(url1 + window_id, data=json.dumps({'custom':{'open':True}}), headers=headers2)
    print(json.dumps({'custom':{'open':True}}))


    if platform.machine() == 'armv6l':
        print('Cannot run hotword demo on Pi Zero!')
        exit(-1)
    
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        r = requests.get(endpoint_indoor, headers=headers)
        humidity = round(r.json()['data']['attributes']['FTKPlus']['properties']['Humidity'], 1)

        for event in assistant.start():
            process_event(assistant, event, humidity, window_id, url1, headers2)


if __name__ == '__main__':
    main()
