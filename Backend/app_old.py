from flask import Flask
from flask import request, url_for
from flask_cors import CORS
import os
import random
from PIL import Image
from flask import send_from_directory
import json
from CLIP import CLIP
from setup_func import compare
import torch
import requests
import uuid
import time
import numpy as np
from ExtColor import show_selected_images, FeatureExtractor, show_selected_images_filtering
from collections import deque
import ast
from dotenv import load_dotenv

load_dotenv('../.env')


model = CLIP()
color_model = FeatureExtractor()


path_data = os.environ.get("PATH_TO_IMAGES")
files = os.environ.get("INDEX_FOLDER")

with open(f"./server_setup/{files}/index.json", "r") as openfile:

    index = json.load(openfile)

with open(f"./server_setup/{files}/config.json", "r") as openfile:

    config = json.load(openfile)
    features = config['features']
    features.sort(key=lambda d: d['order'])

    tab_list = config['categories']

with open(f"./server_setup/{files}/embeds.json", "r") as openfile:

    img_embeds = json.load(openfile)


app = Flask(__name__)
CORS(app)


@app.route("/tabs", methods=["GET"])
def tabs():
    return {"tabs": tab_list}


@app.route("/random", methods=["POST"])
def get_random_imgs():

    tab = request.json["tab"]

    if tab == "Variety" or tab == "Custom":
        images = [img for img in os.listdir(path_data)]
        images = random.sample(images, 20)

        responses = []
        for image in images:
            responses.append(make_image_response(image))

        return responses
    else:
        text_embeds = model(text=[tab])

        best_idxs = compare(text_embeds, torch.tensor(
            list(img_embeds.values())), 60)

        responses = []
        for idx in best_idxs[0]:
            responses.append(make_image_response(index[str(idx.item())]))

        return random.sample(responses, 20)


@app.route("/random_all", methods=["GET"])
def get_random_img():

    final = []
    for tab in tab_list:

        if tab == "Brand Color":
            images = [img for img in os.listdir(path_data)]

            color = [138, 44, 32]

            images = find_similar_by_color(images, color)

            responses = []
            for image in images:
                responses.append(make_image_response(image))

            final.append({"feature": tab, "images": responses[:20]})
        elif tab == "Variety":
            images = [img for img in os.listdir(path_data)]
            images = random.sample(images, 50)

            responses = []
            for image in images:
                responses.append(make_image_response(image))

            final.append({"feature": tab, "images": responses[:20]})
        else:
            text_embeds = model(text=[tab])

            best_idxs = compare(
                text_embeds, torch.tensor(list(img_embeds.values())), 20
            )

            responses = []
            for idx in best_idxs[0]:
                responses.append(make_image_response(index[str(idx.item())]))
            #responses = random.sample(responses, 20)
            final.append({"feature": tab, "images": responses})
    return final


@app.route("/images/<path>")
def images(path):
    return send_from_directory(path_data, path)


@app.route("/get_similar", methods=["POST"])
def get_similar():

    img = request.json["img"]
    img = img.split("/")[-1]

    responses = []
    for image in img_idxs[img]:
        responses.append(make_image_response(image))

    return responses


@app.route("/search", methods=["POST"])
def search(n_res=30):

    txt = request.json["txt"]
    text_embeds = model(text=[txt])
    history = request.json['history']
    stack = deque(history, maxlen=3)
    best_idxs = compare(text_embeds, torch.tensor(
        list(img_embeds.values())), n_res)

    responses = []
    for idx in best_idxs[0]:
        responses.append(make_image_response(index[str(idx.item())]))
    stack.appendleft([responses, 'gallery'])
    return {'images': responses, 'history': list(stack)}


def make_image_response(image):

    response = {}
    response["src"] = url_for("images", path=image, _external=True)
    img = Image.open(os.path.join(path_data, image))
    response["width"] = img.width
    response["height"] = img.height

    return response


