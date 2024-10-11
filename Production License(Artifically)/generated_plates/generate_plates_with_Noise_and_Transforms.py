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
templates = [os.path.basename(os.path.splitext(template)[0]) for template in os.listdir('../templates') if template.endswith('.png') and template not in ['1.png', 'a.png']]
noises = os.listdir('../Noises')
transformations = ['rotate_right', 'rotate_left', 'zoom_in', 'zoom_out', 'prespective_transform']
glyph_cache = {}

permutations = 5

template_letter_restrictions = {
    'template-artesh': ['U'],
    'template-ommomi': ['E', 'K', 'T'],
    'template-base': ['-', 'B', 'C', 'D', 'H', 'J', 'L', 'M', 'N', 'O', 'Q', 'R', 'S', 'V', 'W', 'X', 'Y'],
    'template-defa': ['Z'],
    'template-Niromosalah': ['F'],
    'template-police': ['P'],
    'template-sepah': ['I'],
    'template-service': ['&'],
    'template-diplomat': ['@'],
    'template-dolati': ['A'],
    'template-tashrifat': ['#'],
    'template-gozar': ['G']
}

white_text_templates = ['template-defa', 'template-Niromosalah', 'template-police', 'template-sepah', 'template-dolati', 'template-tashrifat']

def getPlateName(n1, n2, l, n3, n4, n5, n6, n7):
    return f'{n1}{n2}{l}{n3}{n4}{n5}{n6}{n7}'

def getTashrifatPlateName(l, n1, n2, n3, n4):
    return f'{l}{n1}{n2}{n3}{n4}'

def getGozarPlateName(n1, n2, l, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12):
    return f'{n1}{n2}{l}{n3}{n4}{n5}{n6}{n7}_{n8}{n9}{n10}{n11}{n12}'

def getGlyphAddress(font, glyphName, white=False):
    prefix = "processed_" if white else ""
    return f'../Glyphs/{font}/{prefix}{glyphName}_trim.png'

def getGlyphImage(font, glyph, white=False):
    glyph_path = getGlyphAddress(font, glyph, white)
    
    if glyph in ["*"]:
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
        if template == 'template-tashrifat':
            plate = [random.choice(template_letter_restrictions[template]),
                     random.choice(numbers[1:]),
                     random.choice(numbers),
                     random.choice(numbers),
                     random.choice(numbers)]
            plate_name = getTashrifatPlateName(*plate)
        elif template == 'template-gozar':
            n11 = random.choice(['0', '1'])
            n12 = random.choice(numbers) if n11 == '0' else random.choice(numbers[:3])
            plate = [random.choice(numbers[1:]), 
                     random.choice(numbers),
                     random.choice(template_letter_restrictions[template]),
                     random.choice(numbers), 
                     random.choice(numbers),
                     random.choice(numbers),
                     random.choice(numbers[1:]),
                     random.choice(numbers),
                     random.choice(numbers),
                     random.choice(numbers),
                     '$',
                     n11,
                     n12]
            plate_name = getGozarPlateName(*plate)
        else:
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
    plate = plate.resize((400,200), Image.Resampling.LANCZOS)
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
        if template == 'template-tashrifat':
            plateName = getTashrifatPlateName(*plate)
        elif template == 'template-gozar':
            plateName = getGozarPlateName(*plate)
        else:
            plateName = getPlateName(*plate)
        generated_plates.add(plateName)

        glyphImages = []
        for glyph in plate:
            glyphImage = getGlyphImage(font, glyph, white=use_white_text)
            if glyphImage is not None:
                glyphImages.append(glyphImage)
            else:
                break
        
        if (template == 'template-tashrifat' and len(glyphImages) != 5) or (template == 'template-gozar' and len(glyphImages) != 13) or (template not in ['template-tashrifat', 'template-gozar'] and len(glyphImages) != 8):
            continue

        newPlate = Image.new('RGBA', (600,132), (0, 0, 0, 0))
        background = Image.open(f'../Templates/{template}.png').convert("RGBA")
        newPlate.paste(background, (0,0))

        if template == 'template-tashrifat':
            left_rectangle_width = 339 - 66
            right_rectangle_width = 585 - 341

            letter_glyph = glyphImages[0]
            number_glyphs = glyphImages[1:]

            new_width = int(letter_glyph.size[0] * (left_rectangle_width / letter_glyph.size[0]))
            new_height = int(letter_glyph.size[1] * (left_rectangle_width / letter_glyph.size[0]))
            resized_letter = letter_glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            y = 10 + (119 - 10 - new_height) // 2
            newPlate.paste(resized_letter, (66, y), mask=resized_letter)

            total_width_right = sum(glyph.size[0] for glyph in number_glyphs)
            scale_right = min(1, right_rectangle_width / total_width_right)

            x = 341
            for i, glyph in enumerate(number_glyphs):
                new_width = int(glyph.size[0] * scale_right)
                new_height = int(glyph.size[1] * scale_right)
                resized_glyph = glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                y = 11 + (118 - 11 - new_height) // 2
                newPlate.paste(resized_glyph, (x, y), mask=resized_glyph)
                x += new_width
                if i < 3:
                    x += int((right_rectangle_width - total_width_right * scale_right) // 3)

        elif template == 'template-gozar':
            left_rectangle_width = 448 - 67
            right_rectangle_width = 567 - 484  # Updated to new dimensions
            bottom_rectangle_width = 583 - 469

            total_width_left = sum(glyph.size[0] for glyph in glyphImages[:6])
            total_width_right = sum(glyph.size[0] for glyph in glyphImages[6:8])
            total_width_bottom = sum(glyph.size[0] for glyph in glyphImages[8:])

            scale_left = min(1, left_rectangle_width / total_width_left)
            scale_right = min(1, right_rectangle_width / total_width_right)
            scale_bottom = min(1, bottom_rectangle_width / total_width_bottom)

            # Handle the main area (first 6 characters)
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

            # Handle n6 and n7 (top-right area)
            x_start = 484
            x_end = 567
            y_start = 17
            y_end = 54
            available_width = x_end - x_start
            available_height = y_end - y_start
            
            right_glyphs = glyphImages[6:8]
            total_width = sum(glyph.size[0] for glyph in right_glyphs)
            max_height = max(glyph.size[1] for glyph in right_glyphs)
            
            # Calculate scale to fit within 90% of the available space
            scale = min(0.9 * available_width / total_width, 0.9 * available_height / max_height)
            
            new_total_width = sum(int(glyph.size[0] * scale) for glyph in right_glyphs)
            new_max_height = int(max_height * scale)
            
            # Calculate starting positions to center the glyphs
            x = x_start + (available_width - new_total_width) // 2
            y = y_start + (available_height - new_max_height) // 2
            
            for glyph in right_glyphs:
                new_width = int(glyph.size[0] * scale)
                new_height = int(glyph.size[1] * scale)
                resized_glyph = glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                newPlate.paste(resized_glyph, (x, y), mask=resized_glyph)
                x += new_width

            # Handle the bottom area (remaining 5 characters)
            x = 469
            for i, glyph in enumerate(glyphImages[8:]):
                new_width = int(glyph.size[0] * scale_bottom)
                new_height = int(glyph.size[1] * scale_bottom)
                resized_glyph = glyph.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                y = 73 + (117 - 73 - new_height) // 2
                newPlate.paste(resized_glyph, (x, y), mask=resized_glyph)
                x += new_width
                if i < 4:
                    x += int((bottom_rectangle_width - total_width_bottom * scale_bottom) // 4)

        else:
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