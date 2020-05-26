# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 13:46:06 2019

@author: Larry
"""
import datetime
import cv2
import numpy as np
from sklearn.metrics import r2_score

class Tracked:
	ID=0
	CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat","bottle", "bus", "car", "cat", "chair", "cow", "diningtable","dog", "horse", "motorbike", "person", "pottedplant", "sheep","sofa", "train", "tvmonitor"]
	COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
		
	# load our serialized model from disk
	#net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt.txt", "MobileNetSSD_deploy.caffemodel")   
 
	def __init__(self, x, y,w,h,start,end,frame_start,frame_end,active,image):
		self.x=x #define the rectangle
		self.y=y
		self.w=w 
		self.h=h 
		self.start_time=start #start time in video
		self.end_time=end
		self.frame_start=frame_start #and the frame number as well
		self.frame_end=frame_end
		self.active=active #is it still being tracked?
		self.classification = "unknown"
		self.ID = Tracked.ID
		Tracked.ID += 1
		self.xywh_track = []
		self.image = None
		self.previousHistogramRed = cv2.calcHist(image, [0], None, [256], [0, 256])
		self.previousHistogramGreen = cv2.calcHist(image, [1], None, [256], [0, 256])
		self.previousHistogramBlue = cv2.calcHist(image, [2], None, [256], [0, 256])
		
			 	
	def write(self, file):
		file.write("Object ID:" + str(self.ID)+ "\n")
		file.write("Dimensions:" + str(self.x) + "," + str(self.y) +","+str(self.w)+","+str(self.h)+"\n")
		file.write("TimeStamp" + str(datetime.datetime.now())+"\n")
		file.write("Frame Bounds" + str(self.frame_start) + "-" + str(self.frame_end) + "\n")
		file.write("\n")
	
	def toStr(self):
		return str("Object ID:" + str(self.ID)+ " created\n" + "Classification: " + self.classification + "\n")
	
	def toPNG(self, filename, frame):
		cv2.imwrite(filename, frame) #for now its just the first frame as the base image
		
	def toSQLiteDB(self, db):
		print("outputting to database")
		
	def classify(self, frame, min_confidence):
		#get the histogram for each channel, if all 3 close enough its background
		#if its close enough to the original one, classify it as background
		histRed = cv2.calcHist(frame, [0], None, [256], [0, 256])
		histGreen = cv2.calcHist(frame, [1], None, [256], [0, 256])
		histBlue = cv2.calcHist(frame, [2], None, [256], [0, 256])
		r2Red = r2_score(histRed, self.previousHistogramRed)
		r2Green = r2_score(histGreen, self.previousHistogramGreen)
		r2Blue = r2_score(histBlue, self.previousHistogramBlue)
		self.previousHistogramRed = histRed
		self.previousHistogramGreen = histGreen
		self.previousHistogramBlue = histBlue
		
		if r2Red > 0.9 and r2Green > 0.9 and r2Blue > 0.9:
			return "background"
		
		#Now check if its stuck, then drop it
		list_length = len(self.xywh_track)
		same_in_a_row = 0
		index = list_length  - 1
		stuck_at = 10

		if list_length > stuck_at:
			while same_in_a_row < stuck_at:
				track1 = self.xywh_track[index]
				track2 = self.xywh_track[index -1]
				if track1 == track2:
					same_in_a_row = same_in_a_row + 1
					index = index - 1
				else:
					break
		
		if same_in_a_row == stuck_at:
			return "background"
		

				
		return "unknown"
		
