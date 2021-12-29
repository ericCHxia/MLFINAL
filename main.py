import celery
import celery.result
import celery.exceptions
from flask import Flask,request,abort,send_file,make_response
from flask_socketio import SocketIO, emit
from task import lama_task, detectron2_task
import task
import PIL.Image as Image
from flask_cors import CORS
import numpy as np
from io import BytesIO

app = Flask(__name__)
CORS(app,  resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app)

def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route("/")
def hello_world():
    return {
        "status":"OK"
    }

@app.route("/detectron2_upload", methods=['POST'])
def detectron2_upload():
    image = request.files["image"]
    image = Image.open(image.stream)
    max_width = 500
    max_height = 500
    ratio1 = 1 if max_width >= image.width else max_width/image.width
    ratio2 = 1 if max_height >= image.height else max_height/image.height
    ratio = min(ratio1,ratio2)
    image = image.resize((int(ratio*image.width),int(ratio*image.height)))
    # res:celery.result.AsyncResult = detectron2_task.AsyncResult("ee554340-6529-4ec0-a0b2-6472da4e718f")
    res:celery.result.AsyncResult = detectron2_task.delay(image)
    return {"res":res.get().tolist(),"id":res.id}

@app.route("/detectron2/<id>/<int:maskid>", methods=['GET'])
def detectron2_mask(id,maskid):
    res:celery.result.AsyncResult = detectron2_task.AsyncResult(id)
    try:
        res = res.get(timeout=3)
        res = res==maskid
        res = np.array([res*255,res*0,res*0,res*125]).astype(np.uint8).transpose([1,2,0])
        image = Image.fromarray(res).convert("RGBA")
        max_width = 128
        max_height = 128
        ratio1 = 1 if max_width >= image.width else max_width/image.width
        ratio2 = 1 if max_height >= image.height else max_height/image.height
        ratio = min(ratio1,ratio2)
        image = image.resize((int(ratio*image.width),int(ratio*image.height)))
        return serve_pil_image(image)
    except celery.exceptions.TimeoutError:
        return abort(404)

def mask2reag(mask:np.ndarray):
    mask_w = mask.max(axis=1)
    
    mask_h = mask.max(axis=0)
    p1 = []
    p2 = []
    for i,v in enumerate(mask_w):
        if v:
            p1.append(i)
            break
    for i,v in enumerate(mask_w[::-1]):
        if v:
            p2.append(len(mask_w)-i)
            break
    for i,v in enumerate(mask_h):
        if v:
            p1.append(i)
            break
    for i,v in enumerate(mask_h[::-1]):
        if v:
            p2.append(len(mask_h)-i)
            break
    p1[0] = max(0,p1[0]-5)
    p1[1] = max(0,p1[1]-5)

    p2[0] = min(len(mask_w),p2[0]+5)
    p2[1] = min(len(mask_h),p2[1]+5)
    print(p1,p2)
    mask[p1[0]:p2[0],p1[1]:p2[1]]=True
    return mask

@app.route("/lama/", methods=['POST'])
def lama_step():
    image = request.files["image"]
    image = Image.open(image.stream)
    ids = request.form.get("id")
    ids = [int(i) for i in ids.split(",")]
    task_id = request.form.get("task")

    max_width = 1000
    max_height = 1000
    ratio1 = 1 if max_width >= image.width else max_width/image.width
    ratio2 = 1 if max_height >= image.height else max_height/image.height
    ratio = min(ratio1,ratio2)
    image = image.resize((int(ratio*image.width),int(ratio*image.height)))
    try:
        res:celery.result.AsyncResult = detectron2_task.AsyncResult(task_id)
        res = res.get(timeout=3)
        mask = np.zeros_like(res).astype(np.bool)
        for i in ids:
            mask = mask|mask2reag(res==i)
        mask = (mask*255).astype(np.uint8)
        mask = Image.fromarray(mask).resize((image.width,image.height))
        mask.save("tmp.jpg")
        res = lama_task.delay(image,mask)
        return res.get()
    except celery.exceptions.TimeoutError:
        abort(404)

if __name__ == '__main__':
   app.run(port=8053)