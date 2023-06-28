import os
import json
import cv2 as cv
from CLIP import CLIP
from torch import matmul, topk, cat
import torch
import numpy as np
from PIL import Image
from ResNet101 import FeatureExtractor as TextureExtractor
from ExtColor import FeatureExtractor
#from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import requests
import time
import face_recognition
from dotenv import load_dotenv

load_dotenv('../.env')

data = os.environ.get("PATH_TO_IMAGES")
output_folder = os.environ.get("INDEX_FOLDER")


def load_images_from_azure(conn_str):
    client = BlobServiceClient.from_connection_string(conn_str=conn_str)

    images = []
    for cont in client.list_containers():
        contain = client.get_container_client(container=cont['name'])

        for blob in contain.list_blob_names():
            blob = contain.get_blob_client(blob=blob)
            images.append(blob.url)

    return images


def call_tagging_api(urls, token, tenantId='tid'):
    url = "https://ai-content-tagging.staging.m-operations.com/api/v1/many"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    body = {
        "TenantId": tenantId,
        "SourceSystem": "Visual Search",
        "ContentType": "image",
        "Content": [{'Id': i.split('/')[-1].split('.')[-2], "Url":i} for i in urls]
    }

    i = 0
    while i < len(urls):
        res = requests.post(url, json=body, headers=headers)
        time.sleep(1)
        i += 4


def get_results_from_api(urls, token, tenantId='tid'):
    url = "https://ai-content-tagging.staging.m-operations.com/api/v1/get-many"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json", }

    body = {
        "TenantId": tenantId,
        "SourceSystem": "Visual Search",
        "ContentType": "image",
        "Methods": ["ImageTagging", "Custom"],
        "Content":
            [{'Id': i.split('/')[-1].split('.')[-2], "Url":i} for i in urls]

    }
    res = requests.post(url, json=body, headers=headers)
    return res.json()


def get_tags(urls):
    i = 0
    final_tags = {}
    final_custom = {}
    while i < len(urls):
        res = get_results_from_api(urls[i:i+4])
        time.sleep(1)
        for cont in res['Content']:

            final_tags[cont['ContentId']] = [tag['name']
                                             for tag in cont['ImageTagging'][0]['Tags']]
            final_custom[cont['ContentId']] = cont['Custom'][0]['Tags']
        i += 4

    with open(f"./server_setup/{output_folder}/tags.json", "w") as openfile:
        hm = json.dump(final_tags, openfile)
    with open(f"./server_setup/{output_folder}/custom_tags.json", "w") as openfile:
        hm = json.dump(final_custom, openfile)


def load_images(path):

    images = [(os.path.join(path, img)) for img in os.listdir(path)]

    return images


def make_image_index(path, output_path):

    dict = {i: img for i, img in enumerate(os.listdir(path))}

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


@torch.no_grad()
def make_sim_matrix(batch_size, path, path_to_idx, output_path, threshold=1.1):

    embeds = make_img_embeds(batch_size, path)

    best_idxs = compare(embeds, embeds, 20, threshold=threshold)

    dict = {}
    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    for i, top in enumerate(best_idxs):
        dict[img_idxs[str(i)]] = [img_idxs[str(j)] for j in top.tolist()]

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


def compare(text_embeds, img_embeds, n_res=20, threshold=1):

    sim_matrix = matmul(text_embeds, img_embeds.t())
    idx = sim_matrix >= threshold
    sim_matrix = sim_matrix.masked_fill(idx, -1)
    best_idxs = topk(
        sim_matrix,
        n_res,
    ).indices

    return best_idxs


@torch.no_grad()
def make_img_embeds(batch_size, path):
    images = load_images(path)
    model = CLIP()

    embeds = []
    i = 0
    while i < len(images):
        embed = model(images=images[i: i + batch_size])

        i += batch_size
        embeds.append(embed)
    images = None
    embeds = cat(embeds)

    return embeds


