from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2
import time
import requests
import os
import random
import json

looptime = 5

# Machine ID
ID = 11222

# Lists
prod = ["caffe", "cioccolato", "te", "cappucino", "laghine"]

trans = ["rfid", "cash", "app"]

# Amazon URL
ec2 = 'http://ec2-18-212-110-170.compute-1.amazonaws.com:3000'

# Microsoft API
subscription_key = os.environ['API_KEY']
vision_base_url = "https://francecentral.api.cognitive.microsoft.com/vision/v2.0/"
vision_analyze_url = vision_base_url + "analyze"


headers = {'Ocp-Apim-Subscription-Key': subscription_key,
           "Content-Type": "application/octet-stream"}

params = {'visualFeatures': 'Objects,Faces'}


debug = False
ssh = False


def getRectangle(personDict):
    if 'object' in personDict.keys():
        if(personDict['object'] == 'person'):
            rect = personDict['rectangle']
            left = rect['x']
            top = rect['y']
            bottom = left + rect['w']
            right = top + rect['h']
            return left, top, bottom, right
    else:
        rect = personDict['faceRectangle']
        left = rect['left']
        top = rect['top']
        bottom = left + rect['height']
        right = top + rect['width']
        return left, top, bottom, right


camera = PiCamera()
camera.resolution = (1280, 720)
time.sleep(0.1)

elapsed_time = 0
try:
    while True:

        print(elapsed_time)

        # Per evitare di fare più di 20 chiamate al min
        if (elapsed_time < looptime):
            time.sleep(looptime - elapsed_time)

        start_time = time.time()

        rawCapture = PiRGBArray(camera)
        camera.capture(rawCapture, format="bgr")
        frame = rawCapture.array

        img_str = cv2.imencode('.jpg', frame)[1].tostring()

        response = requests.post(vision_analyze_url,
                                 headers=headers,
                                 params=params,
                                 data=img_str)

        if response.status_code != 200:
            raise Exception("Error:", response)

        parsed = response.json()

        people = 0
        faces = len(parsed['faces'])

        for obj in parsed['objects']:
            if (obj['object'] == 'person'):
                people += 1
                x, y, w, h = getRectangle(obj)
                cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)

        for face in parsed['faces']:
            x, y, w, h = getRectangle(face)
            cv2.rectangle(frame, (x, y), (w, h), (0, 0, 255), 2)

        print("<", people, " people, ", faces, "faces> ")

        url_ord = ec2 + '/' + str(ID) + '/order'

        trn = trans[random.randint(1, len(trans) - 1)]
        prd = prod[random.randint(1, len(prod) - 1)]

        # TODO: add products levels
        tmp = {"transaction_type": trn,
               "product": prd,
               "satisfaction": random.random(),
               "people_detected": people,
               "face_recognised": faces
               }

        url_frame = ec2 + '/' + str(ID) + '/live'
        path = str(ID) + ".jpg"
        res = cv2.resize(frame, (640, 360))
        cv2.imwrite(path, res)

        with open(path, 'rb') as f:
            try:
                requests.post(url_ord, json=json.dumps(tmp))
                requests.post(url_frame, files={"frame": f})
            except Exception as e:
                print('Error:', e)

        elapsed_time = time.time() - start_time

except Exception as e:
    print('Error:', e)
