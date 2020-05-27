# import the necessary packages
from imutils.video import VideoStream
import datetime
import imutils
import time
import cv2
from Tracked import Tracked
import numpy as np
from bbdb import bbdb
from PIL import Image

class BirdBuddy:
	path = None #file path to process, or a unique primary key, like a path to the camera
	minArea = 225 #smallest size to track.
	db = None #The database handling object
	
	def __init__(self, db, path):
		BirdBuddy.db = db
		self.path = path
		self.firstFrame = None
		self.frame_count = 0
		self.Take_Screen_Grab = True #we dont have our base screen grab now
		self.TrackedList = [] #all objects being tracked
		self.StatusChange = 0 #Weve added or completed an object track
		self.video_width = 500 #the width of video as its analyzed
		self.video_height = 242 #and the height
	def addTrackedObject(to):
		BirdBuddy.db.addTrackedObject(to)		
	def closeEnough(TrackedObjects, x, y, w, h):
		#find the intersecting rectangle of the two and if they share a certain percentage its close enough
		percentage = 0
		for o in TrackedObjects:
			axmax = o.x + o.w #max x for first rectangle
			bxmax = x + w #max x for second rect
			axmin = o.x
			bxmin = x
			
			aymax = o.y + o.h
			bymax = y + h
			aymin = o.y
			bymin = y
			
			dx = min(axmax, bxmax) - max(axmin, bxmin)
			dy = min(aymax, bymax) - max(aymin, bymin)
			if (dx>=0) and (dy>=0):
				intersectArea = dx*dy
				originalArea = (axmax - axmin) * (aymax - aymin)
				newArea = (bxmax - bxmin) * (bymax - bymin)
				if (((intersectArea / originalArea) > percentage) or ((intersectArea / newArea) > percentage)): #calculate the ratio of the two areas
					return TrackedObjects.index(o)
		return -1  #Gone through list nothing matched well enough

	def processFrame(self, frame):
		self.frame_count = self.frame_count + 1 #Count the frames for later use
		# start reading the frames and initialize the screen		 
		text = "Empty" #Important to know whether anything is on the screen
		# if the frame could not be grabbed, then we have reached the end
		# of the video
		if frame is None:
			print("No image data supplied, returning")
			return
		
		# resize the frame, convert it to grayscale, and blur it
		original_frame = frame
		frame = imutils.resize(frame, width=self.video_width)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)

		# if the first frame is None, initialize it, or every 1000 frames no matter what
		if (self.firstFrame is None) or self.Take_Screen_Grab or (self.frame_count % 1000) == 0:
			self.firstFrame = gray
			self.Take_Screen_Grab = False #shouldnt need to keep taking over and over just in case
			#rectangles.write("Screen Grab\n")
			#print("taking screen grab"+ str(frame_count))
			return	# compute the absolute difference between the current frame and
		# first frame
		frameDelta = cv2.absdiff(self.firstFrame, gray)
		thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

		# dilate the thresholded image to fill in holes, then find contours
		# on thresholded image
		thresh = cv2.dilate(thresh, None, iterations=2)
		cnts = cv2.findContours(thresh.copy(), 
								cv2.RETR_EXTERNAL,
								cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		
		# loop over the contours
		for c in cnts:
			# if the contour is too small, ignore it
			if cv2.contourArea(c) < BirdBuddy.minArea:
				continue
			text = "Tracked:" + str(len(self.TrackedList))	# draw the text and timestamp on the frame
				# compute the bounding box for the contour, draw it on the frame,
			# and update the text
			(x, y, w, h) = cv2.boundingRect(c)
			##cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			#is this an existing Tracked being tracked?
			#compare the rectangle to existing Tracked rectangels
			#if its close enough extend the time sequence on the existing pbject
			#if not make another tracking rectangle
			#if it occupies 95% of the same area then its same enough
			#compare the intersection of the two bounding rectangles
			#if theres no Trackeds to contain it, make a new Tracked and insert it into the lists
			listIndex = BirdBuddy.closeEnough(self.TrackedList, x, y, w, h)
			#img = np.array(frame) #get the moved part of the image
			img = frame[y:y+h, x:x+w]

			if(listIndex != -1): #-1 if theres no existing box close enough
				if self.TrackedList[listIndex].classification == "unknown":
					classy = self.TrackedList[listIndex].classify(img,0.75) #Classify the image, 75% sure
					self.TrackedList[listIndex].classification = classy
				if self.TrackedList[listIndex].classification == "background": #if its the background weed it out
					self.TrackedList[listIndex].active = False #its reverted back to background, stop tracking it.
					continue
									
				#Now update the currently being tracked object
				x1 = x
				x2 = self.TrackedList[listIndex].x
				w1 = w
				w2 = self.TrackedList[listIndex].w
				y1 = y
				y2 = self.TrackedList[listIndex].y
				h1 = h
				h2 = self.TrackedList[listIndex].h
				
				self.TrackedList[listIndex].x = min(x1,x2) #make the box as big as possible
				self.TrackedList[listIndex].y = min(y1,y2)
				self.TrackedList[listIndex].w = max(x1+w1,x2+w2) - min(x1,x2)
				self.TrackedList[listIndex].h = max(y1+h1,y2+h2) - min(y1,y2)
					
				self.TrackedList[listIndex].active = True
				self.TrackedList[listIndex].frame_end = self.frame_count
				self.TrackedList[listIndex].image = img					
				#good to know the path it took
				track =  (x,y,w,h)
				self.TrackedList[listIndex].xywh_track.append(track)
				
			else: #if no box close enough, tack on another tracking frame
				o = Tracked(x,y,w,h,0,0,self.frame_count,self.frame_count,True,img) #reset the Tracked as active
				self.TrackedList.append(o)
				self.StatusChange = True
				print(o.toStr())
				#write out the image file that starts the object tracking
				#cv2.imwrite("file" + str(o.ID) + "start.png", img) #output the pic of the captured movement

		#Finished coutning contours now to process them a little further
		#remove all inactive all tracked objects that werent touched during the last loop
		count=0
		for o in self.TrackedList:
			if o.active == False:
				self.StatusChange = 1
				#write the Tracked to the output file
				#o.write(rectangles)
				#print out the image maybe
				#o.toPNG(path+str(frame_count)+".png", frame)
				
				#then remove it from the list and add it to the database
				(x,y,w,h) = (o.x,o.y,o.w,o.h)
				img = frame[y:y+h, x:x+w]
				o.image = img
				BirdBuddy.db.addTrackedObject(o, self.path)
				self.TrackedList.remove(o)
				
				#write the original full definition image
				#cv2.imwrite(self.path+str(frame_count)+".png", original_frame)
				
			
		#now for the remaining tracked objects set them to inactive unless found again
		for o in self.TrackedList:
			o.active = False #Reset it so it'll have to see motion to reactive the tracking rectangle.
			cv2.rectangle(frame, (o.x, o.y), (o.x + o.w, o.y + o.h), (0, 255, 0), 2)
			cv2.putText(frame, 
						str(o.ID), 
						(o.x, o.y),
						cv2.FONT_HERSHEY_SIMPLEX,
						0.5,
						(0, 0, 255),
						2)
 
		#Now  we need to write to the log file, all relevant information	
		if self.StatusChange == True: #something was added or removed
			if len(self.TrackedList) == 0: #so we dont write empty room until movement is detected
				print("The Room is Empty\n")
				self.Take_Screen_Grab = True #and lets use this opportunity to update the screen
			else:
				print("There are " + str(len(self.TrackedList))+ "objects being tracked\n")
				self.StatusChange = 0 #We have recored the change in status
				self.firstFrame = gray
			self.StatusChange = False
		else:
			if len(self.TrackedList) == 0:
				self.firstFrame = gray
	
		#Write the graphics on the screen showing the status of the room
		cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
					(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
	def classify(self, path):
		#loop through every row matching the path 
		recs = BirdBuddy.db.getRecords(path)
		htmloutput = """
<HTML>
<head>
	<title>Training</title>
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
	<link href="style.css", ref="stylesheet">
</head>
<body>
	<div class="row">
		<div class ="col-md-6 no-gutters"
			<div class="leftside">
				<table width=\"500\" border=\"1\" cellpadding=\"5\">
				<tr>
		"""

		for index, row in recs.iterrows():
			image_data = row['image']
			width = row['w']
			height = row['h']
			name = str(row['id']) + row['path'] + ".PNG"

			htmloutput = htmloutput + """
				<td align = \"center\" valign = \"center\">
				<img src=\"%s\" alt=\"description here\">
				<br>
				Caption text centered under the image.
				<SELECT>
			""" % name
			#Save the image file for output
			img = Image.frombytes('RGB', (width,height), image_data, 'raw')
			img.save(name, "PNG")			
			#Display most likely pattern matches
			likely = BirdBuddy.db.getPossibles(path) #return a tuple with likelihoods for each listed possbility
			#create an html page with all the images put to disc and a drop down box to select likelies and a textbox to type a new one
			#likely = ((0.4, "junk"),(.7,"Good"),(0.99,"me"))
			
			for count, l in enumerate(likely):
				htmloutput = htmloutput + """
					<option value=\"%s\">%s</option>
				""" % (likely[count][1], likely[count][1] + "-" + str(likely[count][0]))
			#Finish the table of captured images and teaching probabilities, with a text input field for the user
			#to write his own description of the captured motion
			htmloutput = htmloutput + """
				</SELECT>
				Type your description
				<input type="text" id=\"%s\" name=\"%s\"><br>
				<input type="submit">
				</td>
			""" % (name, name)
			#Every third image add a row
			if index % 3 == 0 and index > 1:
				htmloutput = htmloutput + """
				</TR>
				"""
		#Finish and write the html file
		htmloutput = htmloutput + """
			</div>
		</div>
	</div>
	<div class = "col-md-6 no-gutters">
		<div class="rightside">
			Right side
		</div>
	</div>
</BODY>
</HTML>
		"""
		file = open("index.html","w")
		file.write(htmloutput)
		file.close()
	def getClassificationFromUser(self, probables):
		ret = int(input("Selection? "))
		return probables[ret][0]