def save_embeds(batch_size, path, path_to_idx, output_path):

    embeds = make_img_embeds(batch_size, path)

    dict = {}
    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    for i, embed in enumerate(embeds):
        dict[img_idxs[str(i)]] = embed.tolist()

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


def make_tag_index(model, batch_size, path, path_to_idx, output_path, class_list):
    images = load_images(path)

    tags = []
    i = 0
    while i < len(images):
        tag = model(images=images[i: i + batch_size])

        i += batch_size
        tags.append(tag)
    images = None
    tags = cat(tags)

    tags = topk(tags, 5).indices.tolist()

    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    final = {class_list[i]: [] for i in range(len(class_list))}
    for i in range(len(tags)):
        for j in tags[i]:
            final[class_list[tags[i][j]]] += [img_idxs[i]]

    with open(output_path, "w") as outfile:
        json.dump(final, outfile)


def inverse_tag_index(path, output_path):
    with open(path, 'r') as openfile:
        index = json.load(openfile)

    final = {}
    for img in index:
        for tag in index[img]:
            final[tag] = final.get(tag, [])+[img]

    with open(output_path, 'w') as outfile:
        json.dump(final, outfile)


def make_texture_matrix(path, path_to_idx, output_path, threshold=1.1):

    images = load_images(path)

    model = TextureExtractor()
    embeds = model.get_feature(images)

    embeds = torch.from_numpy(embeds)
    best_idxs = compare(embeds, embeds, 20, threshold=threshold)

    dict = {}
    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    for i, top in enumerate(best_idxs):
        dict[img_idxs[str(i)]] = [img_idxs[str(j)] for j in top.tolist()]

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


def make_color_embeds(path, path_to_idx, output_path):

    images = load_images(path)

    model = FeatureExtractor()
    embeds = model.get_feature(images)
    embeds = [[list(i) for i in j] for j in embeds]
    dict = {}

    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    for i, feats in enumerate(embeds):
        dict[img_idxs[str(i)]] = feats

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


def get_faces_from_image(img):
    load_faces = face_recognition.load_image_file(img)
    encode_faces = face_recognition.face_encodings(load_faces)
    face_locations = face_recognition.face_locations(load_faces)

    return encode_faces, face_locations


def make_face_embeds(path, path_to_idx, output_path):

    images = load_images(path)
    embeds = []
    for img in images:
        embed, location = get_faces_from_image(img)

        if embed and location:
            embeds.append([j.tolist() for j in embed])
        else:
            embeds.append([])

    dict = {}

    with open(path_to_idx, "r") as openfile:

        img_idxs = json.load(openfile)

    for i, feats in enumerate(embeds):
        if feats:
            dict[img_idxs[str(i)]] = feats

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


def make_face_json(embeds, output_path):

    with open(embeds, "r") as openfile:

        embeds = json.load(openfile)

    cut_point = 0.6
    dict = {}
    for img, embed in embeds.items():
        res = []
        for image, embed1 in embeds.items():
            for face in embed1:
                matches = face_recognition.compare_faces(
                    np.array(embed), np.array(face), tolerance=cut_point)
                if any(matches) == True:

                    res.append(image)
                    break

        dict[img] = res

    with open(output_path, "w") as outfile:
        json.dump(dict, outfile)


