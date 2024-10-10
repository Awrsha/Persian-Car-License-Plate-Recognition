import cv2
import numpy as np
from PIL import Image

input_image_path = "/content/slash_trim.png"
img = cv2.imread(input_image_path)

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

img_rgba = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2RGBA)

lower_white = np.array([200, 200, 200, 255], dtype=np.uint8)
upper_white = np.array([255, 255, 255, 255], dtype=np.uint8)

mask = cv2.inRange(img_rgba, lower_white, upper_white)

img_rgba[mask == 255] = [0, 0, 0, 0]

output_image_path = "output_image.png"
result = Image.fromarray(img_rgba)
result.save(output_image_path)

print("Image saved with transparent background.")