from PIL import Image
import os
import random
import numpy as np
import cv2
import imutils
import csv
from tqdm import tqdm
from multiprocessing import Pool

numbers = [str(i) for i in range(0, 10)]
fonts = ['roya_bold']
templates = [os.path.basename(os.path.splitext(template)[0]) for template in os.listdir('../templates') if template.endswith('.png') and template not in ['tashrifat.png', '1.png', 'a.png']]
noises = os.listdir('../Noises')
glyph_cache = {}

permutations = 1000

template_letter_restrictions = {
    'template-artesh': ['U'],
    'template-ommomi': ['E', 'K', 'T'],
    'template-base': ['A', 'B', 'C', 'D', 'H', 'J', 'L', 'M', 'N', 'O', 'Q', 'R', 'S', 'V', 'W', 'X', 'Y', '-'],
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
    
    if glyph in ["A"]:
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

        newPlate = newPlate.resize((312, 70), Image.Resampling.LANCZOS)
        newPlate.save(f"{font}/{plateName}.png")

if __name__ == '__main__':
    pool = Pool()
    tasks = [(template, font) for template in templates for font in fonts]
    pool.starmap(generate_plate, tasks)
    pool.close()
    pool.join()
