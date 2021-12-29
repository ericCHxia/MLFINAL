from celery import Celery
from config import load_config
import os
if os.getenv("IS_SERVER") is not None:
    from model import LAMA, Detectron2
    from utils import upload

config = load_config()
app = Celery('task', backend=config.celery.backend, broker=config.celery.broker)
app.conf.update(
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle']
)
lama_model = None
detectron2_model = None

@app.task
def lama_task(image, mask):
    global lama_model
    global config
    if lama_model is None:
        lama_model = LAMA(config.lama.device)
    mask = mask.convert("L")
    result = lama_model(image,mask)
    return upload(result)

@app.task
def detectron2_task(image):
    global detectron2_model
    global config
    if detectron2_model is None:
        detectron2_model = Detectron2()
    return detectron2_model(image)
