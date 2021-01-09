import time
import numpy as np
import cv2
from laser import *

IDLE = -1
DETECT_BOX = 0
DETECT_LASER = 1

display_fps = False
state = DETECT_BOX

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
coords = []  # all (x,y) coords on boundary
x_values = {}  # x -> list(assoc y coords)
y_values = {}  # y -> list(assoc x coords)


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
    contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    contour = max(contours, key=cv2.contourArea)
    coords = contour
    if contour is not None:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
    # for pt in box:
    #     cv2.drawMarker(gray, tuple(pt.tolist()), (0, 0, 255))

    # print("coords")
    # print(coords)
    # for coord in coords.ravel():
    #     x_values.setdefault(coord[0], []).append(coord[1])
    #     y_values.setdefault(coord[1], []).append(coord[0])
    # debug
    for coord in coords:
        # cv2.circle(gray, tuple(coord.tolist()[0]), 0, (0, 0, 255), thickness=-1)
        print(gray[coord.tolist()[0][0]][coord.tolist()[0][1]])
        gray[coord.tolist()[0][0]][coord.tolist()[0][1]] = 255
    cv2.imshow("frame", gray)
    cv2.imwrite("result.png", gray)
    time.sleep(10)


# min_x, min_y define the padding for the bounding box.
def get_x_values_for_row(y, lline, rline, x_padding):
    min_val = (y - lline[1]) / lline[0]  # x = (y - c)/m
    max_val = (y - rline[1]) / rline[0]  # x = (y - c)/m
    return x_padding + min_val, x_padding + max_val


def get_y_values_for_column(x, uline, dline, y_padding):
    min_val = dline[0] * x + dline[1]  # y = mx + c
    max_val = uline[0] * x + uline[1]  # y = mx + c
    return y_padding + min_val, y_padding + max_val


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


def outside_box(laser_loc):
    pass  # FIXME


def move_mouse(laser_loc):
    pass  # FIXME


def detect_laser(gray):
    print("detecting laser")
    laser_loc = get_laser_loc(gray)
    if outside_box(laser_loc):  # TODO: implement
        return
    else:
        move_mouse(laser_loc)  # TODO: implement


portXcoord, portYcoord = [], []


def get_line(p1, p2):
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    c = p1[1] - m * p1[0]
    return (m, c)


def calibrate_box(box):
    rd, ld, lu, ru = box
    max_x, min_x = max(ru[0], rd[0]), min(lu[0], ld[0])
    max_y, min_y = max(ld[1], rd[1]), min(lu[1], ru[1])
    print("maxmin")
    print(max_x, max_y, min_x, min_y)
    width = max_x - min_x
    height = max_y - min_y
    portXcoord, portYcoord = np.zeros((height, width)), np.zeros((height, width))
    lline, rline = get_line(ld, lu), get_line(ld, lu)
    uline, dline = get_line(lu, ru), get_line(ld, rd)
    print("lines")
    print(lline, rline, uline, dline)
    for x in range(width):  # FIXME: remember to account for paddings around
        for y in range(height):
            start_x, end_x = get_x_values_for_row(y + min_y, lline, rline, min_x)
            start_y, end_y = get_y_values_for_column(x + min_x, uline, dline, min_y)
            # print("pts in cross")
            # print(start_x, end_x, start_y, end_y)
            yperc = (y + min_y - start_y) / (end_y - start_y)
            xperc = (x + min_x - start_x) / (end_x - start_x)
            portXcoord[y][x] = xperc
            portYcoord[y][x] = yperc


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
            # update_dict(gray)
            calibrate_box(box)
            print(portXcoord, portYcoord)
            state = DETECT_LASER
        detect_box(gray)
    elif state == DETECT_LASER:
        break  # FIXME
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
