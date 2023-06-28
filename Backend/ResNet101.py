from tensorflow.keras.applications.resnet_rs import ResNetRS101, preprocess_input
from tensorflow.keras.models import Model
#from tensorflow.keras.preprocessing import image
import numpy as np
import tensorflow as tf
from PIL import Image
import torch
import os
from dotenv import load_dotenv

load_dotenv('../.env')

pathnm = os.environ.get("PATH_TO_IMAGES")

class FeatureExtractor:
    def __init__(self):
        # Use ResNet50 as the architecture and ImageNet for the weight
        # resnet_weights_path = '../input/keras-pretrained-models/resnet50_weights_tf_dim_ordering_tf_kernels.h5'
        base_model = ResNetRS101(weights='imagenet')
        # Customize the model to return features from fully-connected layer
        self.model = Model(inputs=base_model.input,
                           outputs=base_model.get_layer('avg_pool').output)

    def extract(self, img):
        # Resize the image
        img = img.resize((224, 224))
        # Convert the image color space
        img = img.convert('RGB')
        # Reformat the image
        x = np.asarray(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        # Extract Features
        feature = self.model.predict(x)[0]
        return feature / np.linalg.norm(feature)

    def get_feature(self, image_data: list):
        self.image_data = image_data

        features = []
        for img_path in self.image_data:  # Iterate through images
            # Extract Features

            feature = self.extract(img=Image.open(img_path))

            features.append(feature)
        features = np.asarray(features)
        return features


if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    model = FeatureExtractor()

    images = [os.path.join(pathnm, img) for img in os.listdir(pathnm)][:10]

    features = model.get_feature(images)

    features = torch.from_numpy(features)
    sim_matrix = torch.matmul(features, features.t())
    sim = torch.topk(sim_matrix, 5).indices
