#!/usr/bin/env python3

import cv2
import imutils

def simplify_image(image,
                   width: int = None,
                   blur: bool = False,
                   greyscale: bool = False,
                   outline: bool = False,
                  ):
    """
    Simplify an image, by shrinking, blurring, greyscaling, outlining
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

def detect_motion(old_image, new_image):
    """
    Compare two images. If there is motion, it will return a box around the
    largest area that had motion.

    All credit goes to this fantastic article.
    https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    """
    if old_image is None:
        return (0, 0, 0, 0)

    # FIXME - Debugging only
    print_image = new_image.copy()

    new_simple = simplify_image(new_image, greyscale=True, blur=True)
    old_simple = simplify_image(old_image, greyscale=True, blur=True)

    # Find all areas that have changed from the original
    delta = cv2.absdiff(new_simple, old_simple)

    # Only keep areas that have changed by a significant value
    _, delta = cv2.threshold(delta, 30, 255, cv2.THRESH_BINARY)

    # Dilate just expands/bleeds/dilates the edges of shapes. This means a tiny
    # dot would grow in size. A donut might become a large circle (with no hole).
    delta = cv2.dilate(delta, None, iterations=15)

    # FIXME - copy is slow. just for debugging? Dunno why the code online had it?
    cnts = cv2.findContours(delta.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    largest_motion = (0, 0, 0, 0)

    for c in cnts:
        area = cv2.contourArea(c)
        # Ignore areas that are too small
        # FIXME - This should be adjusted for different resolutions? Don't hard-code!
        if area < 2000:
            continue

        (x, y, w, h) = cv2.boundingRect(c)
        # cv2.putText(print_image, str(area), (x, max(y - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Find out if the movement was larger than another on this image
        if w * h > largest_motion[2] * largest_motion[3]:
            largest_motion = (x, y, w, h)

    # Only print the biggest move
    (x, y, w, h) = largest_motion
    cv2.rectangle(print_image, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # FIXME - Debugging only
    show_image(print_image, "Motion Visualisation")

    return largest_motion

def show_image(image, title: str = "image"):
    # Show the
    cv2.imshow(title, image)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        raise Exception("User pressed 'q', exiting.")