@app.route("/get_similar_all", methods=["POST"])
def get_similar_all():

    img = request.json["img"]
    print('im here')
    img = img.split("/")[-1]
    px = request.json['px']
    click = request.json['click']
    history = request.json['history']

    stack = deque(history, maxlen=3)
    data = Image.open(path_data+img)
    wd = int(round(data.width * click[0]))
    ht = int(round(data.height * click[1]))

    area = np.asarray(data)[ht-px:ht+px, wd-px:wd+px, :]
    # area = cv2.cvtColor(area, cv2.COLOR_BGR2RGB)
    # cv2.imshow("image", area)
    # cv2.waitKey(0)
    selected_color = list(color_model.extract(
        Image.fromarray(area), rgb=True)[0])
    # selected_color = list(np.mean(area, axis=(0, 1)).astype(int))
    final = []
    for feat in features:
        responses = []
        if feat['feature'] == 'SimilarityMatrix':

            with open(feat["file"], "r") as openfile:
                img_idxs = json.load(openfile)
            try:
                for image in img_idxs[img]:

                    responses.append(make_image_response(image))

                final.append(
                    {"feature": feat["name"], "images": responses, "type": 'similarity', 'order': feat['order']})

            except:
                continue

        elif feat['feature'] == 'Tagging':
            with open(feat["index"], "r") as openfile:
                img_idxs = json.load(openfile)
            if "tags" in feat:
                tags = [img_idxs[img][i] for i in feat['tags']]
            else:
                if "default" in feat:
                    tags = [img_idxs[img][i] for i in feat['default']]
                    all_tags = img_idxs[img]
                else:
                    tags = random.sample(img_idxs[img], int(feat['n_tags']))
            img_idxs = None
            with open(feat["inverse_index"], "r") as openfile:
                tag_index = json.load(openfile)
            inter = set(tag_index[tags[0]])
            for tag in tags[1:]:
                inter = inter.intersection(tag_index[tag])
            for image in random.sample(inter, min(20, len(inter))):
                responses.append(make_image_response(image))
            if "default" in feat:
                final.append(
                    {"feature": feat["name"], "images": responses, "type": 'tagging_choice', 'tags': all_tags, 'order': feat['order']})
            else:
                final.append(
                    {"feature": feat["name"]+' ('+', '.join(tags)+')', "images": responses, "type": 'tagging', 'tags': tags, 'order': feat['order']})

        elif feat['feature'] == 'Color':
            with open(feat['file'], "r") as openfile:
                color_embeds = json.load(openfile)
            imgs = show_selected_images_filtering(
                color_embeds, selected_color)

            #imgs = random.sample(imgs, min(20, len(imgs)))

            for image in imgs:
                responses.append(make_image_response(image))
            selected_color = f'rgb({selected_color[0]},{selected_color[1]},{selected_color[2]})'
            final.append(
                {"feature": feat['name'], "images": responses, 'type': 'color', 'color': selected_color, 'order': feat['order']})

    stack.appendleft([final, 'rows'])

    return {'final': final, 'history': list(stack)}


@app.route("/get_similar_from_search", methods=["POST"])
def get_similar_from_search():

    img = request.json["img"]
    img = img.split("/")[-1]
    history = request.json['history']

    stack = deque(history, maxlen=3)
    final = []
    for feat in features:
        responses = []
        if feat['feature'] == 'SimilarityMatrix':
            with open(feat["file"], "r") as openfile:
                img_idxs = json.load(openfile)
            try:
                for image in img_idxs[img]:

                    responses.append(make_image_response(image))

                final.append(
                    {"feature": feat["name"], "images": responses, "type": 'similarity', 'order': feat['order']})

            except:
                continue
        elif feat['feature'] == 'Tagging':
            with open(feat["index"], "r") as openfile:
                img_idxs = json.load(openfile)

            if "tags" in feat:
                tags = [img_idxs[img][i] for i in feat['tags']]
            else:
                if "default" in feat:
                    tags = [img_idxs[img][i] for i in feat['default']]
                    all_tags = img_idxs[img]
                else:
                    tags = random.sample(img_idxs[img], int(feat['n_tags']))
            img_idxs = None
            print('1.5')
            with open(feat["inverse_index"], "r") as openfile:
                tag_index = json.load(openfile)

            inter = set(tag_index[tags[0]])
            for tag in tags[1:]:
                inter = inter.intersection(tag_index[tag])
            for image in random.sample(inter, min(20, len(inter))):
                responses.append(make_image_response(image))
            print('2')
            if "default" in feat:
                final.append(
                    {"feature": feat["name"], "images": responses, "type": 'tagging_choice', 'tags': all_tags, 'order': feat['order']})
            else:
                final.append(
                    {"feature": feat["name"]+' ('+', '.join(tags)+')', "images": responses, "type": 'tagging', 'tags': tags, 'order': feat['order']})

    stack.appendleft([final, 'gallery'])
    return {'final': final, 'history': list(stack)}


