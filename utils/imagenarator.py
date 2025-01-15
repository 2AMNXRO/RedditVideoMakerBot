import os
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont
from rich.progress import track

from TTS.engine_wrapper import process_text
from utils.fonts import getheight, getsize

from utils import settings

import time

def draw_word_by_word_text(
    image, text, font, text_color, padding, wrap=50, transparent=False
) -> None:
    """
    Draw text one word at a time, centered on the image with a delay between each word
    """
    draw = ImageDraw.Draw(image)
    words = text.split()
    image_width, image_height = image.size

    # Calculate starting y position for centering text vertically
    total_text_width = sum([getsize(font, word)[0] for word in words])
    x_start = (image_width - total_text_width) / 2
    y_start = image_height / 2

    x = x_start
    for word in words:
        word_width, word_height = getsize(font, word)
        
        if transparent:
            shadowcolor = "black"
            for i in range(1, 5):
                draw.text(
                    (x - i, y_start - i),
                    word,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    (x + i, y_start - i),
                    word,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    (x - i, y_start + i),
                    word,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    (x + i, y_start + i),
                    word,
                    font=font,
                    fill=shadowcolor,
                )
        
        # Draw the word on the image
        draw.text((x, y_start), word, font=font, fill=text_color)

        # Update the x position for the next word
        x += word_width + padding

def draw_multiple_line_text(
    image, text, font, text_color, padding, wrap=50, transparent=False
) -> None:
    """
    Draw multiline text over given image
    """
    draw = ImageDraw.Draw(image)
    font_height = getheight(font, text)
    image_width, image_height = image.size
    lines = textwrap.wrap(text, width=wrap)
    y = (image_height / 2) - (((font_height + (len(lines) * padding) / len(lines)) * len(lines)) / 2)
    for line in lines:
        line_width, line_height = getsize(font, line)
        if transparent:
            shadowcolor = "black"
            for i in range(1, 5):
                draw.text(
                    ((image_width - line_width) / 2 - i, y - i),
                    line,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    ((image_width - line_width) / 2 + i, y - i),
                    line,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    ((image_width - line_width) / 2 - i, y + i),
                    line,
                    font=font,
                    fill=shadowcolor,
                )
                draw.text(
                    ((image_width - line_width) / 2 + i, y + i),
                    line,
                    font=font,
                    fill=shadowcolor,
                )
        draw.text(((image_width - line_width) / 2, y), line, font=font, fill=text_color)
        y += line_height + padding

def imagemaker(theme, reddit_obj: dict, txtclr, padding=8, transparent=False) -> None:

    one_word_mode = settings.config["settings"]["one_word"]
    storymode = settings.config["settings"]["storymode"]

    """
    Render Images for video 
    Args:
        theme (str): Background color for the image.
        reddit_obj (dict): Dictionary containing the Reddit thread post.
        txtclr (str): Text color for the captions.
        padding (int, optional): Padding between the text and the image borders. Defaults to 8.
        transparent (bool, optional): Whether to use a transparent background. Defaults to False.
        one_word_mode (bool, optional): Whether to create a new image for each word. Defaults to False.
    """
    texts = reddit_obj["thread_post"]

    id = re.sub(r"[^\w\s-]", "", reddit_obj["thread_id"])   

    if one_word_mode:
        if transparent:
            font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 150)
        else:
            font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 150)
    else:
        if transparent:
            font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 100)
        else:
            font = ImageFont.truetype(os.path.join("fonts", "Roboto-Regular.ttf"), 100)  

    size = (1920, 1080) 

    audio_idx = 0

    for idx, text in track(enumerate(texts), "Rendering Image"):
        text = process_text(text, False)  
        if storymode and one_word_mode:
            # One word per image mode
            words = text.split()
            for word_idx, word in enumerate(words):
                image = Image.new("RGBA", size, theme)
                draw_word_by_word_text(
                    image=image,  # Create a copy for each word
                    text=word,
                    font=font,
                    text_color=txtclr,
                    padding=padding,
                    transparent=transparent,
                )
                # Save the image with the pattern img{audio_idx}_{word_idx}.png
                image.save(f"assets/temp/{id}/png/img{audio_idx}_{word_idx}.png")
            audio_idx += 1
        else:
            # Multi-line text mode
            image = Image.new("RGBA", size, theme)
            draw_multiple_line_text(image, text, font, txtclr, padding, wrap=30, transparent=transparent)
            image.save(f"assets/temp/{id}/png/img{idx}.png")
