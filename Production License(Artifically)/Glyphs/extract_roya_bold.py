import os
from PIL import Image, ImageDraw, ImageFont

# Path to your font file
font_path = "../../Fonts/roya_bold.ttf"  # Adjust the path as needed
output_dir = "../../Glyphs"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the font
font_size = 600  # Desired height
font = ImageFont.truetype(font_path, font_size)

# Glyph to generate
glyph = '/'  # The character you want to create an image for

# Create a blank image with a transparent background
image = Image.new('RGBA', (font_size, font_size), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Calculate the bounding box of the text to center it
bbox = draw.textbbox((0, 0), glyph, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

text_x = (font_size - text_width) / 2
text_y = (font_size - text_height) / 2

# Draw the glyph on the image
draw.text((text_x, text_y), glyph, font=font, fill=(0, 0, 0, 255))  # Black color

# Use a safe filename for the slash character
filename = os.path.join(output_dir, f"_slash_.png")  # Use a safe filename

# Save the image
try:
    image.save(filename)
    print(f"Saved image as {filename}")
except Exception as e:
    print(f"Error saving {filename}: {e}")
