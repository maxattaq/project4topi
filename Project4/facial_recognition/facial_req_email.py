#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
import requests
from datetime import datetime


all_students = ["Max", "Bob", "Charlie", "David", "Eve"]
detected_students = set()
#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"
#use this xml file
cascade = "haarcascade_frontalface_default.xml"

#function for setting up emails
def send_message(name):
    return requests.post(
        "https://api.mailgun.net/v3/sandboxe4eab8d3a6684aa59b45743f5af22006.mailgun.org/messages",
        auth=("api", "api here"),
        files = [("attachment", ("image.jpg", open("image.jpg", "rb").read()))],
        data={"from": 'email here',
            "to": ["email here"],
            "subject": "A Student Has Been Marked Present",
            "html": "<html>" + name + " is in class.  </html>"})

def send_attendance_email(present_students, absent_students):
    present_list = ", ".join(present_students)
    absent_list = ", ".join(absent_students)
    attendance_summary = f"""
        <html>
        <body>
            <h2>Attendance Summary</h2>
            <p><strong>Present:</strong> {present_list}</p>
            <p><strong>Absent:</strong> {absent_list}</p>
        </body>
        </html>
    """
    return requests.post(
        "https://api.mailgun.net/v3/sandboxe4eab8d3a6684aa59b45743f5af22006.mailgun.org/messages",
        auth=("api", "api here"),
        data={
            "from": 'email here',
            "to": ["email here"],
            "subject": "Class Attendance Report",
            "html": attendance_summary
        }
    )




# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
detector = cv2.CascadeClassifier(cascade)

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
# vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

# loop over frames from the video file stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to 500px (to speedup processing)
	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	
	# convert the input frame from (1) BGR to grayscale (for face
	# detection) and (2) from BGR to RGB (for face recognition)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

	# detect faces in the grayscale frame
	rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
		minNeighbors=5, minSize=(30, 30),
		flags=cv2.CASCADE_SCALE_IMAGE)

	# OpenCV returns bounding box coordinates in (x, y, w, h) order
	# but we need them in (top, right, bottom, left) order, so we
	# need to do a bit of reordering
	boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

	# compute the facial embeddings for each face bounding box
	encodings = face_recognition.face_encodings(rgb, boxes)
	names = []

	# loop over the facial embeddings
	for encoding in encodings:
		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown"

		# check to see if we have found a match
		if True in matches:
			# find the indexes of all matched faces then initialize a
			# dictionary to count the total number of times each face
			# was matched
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}

			# loop over the matched indexes and maintain a count for
			# each recognized face face
			for i in matchedIdxs:
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1
			detected_students.add(name)
			# determine the recognized face with the largest number
			# of votes (note: in the event of an unlikely tie Python
			# will select first entry in the dictionary)
			name = max(counts, key=counts.get)
			
			#If someone in your dataset is identified, print their name on the screen
			if currentname != name:
				currentname = name
				print(currentname)
				#Take a picture to send in the email
				img_name = "image.jpg"
				cv2.imwrite(img_name, frame)
				print('Taking a picture.')
				
				#Now send me an email to let me know who is at the door
				request = send_message(name)
				print ('Status Code: '+format(request.status_code)) #200 status code means email sent successfully
				
		# update the list of names
		names.append(name)

	# loop over the recognized faces
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# draw the predicted face name on the image - color is in BGR
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 225), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			.8, (0, 255, 255), 2)

	# display the image to our screen
	cv2.imshow("Facial Recognition is Running", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		#date + attendance
		# add attendance and date functionality the program should create a file similar to attendance_input.txt
		# add emailing of the list of student names that were present and absent
		# add printing of the precent of students that attended the class
		# Save attendance to file
		current_date = datetime.now().strftime("%Y-%m-%d")
		with open("attendance_input.txt", "w") as file:
			file.write(f"{current_date}\n")
			for student in all_students:
				presence = 1 if student in detected_students else 0
				file.write(f"{student}: {presence}\n")

		# Email attendance summary
		present_students = [s for s in all_students if s in detected_students]
		absent_students = [s for s in all_students if s not in detected_students]
		send_attendance_email(present_students, absent_students)

		# Print attendance percentage
		total_students = len(all_students)
		attendance_percentage = (len(present_students) / total_students) * 100
		print(f"Attendance Percentage: {attendance_percentage:.2f}%")
		print("Attendance saved to attendance_input.txt")


		break

	# update the FPS counter
	fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
