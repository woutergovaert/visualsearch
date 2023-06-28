from transformers import CLIPProcessor, CLIPModel
from torch import matmul, topk
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv('../.env')


class CLIP:
    def __init__(
        self,
    ):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32")

    def __call__(self, text=None, images=None):

        if text is not None and images is not None:

            images = [Image.open(img) for img in images]

            img_inputs = self.processor(images=images, return_tensors="pt")
            txt_inputs = self.processor(
                text=text, return_tensors="pt", padding=True)
            image_embeds = self.model.get_image_features(**img_inputs)
            text_embeds = self.model.get_text_features(
                **txt_inputs,
            )

            image_embeds = image_embeds / \
                image_embeds.norm(p=2, dim=-1, keepdim=True)
            text_embeds = text_embeds / \
                text_embeds.norm(p=2, dim=-1, keepdim=True)

            return matmul(text_embeds, image_embeds.t())

        if images is not None:

            images = [Image.open(img) for img in images]

            img_inputs = self.processor(images=images, return_tensors="pt")
            image_embeds = self.model.get_image_features(**img_inputs)

            image_embeds = image_embeds / \
                image_embeds.norm(p=2, dim=-1, keepdim=True)

            return image_embeds

        if text is not None:

            txt_inputs = self.processor(
                text=text, return_tensors="pt", padding=True)
            text_embeds = self.model.get_text_features(**txt_inputs)

            text_embeds = text_embeds / \
                text_embeds.norm(p=2, dim=-1, keepdim=True)

            return text_embeds


if __name__ == "__main__":
    pathnm = os.environ.get("PATH_TO_IMAGES")
    print(os.listdir("./"))
    images = [os.path.join(pathnm, img) for img in os.listdir(pathnm)]
    # # text = ["photo of people", "photo of animal"]
    model = CLIP()
    i = 0
    while i < 1700:

        embeds = model(images=images[i:i+20])
        print(i)
        sim_matrix = matmul(embeds, embeds.t())
        best_imgs = topk(sim_matrix, 10).indices
        for j in range(len(best_imgs)):
            if best_imgs[j][0] != j:
                print(j)
        i += 20
        # print(best_idxs)
