import time
import numpy as np
import cv2
from laser import *
import mouse

# import pyautogui

IDLE = -1
DETECT_BOX = 0
DETECT_LASER = 1

display_fps = False
state = IDLE

box = None
cap = cv2.VideoCapture(0)
time1 = time.time()
width, height = 0, 0
screenres = (1920, 1080)

# phase 1: detecting rectangle
# phase 2: detecting dot and move mouse

# TODO:
# 1. (double for loop in paper) calibrate skew
# 2. keep detecting box to 3s, add a key to recalibrate
# 3. tie up with pyautogui for mouse input


past_boxes = []


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


def get_laser_loc_raw(gray):
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    print(maxVal, maxLoc)
    if maxVal < 254:  # if too dark treat as no laser
        return np.array([-1, -1])
    else:  # return (x_perc, y_perc)
        matinv = np.linalg.pinv(mat)
        tmp = np.array([maxLoc[0], maxLoc[1], 1])
        return np.dot(matinv, tmp)[:2]


def outside_box(laser_loc):
    return laser_loc[0] < 0 or laser_loc[0] > 1 or laser_loc[0] < 0 or laser_loc[0] > 1


def move_mouse(laser_loc):
    x = int(laser_loc[0] * screenres[0])
    y = int(laser_loc[1] * screenres[1])
    mouse.move(x, y)


def detect_laser(gray):
    print("detecting laser")
    laser_loc_raw = get_laser_loc_raw(gray)
    laser_loc = np.divide(laser_loc_raw, np.array([width, height]))
    if outside_box(laser_loc):  # TODO: check if outside_box works as intended
        return
    else:
        move_mouse(laser_loc)  # TODO: implement


mat = []


def calibrate_box(box, img):
    box = np.float32(box)
    br, bl, tl, tr = box
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # maxHeight, maxWidth = maxWidth, maxHeight
    print("box", box)
    print(maxWidth, maxHeight)

    # dst = np.array(
    #     [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
    #     dtype="float32",
    # )
    dst = np.array(
        [[maxWidth - 1, maxHeight - 1], [0, maxHeight - 1], [0, 0], [maxWidth - 1, 0]],
        dtype="float32",
    )

    mat = cv2.getPerspectiveTransform(box, dst)
    warped = cv2.warpPerspective(img, mat, (maxWidth, maxHeight))
    cv2.imshow("frame", warped)
    cv2.imwrite("result.png", warped)
    global width, height
    width, height = maxWidth, maxHeight
    return mat


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
            mat = calibrate_box(box, gray)
            state = DETECT_LASER
            # cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
            # cap.set(cv2.CAP_PROP_EXPOSURE, -2.0)
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
