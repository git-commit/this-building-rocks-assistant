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

"""A demo of the Google Assistant GRPC recognizer."""

import logging

import aiy.cloudspeech
import aiy.audio
import aiy.voicehat

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def main():
    status_ui = aiy.voicehat.get_status_ui()
    status_ui.status('starting')
    
    recognizer = aiy.cloudspeech.get_recognizer()   
    button = aiy.voicehat.get_button()
    with aiy.audio.get_recorder():
        while True:
            status_ui.status('ready')
            print('Press the button and speak')
            button.wait_for_press()
            status_ui.status('listening')
            print('Listening...')
            text = recognizer.recognize()
            if text:
                if 'what\'s the humidity inside' in text:
                    aiy.audio.say('The relative humidity is over 9000.')    
                elif 'test' in text:
                    aiy.audio.say('ok google')
                print('You said "', text, '"')


if __name__ == '__main__':
    main()
