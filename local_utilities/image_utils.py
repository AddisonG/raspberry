#!/usr/bin/env python3

import cv2
import imutils
from numpy import ndarray as np_image, array, uint8

circle = array([
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
], dtype=uint8)

def simplify_image(image: np_image,
                   width: int = None,
                   blur: bool = False,
                   greyscale: bool = False,
                   outline: bool = False,
                  ) -> np_image:
    """
    Simplify an image, by shrinking, blurring, greyscaling, outlining.
    """
    # Shrink the image
    if width is not None:
        image = imutils.resize(image, width=width)

    # Convert to greyscale
    if greyscale:
        conversion = cv2.COLOR_BGR2GRAY  # cv2.IMREAD_GRAYSCALE
        image = cv2.cvtColor(image, conversion)

    # Blur the image
    if blur:
        # FIXME - Maybe base this on scale? Maybe not.
        image = cv2.GaussianBlur(image, (25, 25), 0)

    # Convert to outlines
    if outline:
        image = cv2.Canny(image, 50, 200)

    return image

def is_greyscale(image: np_image) -> bool:
    """
    Sample every 100th pixel in each row and column of the image.
    If they're all grey, then the image is probably greyscale.
    """
    if len(image.shape) == 2:
        # Only height and width dimensions (no color dimension)
        return True

    height, width = image.shape[:2]

    for col in range(0, width, 100):  # e.g: 1920
        for row in range(0, height, 100):  # e.g: 1080
            pixel = image[row][col]
            # The RGB values must all be identical, or the pixel is non-grey
            if not pixel[0] == pixel[1] == pixel[2]:
                return False

    return True

def detect_motion(old_image: np_image, new_image: np_image, scale: float, sensitive: bool):
    """
    Compare two images. If there is motion, it will return a box around the
    largest area that had motion.

    The images to be compared MUST be binary images (greyscale).

    All credit goes to this fantastic article.
    https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    """
    if old_image is None or new_image is None:
        return (0, 0, 0, 0)

    if len(new_image.shape) >= 3:
        raise SystemExit("Can only detect motion on greyscale images.")

    # Find all areas that have changed from the original
    delta = cv2.absdiff(new_image, old_image)

    # Only keep areas that have changed by a significant value
    sensitity = 15 if sensitive else 40
    _, delta = cv2.threshold(delta, sensitity, 255, cv2.THRESH_BINARY)

    # Dilate just expands/bleeds/dilates shapes. This means a tiny circle would
    # grow in size. A donut shape might expand to a large circle (with no hole).
    # FIXME - https://www.geeksforgeeks.org/erosion-dilation-images-using-opencv-python/

    delta = cv2.dilate(delta, circle, iterations=int(scale * 1.5))

    cnts = cv2.findContours(delta, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    largest_motion = (0, 0, 0, 0)

    for c in cnts:
        # Ignore areas that are too small
        area = cv2.contourArea(c)
        if area < (200 * scale):
            continue

        (x, y, w, h) = cv2.boundingRect(c)

        # Find out if the movement was larger than another on this image
        if w * h > largest_motion[2] * largest_motion[3]:
            largest_motion = (x, y, w, h)

    return largest_motion

def show_image(image: np_image, title: str = "image"):
    # Show the image in a window, for debugging or visualisation purposes.
    cv2.imshow(title, image)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        raise SystemExit("User pressed 'q', exiting.")
