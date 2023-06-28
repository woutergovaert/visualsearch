import cv2
import numpy as np
import extcolors
from skimage.color import rgb2lab, deltaE_cmc, deltaE_cie76, lab2rgb, rgb2hsv, hsv2rgb, deltaE_ciede2000, deltaE_ciede94
from PIL import Image
import random
from operator import itemgetter
import os
from dotenv import load_dotenv

load_dotenv('../.env')

output_folder = os.environ.get("INDEX_FOLDER")

class FeatureExtractor:
    def __init__(self, extract_type='cprimary', resize=300):
        self.resize_val = resize
        self.extract_type = extract_type

    def extract(self, img, bins=32, number_of_colors=10, tolerance=32, rgb=False):

        output_width = self.resize_val
        if img.size[0] >= self.resize_val:
            wpercent = (output_width/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            res_img = img.resize((output_width, hsize),
                                 Image.Resampling.LANCZOS)
        else:
            res_img = img

        colors_x = extcolors.extract_from_image(
            res_img, tolerance=tolerance, limit=number_of_colors)
        vector = [x[0] for x in colors_x[0]]
        if not rgb:
            vector = [np.asarray(color)/255 for color in vector]

            vector = [rgb2lab(color) for color in vector]

        return vector

    def get_feature(self, image_data: list, bins=32, number_of_colors=10, tolerance=32):
        self.image_data = image_data
        #fe = FeatureExtractor()
        features = []
        for img_path in self.image_data:  # Iterate through images
            # Extract Features

            feature = self.extract(img=Image.open(
                img_path), bins=bins, number_of_colors=number_of_colors, tolerance=tolerance)
            features.append(feature)
        return features


def match_image_by_color(image_colors_lab, color, threshold=60):
    selected_color = rgb2lab(np.asarray(color)/255)
    a = selected_color[1]
    b = selected_color[2]
    if a >= 0 and b >= 0:
        if abs(a) < abs(b):
            threshold = 5
        else:
            threshold = 10
        L_diff = 5
    elif a < 0 and b >= 0:
        if abs(a) < abs(b):
            threshold = 5
        else:
            threshold = 10
        L_diff = 5
    elif a < 0 and b < 0:
        if abs(a) < abs(b):
            threshold = 20
        else:
            threshold = 10
        L_diff = 10
    else:
        if abs(a) < abs(b):
            threshold = 15
            L_diff = 10
        else:
            threshold = 10
            L_diff = 5

    c_diff = 1000000
    c_matched = None
    c_indx = None
    select_image = False
    for i in range(min(len(image_colors_lab), 8)):
        curr_color = image_colors_lab[i]
        diff = deltaE_cmc(selected_color, curr_color)

        if (diff <= threshold):
            if abs(curr_color[0] - selected_color[0]) < L_diff:
                if c_diff > diff:
                    c_diff = diff
                    c_indx = i
                    c_matched = curr_color
                    select_image = True

    return select_image, c_diff, c_indx, c_matched


def match_image_by_color_filtering(image_colors_lab, color, threshold=60):
    selected_color = rgb2lab(np.asarray(color)/255)

    select_image = False
    for i in range(min(len(image_colors_lab), 2)):
        curr_color = image_colors_lab[i]
        diff = deltaE_cmc(selected_color, curr_color)

        if (diff <= threshold):
            select_image = True
            return select_image, diff, i, curr_color
        else:
            diff = 10000000

    return select_image, diff, i, curr_color


def show_selected_images_filtering(embeds, color, threshold=15, total_img=100):

    selected_img = []

    for key in embeds.keys():
        selected, difference, c_indx, matching_c = match_image_by_color_filtering(embeds[key],
                                                                                  color,
                                                                                  threshold)
        if (selected):

            selected_img.append([key, difference])

    sorted_result = sorted(selected_img, key=itemgetter(1))[:total_img]

    return [i for i, j in sorted_result]


def show_selected_images(embeds, color, threshold=15, total_img=100):

    selected_img_by_color_rank = {}
    selected_img = []
    for i in range(10):
        selected_img_by_color_rank[i] = []

    for key, lab_colors in embeds.items():
        selected, difference, c_indx, matching_c = match_image_by_color(lab_colors,
                                                                        color,
                                                                        threshold)
        if (selected):
            selected_img_by_color_rank[c_indx].append([key, difference])
            # selected_img.append([key, difference])
    for i in range(10):
        if len(selected_img_by_color_rank[i]) > 0:
            selected_img = selected_img + \
                sorted(selected_img_by_color_rank[i], key=itemgetter(1))[
                    :int((10-i)*np.round(total_img/20, 0))]
    print("selected len", len(selected_img))
    sorted_result = sorted(selected_img, key=itemgetter(1))[:total_img]
    print("sorted len", len(sorted_result))
    return [i for i, _ in sorted_result]


if __name__ == '__main__':
    import json
    import numpy as np
    with open(f'./server_setup/{output_folder}/color_embeds.json', "r") as openfile:
        hm = json.load(openfile)

    bonk = show_selected_images(list(hm.values()), [123, 8, 3], 15)
