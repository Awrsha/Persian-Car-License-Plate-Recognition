import os
from PIL import Image as PILImage
from tqdm import tqdm

# List of Fonts to look for extracted images of glyphs
fonts = ['roya_bold']

fontsProgBar = tqdm(total=len(fonts), desc='Fonts')
for font in fonts:
    print(font)
    # Getting list of old _trim images and delete them
    oldProcessedImages = [image for image in os.listdir(font) if image.endswith('_trim.png')]
    for image in oldProcessedImages:
        os.remove(os.path.join(font, image))
    
    # for each glyph image, remove the background and trim the image
    images = [image for image in os.listdir(font) if image.endswith('.png')]
    
    glyphProgBar = tqdm(total=len(images), desc='Glyphs', leave=False)
    for image in images:
        # Read the image
        glyphImage = PILImage.open(os.path.join(font, image)).convert("RGBA")
        # Remove the background
        data = glyphImage.getdata()
        newData = []
        for item in data:
            # Change all white (also shades of whites)
            # pixels to transparent
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                newData.append((255, 255, 255, 0))  # Change to transparent
            else:
                newData.append(item)
        glyphImage.putdata(newData)
        glyphImage = glyphImage.crop(glyphImage.getbbox())  # Trim the image

        # If glyph is a Number resize it to 87 pixel height(35 for zero).
        # otherwise 58 pixel height.
        if os.path.splitext(image)[0].isnumeric():
            if os.path.splitext(image)[0] == '0':
                glyphImage = glyphImage.resize((int(glyphImage.width * 35 / glyphImage.height), 35))
            else:
                glyphImage = glyphImage.resize((67, 70))
        else:
            glyphImage = glyphImage.resize((90, 70))
        
        glyphImage.save(os.path.join(font, f'{image.split(".")[0]}_trim.png'))

        glyphProgBar.update(1)
    glyphProgBar.close()
    fontsProgBar.update(1)
fontsProgBar.close()
