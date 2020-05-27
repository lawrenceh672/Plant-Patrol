import cv2
import time
import numpy as np
from BirdBuddy import BirdBuddy
from bbdb import bbdb

key = cv2. waitKey(1)
webcam = cv2.VideoCapture(0)
#take a pic every interval
#compare it to previous baseline image
#if different, run image recongnition on difference area
#if plant growth, set new baseline image
#analyze plant image to determine Age, Health
#update database with image, timestamp
t1 = time.perf_counter()
picture_interval = 3

def onChangeInterval(self):
    print(cv2.getTrackbarPos('interval', 'image'))

# Create a black image, a window
img = np.zeros((300,512,3), np.uint8)
cv2.namedWindow('image')
cv2.createTrackbar('interval','image',picture_interval,60,onChangeInterval)

#Make the Birdbuddy object to process the frames for information
db = bbdb()
bb = BirdBuddy(db, "Text XZ1")
db.wipeDB()

while True:
    try:
        check, frame = webcam.read()
        cv2.imshow("Capturing", frame)
        key = cv2.waitKey(1) #wait 1ms second for kb input
        t2 = time.perf_counter()
        picture_interval = cv2.getTrackbarPos('interval', 'image')
        if t2-t1 > picture_interval: #one second later
            filename = "PP_img_" + str(time.localtime().tm_hour) + str(time.localtime().tm_min) + str(time.localtime().tm_sec) + ".png"
            cv2.imwrite(filename, img=frame)
            print("Image saved!")
            t1 = t2 #reset the timer
            #Process this frame
            bb.processFrame(frame)
            
        if key == ord('q'):
            print("Turning off camera.")
            webcam.release()
            print("Camera off.")
            print("Program ended.")
            cv2.destroyAllWindows()
            break
        
    except(KeyboardInterrupt):
        print("Turning off camera.")
        webcam.release()
        print("Camera off.")
        print("Program ended.")
        cv2.destroyAllWindows()
        break
#After the camera is off lets get input from the user to classify the captured changes in the image
bb.classify("Text XZ1")