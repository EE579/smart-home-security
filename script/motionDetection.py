import cv2
import urllib 
import numpy as np
import sys

#url = "rtsp://group3:uscee579@68.181.131.153:88/videoSub"
url = "http://ip:port/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=xxx&pwd=xxx"
stream=urllib.urlopen(url)
bytes = ""

firstFrame = None
minArea = 20000
startX, startY = 260, 20
majorAxis, minorAxis = 180, 140
centerX, centerY = 400, 200

framenum = 0

def getFrame():
	global  bytes
	global framenum
	bytes += stream.read(1024)
	a = bytes.find('\xff\xd8')
	b = bytes.find('\xff\xd9')
	if a != -1 and b != -1:
		jpg = bytes[a:b+2]
		bytes= bytes[b+2:]
		img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
		framenum += 1
		return img
	else:
		return None

def motionDetection(img):
	global firstFrame
	#img = cv2.resize(frame, (800, 500))
	#img1 = img[startY : (startY + majorAxis * 2), startX : (startX + minorAxis * 2)]

	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)
	#roi = gray[startY : (startY + majorAxis * 2), startX : (startX + minorAxis * 2)]
	if firstFrame is None:
		firstFrame = gray
	else:
		delta = cv2.absdiff(firstFrame, gray)
		thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations = 2)
		(cnt, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		for c in cnt:
			if cv2.contourArea(c) < minArea:
				continue
			
			print "motion detected!"
			sys.stdout.flush()
			(x, y, w, h) = cv2.boundingRect(c)
			cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
	

	cv2.imshow("test", img)

if __name__ == "__main__":
	while True:
		frame = getFrame()
		if not frame is None and framenum > 3:
			motionDetection(frame)
			key = cv2.waitKey(1) & 0xFF
			if key == ord("q"):
				cv2.destroyAllWindows()
				exit(0)
