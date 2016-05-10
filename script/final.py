import cv2
import MySQLdb
import urllib 
import thread
import time
import numpy as np
import sys
from PIL import Image

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from datetime import datetime


url = "http://ip:port/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=xxx&pwd=xxx"
#cap = cv2.VideoCapture(url)
#time.sleep(1)
stream=urllib.urlopen(url)
bytes = ""

cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') 
minArea = 10000
startX, startY = 260, 20
majorAxis, minorAxis = 180, 140
centerX, centerY = 400, 200
index = 0

def getFrame():
	global  bytes
	global stream
	bytes += stream.read(1024)
	a = bytes.find('\xff\xd8')
	b = bytes.find('\xff\xd9')
	if a != -1 and b != -1:
		jpg = bytes[a:b+2]
		bytes= bytes[b+2:]
		img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
		return img
	else:
		return None

def motionDetection(re, cur):
	
	#s, frame = cap.read()
	firstFrame = None
	stableCount = 0
	#flag to prevent re-creating images on desktop
	flag = None
	while True:
		#s, frame = cap.read()
		frame = getFrame()
		if frame is None:
			continue
		img = cv2.resize(frame, (800, 500))
		img1 = img[startY : (startY + majorAxis * 2), startX : (startX + minorAxis * 2)]

		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (21, 21), 0)
		roi = gray[startY : (startY + majorAxis * 2), startX : (startX + minorAxis * 2)]
		if firstFrame is None:
			firstFrame = roi
			continue

		delta = cv2.absdiff(firstFrame, roi)
		thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations = 2)
		(cnt, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, 
				   cv2.CHAIN_APPROX_SIMPLE)

		count = 0
		for c in cnt:
			if cv2.contourArea(c) < minArea:
				continue
			
			count = 1
			if flag is None:
				stableCount += 1
				if stableCount < 50:
					continue

				try:
					thread.start_new_thread(faceRecgnition, (img.copy(), re, cur))
					stableCount = 0
				except:
					print "Can not start new thread"
				
		 	 	flag = True
		
			
			(x, y, w, h) = cv2.boundingRect(c)
			cv2.rectangle(img1, (x, y), (x + w, y + h), (0, 255, 0), 2)
		if count == 0:
			flag = None

		cv2.ellipse(img, (centerX, centerY), (minorAxis, majorAxis), 0, 0, 360, 0, 0)
		cv2.imshow("test", img)
	
		# cv2.imshow("roi", roi)
		#cv2.imshow("th", thresh)
		#cv2.imshow("delt", delta)

		key = cv2.waitKey(1)
		if key == ord("q"):
			break

	#cap.release()
	cv2.destroyAllWindows()

def trainImage(cur):
	#first need to train sample images in database
	recognizer = cv2.createLBPHFaceRecognizer()
	#get training image path from database and train them
	sql = "SELECT * FROM users"
	cur.execute(sql)
	
	images = []
	labels = []
	for row in cur.fetchall():
		#need to modify the argument
		label = row[0]
		
		image_pil = Image.open(row[4]).convert('L')
		image = np.array(image_pil, 'uint8')
		#faces = cascade.detectMultiScale(image, 1.3, 5, minSize = (70, 70), flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
		faces = cascade.detectMultiScale(image)
		# If face is detected, append the face to images and the label to labels
		for (x, y, w, h) in faces:
			cv2.imshow("Adding faces to traning set...", image[y: y + h, x: x + w])
			images.append(image[y: y + h, x: x + w])
			labels.append(row[0])
	
	
	recognizer.train(images, np.array(labels))
	return recognizer
	
def faceRecgnition(img, re, cur):
	global index
	tmpPath = "SET A PICTURE PATH HERE" #This picture is used to open via PIL since our facial recognition
										#require us to use PIL, e.g: /temp.jpg
	cv2.imwrite(tmpPath, img)
	
	gray_pil = Image.open(tmpPath).convert('L')
	gray = np.array(gray_pil, 'uint8')
	#faces = cascade.detectMultiScale(gray, 1.3, 5, minSize = (70, 70), flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
	faces = cascade.detectMultiScale(gray)
	output = None
	minConf = 100
	for (x, y, w, h) in faces:
		
		nbr_predicted, conf = re.predict(gray[y: y + h, x: x + w])
		#print nbr_predicted, conf
		if conf < minConf:
			output = nbr_predicted
			minConf = conf
	
	
	print output, minConf
	sys.stdout.flush()
	photoPath = "PATH TO STORE THE RESULT" #By default please set it as the /result folder
	filename = photoPath + str(index) + ".jpg"
	file = str(index) + ".jpg"
	cv2.imwrite(filename, img)
	index += 1
			
	sendEmail(filename, file, output, minConf, cur)
		
def sendEmail(path, file, label, conf, cur):
	global conn
	sql = "SELECT * FROM users WHERE id = " + "'" + str(label) + "'"
	cur.execute(sql)
	name = None
	for row in cur.fetchall():
		name = row[1]
	#store imagepath to database
	sql = "INSERT INTO history(photo, result, upload_date, confidence) VALUES(" + "'" + file + "','" + name + "','" + str(datetime.now()) + "','" + str(conf) +"')"
	cur.execute(sql)
	conn.commit()
	
	receivers = []
	sql = "SELECT * FROM users"
	cur.execute(sql)
	for row in cur.fetchall():
		receivers.append(row[3])
	sender = "PUT YOUR EMAIL ADDRESS HERE" #By default,we use gmail smtp 
	password = "PUT YOUR PASSWORD HERE"

	#emal msg
	COMMASPACE = ', '
	msg = MIMEMultipart()
	msg['Subject'] = "New Person dected" + str(datetime.now())
	msg['From'] = sender
	msg['To'] = COMMASPACE.join(receivers)

	fp = open(path, "rb")
	attachment = MIMEImage(fp.read())
	fp.close()		
	msg.attach(attachment)
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login(sender, password)
	server.sendmail(sender, receivers, msg.as_string())
	server.quit()
	
def connectToDB():
	host = "localhost"
	user = ""
	pwd = ""
	db = ""
	
	con = MySQLdb.connect(host, user, pwd, db)
	return con, con.cursor()
	
if __name__=="__main__":
	global conn
	conn, cur = connectToDB()
	recognizer = trainImage(cur)
	motionDetection(recognizer, cur)
	conn.close()
	#print "System exit"
	