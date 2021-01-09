import time
import numpy as np
import cv2
from laser import *

IDLE = -1
DETECT_BOX = 0
DETECT_LASER = 1

display_fps = False
state = IDLE

box = None
cap = cv2.VideoCapture(0)
time1 = time.time()

# phase 1: detecting rectangle
# phase 2: detecting dot and move mouse

# TODO:
# 1. (double for loop in paper) calibrate skew
# 2. keep detecting box to 3s, add a key to recalibrate
# 3. tie up with pyautogui for mouse input


past_boxes = []
coords = [] # all (x,y) coords on boundary
x_values = {} # x -> list(assoc y coords)
y_values = {} # y -> list(assoc x coords)

def detect_box(gray):
    # Get contours of rectangle from camera frame
    canny = cv2.Canny(gray, 110, 255)
    contours, hierarchy = cv2.findContours(
        canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    # algorithm to decide the box among contours
    contour = max(contours, key=cv2.contourArea)
    if contour is not None:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        past_boxes.append(box)

    # Show canny edge
    cv2.imshow("frame", canny)

def update_dict(gray):
    img = cv2.Canny(gray, 110, 255)
    contours, _ = cv2.findContours(
        canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )

    contour = max(contours, key=cv2.contourArea)
    if contour is not None:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        coords = np.int0(box)

    for coord in coords.ravel():
        x_values.setdefault(coord[0], []).append(coord[1])
        y_values.setdefault(coord[1], []).append(coord[0])

def get_x_values_for_row(row):
    lst = x_values[row]
    min_val = min(lst)
    max_val = max(lst)
    return (min, max)

def get_y_values_for_column(col):
    lst = y_values[col]
    min_val = min(lst)
    max_val = max(lst)
    return (min, max)

def get_laser_loc_blob(gray):
    print("blob")
    detector = cv2.SimpleBlobDetector_create()
    keypoints = detector.detect(gray)
    # Show blob
    # cv2.imshow("frame", res)
    im_with_keypoints = cv2.drawKeypoints(
        gray,
        keypoints,
        np.array([]),
        (0, 0, 255),
        cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
    )
    cv2.imshow("frame", im_with_keypoints)


def get_laser_loc(gray):
    pt = cv2.minMaxLoc(gray)
    print(pt)


def detect_laser(gray):
    print("detecting laser")
    laser_loc = get_laser_loc(gray)
    if outside_box(laser_loc):  # TODO: implement
        return
    else:
        move_mouse(laser_loc)  # TODO: implement


def most_frequent(lst):
    stringy_dict = {"".join(box.tolist()): box for box in past_boxes}
    return stringy_dict[max(set(stringy_dict.keys()), key=stringy_dict.keys().count)]


portXcoord, portYcoord = [], []


def get_line(p1, p2):
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    c = p1[1] - m * p1[0]
    return m, c


def calibrate_box(box):
    rd, ld, lu, ru = box
    width = max(ru[0], rd[0]) - min(lu[0], ld[0])
    height = max(ld[1], rd[1]) - min(lu[1], ru[1])  # FIXME: doesn't make sense
    portXcoord, portYcoord = np.zeros((width, height)), np.zeros((width, height))
    for x in range(width):  # NOTE: remember to account for paddings around
        for y in range(height):
            start_x, end_x = get_x_values_for_row(y)
            start_y, end_y = get_y_values_for_column(x)
            # FIXME: implement


while True:
    # Get camera frame
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    # to recalibrate
    if cv2.waitKey(1) & 0xFF == ord("r"):
        print("chg state")
        state = DETECT_BOX

    # read 100 frames, find the box.
    # TODO: retrigger this on a certain keystroke, check
    # if "r" works
    if state == DETECT_BOX:
        if len(past_boxes) > 50:
            # then can deduce box.
            # box is the one with most occurrences in past_boxes
            # flattened = np.array([box.flatten() for box in past_boxes])
            # print(flattened)
            # unique, counts = np.unique(flattened)
            # box = unique[np.argmax(counts)]
            # print()
            box = past_boxes[48]
            past_boxes = []
            calibrate_box(box)
            update_dict(gray)
            state = DETECT_LASER
        detect_box(gray)
    elif state == DETECT_LASER:
        detect_laser(gray)
    else:  # state = IDLE
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(
            gray, "Press r to start", (7, 70), font, 3, (0, 255, 0), 2, cv2.LINE_AA
        )
        cv2.imshow("frame", gray)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
