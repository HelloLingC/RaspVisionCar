import cv2
# from picamera2 import Picamera2
import time

# Load the Haar cascade classifier for face detection
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Configure and start the camera
# picam2 = Picamera2()
# picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
# picam2.start()

print("Camera warming up...")
time.sleep(2.0)

cap = cv2.VideoCapture(1)

try:
    while True:
        # Capture frame from the camera
        # im = picam2.capture_array()
        ret, im = cap.read()
        if not ret:
            break
        
        # Convert to grayscale for the classifier
        grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_detector.detectMultiScale(grey, 1.1, 5)
        
        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
        # Display the output
        cv2.imshow("Camera", im)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cv2.destroyAllWindows()
    # picam2.stop()