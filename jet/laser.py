import time
import numpy as np
import cv2
import matplotlib.pyplot as plt

# Read image
img = cv2.imread('laser_point.jpg')
scale_percent = 20 # percent of original size
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)
img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

# Get red from image
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
low_red = np.array([161, 155, 84])
high_red = np.array([179, 255, 255])
red_mask = cv2.inRange(hsv, low_red, high_red)
red = cv2.bitwise_and(img, img, mask=red_mask)

# Display red
cv2.imshow("img", red)
cv2.waitKey(0)
cv2.destroyAllWindows()
