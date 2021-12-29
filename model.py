import torch
import torch.nn.functional as F
import PIL.Image as Image
import torchvision.transforms as transforms
import numpy as np
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg

class transformMod:
    def __init__(self, mod=8) -> None:
        self.mod = mod

    def ceil_modulo(self, x):
        if x % self.mod == 0:
            return x
        return (x // self.mod + 1) * self.mod

    def __call__(self, img):
        _, height, width = img.shape
        out_height = self.ceil_modulo(height)
        out_width = self.ceil_modulo(width)
        return F.pad(img.unsqueeze(0), (0, out_width - width, 0, out_height - height), mode='reflect').squeeze(0)

class Detectron2:
    def __init__(self) -> None:
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-PanopticSegmentation/panoptic_fpn_R_50_3x.yaml"))
        cfg.MODEL.WEIGHTS = "./model_final_c10459.pkl"
        
        self.predictor = DefaultPredictor(cfg)

    def __call__(self, image: Image.Image):
        image = np.array(image)
        panoptic_seg, _ = self.predictor(image)["panoptic_seg"]
        return panoptic_seg.to("cpu").numpy()

class LAMA:
    def __init__(self, device="cpu") -> None:
        self.device = device
        self._device = torch.device(device)
        self.transform = transforms.Compose(
            [transforms.ToTensor(), transformMod()])
        self.model = torch.jit.load('lama_cpu.pt').to(self._device)

    def __call__(self, image: Image.Image, mask: Image.Image):
        image = self.transform(image)
        mask = self.transform(mask)
        image = torch.unsqueeze(image, 0)
        mask = torch.unsqueeze(mask, 0)
        mask = (mask > 0) * 1

        result = self.model(image.to(self._device), mask.to(self._device))

        result = result[0].detach().cpu().numpy()
        result = np.clip(result * 255, 0, 255).astype('uint8')

        return Image.fromarray(result.transpose(1, 2, 0))

if __name__ == "__main__":
    model = Detectron2()
    img = Image.open("tmp.jpg").convert("RGB")
    res = model(img)
    print(res)