if __name__ == "__main__":
    print(os.listdir(f"{__file__[:-14]}/server_setup"))
    if output_folder not in os.listdir(f"{__file__[:-14]}/server_setup"):
        os.makedirs(f"./server_setup/{output_folder}")

    config_list = {}
    config_list['features'] = []
    config_list['categories'] = [
        "Brand Color",
        "Pink",
        "Yellow",
        "Blue",
        "Black",
        "City",
        "Nature"
    ]

    # Function to generate index.json (Works as a numbering file for your images)
    print("Create index of images")
    make_image_index(data, f'./server_setup/{output_folder}/index.json')

    # Generate json file for context signal
    print("Create context index")
    make_sim_matrix(20, data, f'./server_setup/{output_folder}/index.json',
                    f'./server_setup/{output_folder}/clip.json')

    # Generate CLIP embeddings
    save_embeds(20, data, f"./server_setup/{output_folder}/index.json",
                f"./server_setup/{output_folder}/embeds.json")
    config_list['features'].append({
        "feature": "SimilarityMatrix",
        "file": f"./server_setup/{output_folder}/clip.json",
        "name": "Similar Context",
        "order": 7
    })
    make_sim_matrix(20, data, f'./server_setup/{output_folder}/index.json',
                    f'./server_setup/{output_folder}/clip70.json', threshold=0.7)

    config_list['features'].append({
        "feature": "SimilarityMatrix",
        "file": f"./server_setup/{output_folder}/clip70.json",
        "name": "Little less similar Context",
        "order": 8
    })

    # Generate json file for texture signal
    # print("Create texture index")
    # make_texture_matrix(data, f"./server_setup/{output_folder}/index.json",
                        # f"./server_setup/{output_folder}/texture.json")
    # config_list['features'].append({
        # "feature": "SimilarityMatrix",
        # "file": f"./server_setup/{output_folder}/texture.json",
        # "name": "Similar Texture (Patterns)",
        # "order": 0
    # })

    # print("Create tags index")
    # You can use ContentTaggingAPI using the methods above to get tags for your images and populate an index file
    # that will be of the following form:
    # {"image1": ["sunny", "bunny", "honey", "money", ...], "image2": [...], ...}
    # To use the API, your images have to be served publicly. The API accepts urls.
    # Otherwise, you can also provide your own index file for tags in the above form. Make sure you also create the inverse
    # tags index below!

    # print("Create inverse tags index")
    # inverse_tag_index(f'./server_setup/{output_folder}/tags.json',
    #                   f'./server_setup/{output_folder}/inverse_tags.json')
    # config_list['features'].append({
    #         "feature": "Tagging",
    #         "index": "./server_setup/columbia/tags.json",
    #         "inverse_index": f"./server_setup/{output_folder}/inverse_tags.json",
    #         "name": "First Tag",
    #         "n_tags": "1",
    #         "tags": [
    #             0
    #         ],
    #         "order": 3
    #     })

    # config_list['features'].append({
    #         "feature": "Tagging",
    #         "index": "./server_setup/columbia/tags.json",
    #         "inverse_index": f"./server_setup/{output_folder}/inverse_tags.json",
    #         "name": "Second Tag",
    #         "n_tags": "1",
    #         "tags": [
    #             1
    #         ],
    #         "order": 4
    #     })

    # config_list['features'].append({
    #         "feature": "Tagging",
    #         "index": "./server_setup/columbia/tags.json",
    #         "inverse_index": f"./server_setup/{output_folder}/inverse_tags.json",
    #         "name": "Choose your tags",
    #         "default": [
    #             0,
    #             1
    #         ],
    #         "order": 5,
    #         "n_tags": 2
    #     })

    # Generate json file for color signals
    print("Create color index")
    make_color_embeds(data, f'./server_setup/{output_folder}/index.json',
                      f'./server_setup/{output_folder}/color_embeds.json')
    config_list['features'].append({
        "feature": "Color",
        "file": f"./server_setup/{output_folder}/color_embeds.json",
        "name": "Color around Click",
        "order": 2
    })

    print("Create faces index")
    make_face_embeds(data, f'./server_setup/{output_folder}/index.json',
                     f'./server_setup/{output_folder}/face_embeds.json')
    #  Generate json file for face signal
    make_face_json(f'./server_setup/{output_folder}/face_embeds.json',
                   f'./server_setup/{output_folder}/faces.json')
    config_list['features'].append({
        "feature": "SimilarityMatrix",
        "file": f"./server_setup/{output_folder}/faces.json",
        "name": "Similar Faces",
        "order": 1
    })

    json_config = json.dumps(config_list)
    with open(f"./server_setup/{output_folder}/config.json", "w") as outfile:
        outfile.write(json_config)