@app.route("/call_api", methods=["POST"])
def call_api():

    req = request.json
    url = "https://ai-content-tagging.staging.m-operations.com/api/v1/one-sync"
    headers = {
        "Authorization": "token",
        "Content-Type": "application/json",
    }
    tenID = str(uuid.uuid4())
    conID = str(uuid.uuid4())
    body = {
        "TenantId": tenID,
        "ContentId": conID,
        "SourceSystem": "Anthony",
        "ContentType": "image",
        "ContentUrl": req["url"],
        "Methods": req["methods"],
    }
    start = time.time()
    res = requests.post(url, json=body, headers=headers)
    res = res.json()
    print(res)
    final = {
        "ImageTagging": [],
        "ImageDescription": "",
        "OCR": "",
        "Custom": [],
        "ObjectDetection": [],
        "similar": [],
    }
    for method in req["methods"]:
        if method == "ImageTagging":
            final[method] = ", ".join(
                [tag["name"] for tag in res["ImageTagging"]["Tags"]][:5]
            )
        elif method == "ImageDescription":
            final[method] = res["ImageDescription"]["Tags"][0]["captions"][0]["text"]
        elif method == "Custom":
            final[method] = ", ".join([tag["name"]
                                      for tag in res["Custom"]["Tags"]][:5])
        elif method == "OCR":
            final[method] = ", ".join(res["OCR"]["Tags"][:5])
    # tag = frozenset(final['ImageTagging'][:2])
    # responses = []
    # for image in tag_idx[tag]:
    #     responses.append(make_image_response(image))
    # final['similar']= responses
    return final


@app.route("/filter_color", methods=["POST"])
def filter_color():
    history = request.json['history']
    color = request.json['color']
    row = request.json['row']
    # id = request.json['id']
    # methods = request.json['methods']
    # for i in range(len(features)):
    #     if features[i]['order'] == id:
    #         id = i
    #         break
    # if methods == []:
    #     # tags = request.json['history'][0][row]['tags']
    #     inter = [img for img in os.listdir(path_data)]
    # else:
    #     tags = methods

    #     with open(features[id]["inverse_index"], "r") as openfile:

    #         tag_index = json.load(openfile)
    #     inter = set(tag_index[tags[0]])
    #     for tag in tags[1:]:
    #         inter = inter.intersection(tag_index[tag])
    inter = [img for img in os.listdir(path_data)]
    color = list(ast.literal_eval(color[3:]))

    imgs = find_similar_by_color(inter, color)

    responses = []
    for image in imgs:
        responses.append(make_image_response(image))
    random.shuffle(responses)
    if len(history) > 2:
        history[0]['images'] = responses
        return history
    history[0][row]['images'] = responses
    return history


def find_similar_by_color(images, color):
    with open(f"./server_setup/{files}/color_embeds.json", "r") as openfile:
        color_embeds = json.load(openfile)
        color_embeds = {img: color_embeds[img] for img in images}
    imgs = show_selected_images_filtering(
        color_embeds, color)
    return imgs


@app.route("/select_tags", methods=["POST"])
def select_tags():
    history = request.json['history']
    tags = request.json['tags']
    row = request.json['row']

    with open(features[row]["inverse_index"], "r") as openfile:
        tag_index = json.load(openfile)
    inter = set(tag_index[tags[0]])
    for tag in tags[1:]:
        inter = inter.intersection(tag_index[tag])
    responses = []
    for image in random.sample(inter, min(20, len(inter))):
        responses.append(make_image_response(image))
    history[0][row]['images'] = responses
    return history


if __name__ == "__main__":
    app.run(port=5020)
