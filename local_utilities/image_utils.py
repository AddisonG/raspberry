#!/usr/bin/env python3

import cv2
import imutils
import logging
from numpy import ndarray as np_image

def simplify_image(image: np_image,
                   width: int = None,
                   blur: bool = False,
                   greyscale: bool = False,
                   outline: bool = False,
                  ):
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
        image = cv2.GaussianBlur(image, (25, 25), 0)

    # Convert to outlines
    if outline:
        image = cv2.Canny(image, 50, 200)

    return image

def detect_motion(old_image: np_image, new_image: np_image, scale):
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
        logging.critical("Can only detect motion on greyscale images.")
        raise SystemExit("Can only detect motion on greyscale images.")

    # Find all areas that have changed from the original
    delta = cv2.absdiff(new_image, old_image)

    # Only keep areas that have changed by a significant value
    _, delta = cv2.threshold(delta, 30, 255, cv2.THRESH_BINARY)

    # Dilate just expands/bleeds/dilates shapes. This means a tiny circle would
    # grow in size. A donut shape might expand to a large circle (with no hole).
    # FIXME - https://www.geeksforgeeks.org/erosion-dilation-images-using-opencv-python/
    # FIXME - Please investigate using a kernel here instead of dozens of iterations
    delta = cv2.dilate(delta, None, iterations=int(scale * 1.5))

    cnts = cv2.findContours(delta, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    largest_motion = (0, 0, 0, 0)

    for c in cnts:
        # Ignore areas that are too small
        # FIXME - This should be adjusted for different resolutions? Don't hard-code!
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
