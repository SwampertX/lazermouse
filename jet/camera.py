import time
import numpy as np
import cv2

display_fps = False


cap = cv2.VideoCapture(1)
time1 = time.time()

while(True):
    # Get camera frame
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('frame',gray)

    # Get contours of rectangle from camera frame
    ret, thresh = cv2.threshold(gray, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Get rotated bounding box of rectangle
    contour = max(contours, key=cv2.contourArea)
    if contour is not None:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        img = cv2.drawContours(gray, [box], -1, (0, 255, 0), 3)

    # Display FPS (around 30)
    if display_fps:
        time2 = time.time()
        fps = 1/(time2-time1)
        time1 = time2
        fps = str(int(fps))
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, fps, (7,70), font, 3, (0,255,0), 2, cv2.LINE_AA)

    # Show camera
    cv2.imshow('frame', img)

    # Quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()