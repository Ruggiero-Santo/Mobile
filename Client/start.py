import requests
import time
from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2
import os
import numpy as np
from PIL import Image

subscription_key = os.environ['API_KEY']

vision_base_url = "https://francecentral.api.cognitive.microsoft.com/vision/v2.0/"
vision_analyze_url = vision_base_url + "analyze"


headers    = {'Ocp-Apim-Subscription-Key': subscription_key, 
              "Content-Type": "application/octet-stream" }

params     = {'visualFeatures': 'Objects,Faces'}




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
        
        #Per evitare di fare più di 20 chiamate al min
        if (elapsed_time < 3.1):
                time.sleep(3 - elapsed_time)
                
        start_time = time.time()

        rawCapture = PiRGBArray(camera)
        camera.capture(rawCapture, format="bgr")
        frame = rawCapture.array

        #~ frame = cv2.flip(frame, -1)
        
        img_str = cv2.imencode('.jpg', frame)[1].tostring()
        

        response   = requests.post(vision_analyze_url, 
                           headers=headers, 
                           params=params, 
                           data=img_str)

        if response.status_code != 200:
            raise Exception("Error:" , response)
            

        parsed = response.json()

        people = 0
        faces = len(parsed['faces'])
        
        if(debug):
            for obj in parsed['objects']:
                if (obj['object'] == 'person'):
                    people += 1
                    x,y,w,h = getRectangle(obj)
                    cv2.rectangle(frame,(x, y), (w, h), (0, 255, 0), 2)

            
            for face in parsed['faces']:
                x,y,w,h = getRectangle(face)
                cv2.rectangle(frame,(x, y), (w, h), (0, 0, 255), 2)
            
            
            elapsed_time = time.time() - start_time
            print("<", people , " people, ", faces, " faces> " , elapsed_time , " seconds")
            
            if(ssh):
                img2 = Image.fromarray(frame, 'RGB')
                b, g, r = img2.split()
                img2 = Image.merge("RGB", (r, g, b))
                img2.show()
            else:
                cv2.imshow('frame',frame)
                cv2.waitKey(30)
            
        else:
            for obj in parsed['objects']:
                if (obj['object'] == 'person'):
                    people += 1
            
            elapsed_time = time.time() - start_time
            print("<", people , " people, ", faces, " faces> " , elapsed_time , " seconds")
            
            
        
except Exception as e:
    print('Error:')
    print(e)