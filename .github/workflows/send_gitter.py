"Script for sending a message to our gitter channel."

# To update the token, go to https://developer.gitter.im/apps and copy the token to the github repository secret
# GITTER_TOKEN

import os
import requests


GITTER_TOKEN = os.getenv('token')
GITTER_ROOM_ID = os.getenv('room-id')
GITTER_TEXT = os.getenv('text')
GIT_REF = os.getenv('GITHUB_REF')
GIT_SHA = os.getenv('GITHUB_SHA')

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f"Bearer {GITTER_TOKEN}",
}

data = f'{{"text":"{GIT_REF}:{GIT_SHA}: {GITTER_TEXT}"}}'

response = requests.post(f'https://api.gitter.im/v1/rooms/{GITTER_ROOM_ID}/chatMessages', headers=headers, data=data)
