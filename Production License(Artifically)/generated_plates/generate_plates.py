from PIL import Image
import os
import random
import numpy as np
import cv2
import imutils
import csv
import time
from tqdm import tqdm
from multiprocessing import Pool

numbers = [str(i) for i in range(0, 10)]
fonts = ['roya_bold']
templates = [os.path.basename(os.path.splitext(template)[0]) for template in os.listdir('../templates') if template.endswith('.png') and template not in ['tashrifat.png', '1.png', 'a.png']]
noises = os.listdir('../Noises')
transformations = ['rotate_right', 'rotate_left', 'zoom_in', 'zoom_out', 'prespective_transform']
glyph_cache = {}

permutations = 10

template_letter_restrictions = {
    'template-artesh': ['U'],
    'template-ommomi': ['E', 'K', 'T'],
    'template-base': ['A', 'B', 'C', 'D', 'H', 'J', 'L', 'M', 'N', 'O', 'Q', 'R', 'S', 'V', 'W', 'X', 'Y'],
    'template-defa': ['Z'],
    'template-Niromosalah': ['F'],
    'template-police': ['P'],
    'template-sepah': ['I']
}

white_text_templates = ['template-defa', 'template-Niromosalah', 'template-police', 'template-sepah']

def getPlateName(n1, n2, l, n3, n4, n5, n6, n7):
    return f'{n1}{n2}{l}{n3}{n4}{n5}{n6}{n7}'

def getGlyphAddress(font, glyphName, white=False):
    prefix = "processed_" if white else ""
    return f'../Glyphs/{font}/{prefix}{glyphName}_trim.png'

def getGlyphImage(font, glyph, white=False):
    glyph_path = getGlyphAddress(font, glyph, white)
    
    # Skip A_trim.png and W_trim.png
    if glyph in ["W"]:
        print(f"Skipping {glyph}_trim.png")
        return None
    
    try:
        glyph_image = Image.open(glyph_path).convert("RGBA")
    except FileNotFoundError:
        print(f"File not found: {glyph_path}")
        return None
    
    return glyph_image

def getNewPlate(letters, generated_plates, template):
    while True:
        plate = [random.choice(numbers[1:]), 
                 random.choice(numbers),
                 random.choice(template_letter_restrictions[template]),
                 random.choice(numbers), 
                 random.choice(numbers),
                 random.choice(numbers),
                 random.choice(numbers[1:]),
                 random.choice(numbers)]
        plate_name = getPlateName(*plate)
        if plate_name not in generated_plates:
            return plate

def applyNoise(plate):
    background = plate.convert("RGBA")
    noise = random.choice(noises)
    newPlate = Image.new('RGBA', (600,132), (0, 0, 0, 0))
    newPlate.paste(background, (0,0))
    noise = Image.open(os.path.join('../Noises/', noise)).convert("RGBA")
    newPlate.paste(noise, (0, 0), mask=noise)
    return newPlate

def applyTransforms(plate):
    plate = plate.resize((300,65), Image.Resampling.LANCZOS)
    plate = np.array(plate)
    transform = random.choice(transformations)
    
    if transform == 'rotate_right':
        result = imutils.rotate_bound(plate, random.randint(2,10))
    elif transform == 'rotate_left':
        result = imutils.rotate_bound(plate, random.randint(-10,-2))
    elif transform == 'zoom_in':
        height, width, _ = plate.shape
        randScale = random.uniform(1.1, 1.3)
        result = cv2.resize(plate, None, fx=randScale, fy=randScale, interpolation = cv2.INTER_CUBIC)
    elif transform == 'zoom_out':
        height, width, _ = plate.shape
        randScale = random.uniform(0.2, 0.6)
        result = cv2.resize(plate, None, fx=randScale, fy=randScale, interpolation = cv2.INTER_CUBIC)
    else:
        pts1 = np.float32([[0,0],[600,0],[0,132],[600,132]])
        pts2 = np.float32([[random.randint(0,30),random.randint(0,30)],
                           [random.randint(570,600),random.randint(0,30)],
                           [random.randint(0,30),random.randint(102,132)],
                           [random.randint(570,600),random.randint(102,132)]])
        M = cv2.getPerspectiveTransform(pts1,pts2)
        result = cv2.warpPerspective(plate,M,(600,132))
    
    return Image.fromarray(result)

def generate_plate(template, font):
    generated_plates = set()
    letters = []
    with open(f'../Fonts/{font}_namesMap.csv') as nameMapCsv:
        reader = csv.reader(nameMapCsv)
        next(reader)
        letters = [rows[1] for rows in reader if rows[1] != 'a' and not rows[1].isdigit()]

    use_white_text = template in white_text_templates

    for i in range(permutations):
        plate = getNewPlate(letters, generated_plates, template)
        plateName = getPlateName(*plate)
        generated_plates.add(plateName)

        glyphImages = []
        for glyph in plate:
            glyphImage = getGlyphImage(font, glyph, white=use_white_text)
            if glyphImage is not None:
                glyphImages.append(glyphImage)
            else:
                break
        
        if len(glyphImages) != 8:
            continue

        newPlate = Image.new('RGBA', (600,132), (0, 0, 0, 0))
        background = Image.open(f'../Templates/{template}.png').convert("RGBA")
        newPlate.paste(background, (0,0))

        left_rectangle_width = 448 - 67
        right_rectangle_width = 580 - 471

        total_width_left = sum(glyph.size[0] for glyph in glyphImages[:6])
        total_width_right = sum(glyph.size[0] for glyph in glyphImages[6:])

        scale_left = min(1, left_rectangle_width / total_width_left)
        scale_right = min(1, right_rectangle_width / total_width_right)

        x = 67
        for i, glyph in enumerate(glyphImages[:6]):
            new_width = int(glyph.size[0] * scale_left)
            new_height = int(glyph.size[1] * scale_left)
            resized_glyph = glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            y = 14 + (118 - 14 - new_height) // 2
            newPlate.paste(resized_glyph, (x, y), mask=resized_glyph)
            x += new_width
            if i < 5:
                x += int((left_rectangle_width - total_width_left * scale_left) // 5)

        x = 471
        for i, glyph in enumerate(glyphImages[6:]):
            new_width = int(glyph.size[0] * scale_right)
            new_height = int(glyph.size[1] * scale_right)
            resized_glyph = glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            y = 37 + (116 - 37 - new_height) // 2
            newPlate.paste(resized_glyph, (x, y), mask=resized_glyph)
            x += new_width
            if i == 0:
                x += int(right_rectangle_width - total_width_right * scale_right)

        noisyPlate = applyNoise(newPlate)
        transformedPlate = applyTransforms(noisyPlate)
        
        finalPlate = transformedPlate.resize((312,70), Image.Resampling.LANCZOS)
        finalPlate.save(f"{font}/{plateName}.png")

if __name__ == '__main__':
    pool = Pool()
    tasks = [(template, font) for template in templates for font in fonts]
    pool.starmap(generate_plate, tasks)
    pool.close()
    pool.join()