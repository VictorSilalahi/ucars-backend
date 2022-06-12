import uvicorn
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import config.db as db
import os
import aiofiles
import uuid
import re
import socket

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
thishost = socket.gethostbyname(socket.gethostname())+":8000/static/data/cars/"

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8000/v1/brands",
    "http://127.0.0.1:8000/v1/models",
    "*"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
dbase = db.toConnect()

@app.get("/")
async def index():
    return {"msg":"UCARS"}

# show HTML Form
@app.get("/formbrand", response_class=HTMLResponse)
async def form_brand(request: Request):
    return templates.TemplateResponse("brandform.html", context={'request': request})

@app.get("/formmodel", response_class=HTMLResponse)
async def form_model(request: Request):
    brandlist = []
    tbrnds = dbase['tBrands']
    all = tbrnds.find()
    for a in all:
        brandlist.append({"brandid":a["brandid"],"brandname":a["brandname"]})
    print(brandlist)
    return templates.TemplateResponse("modelform.html", context={'request': request, 'brands':brandlist})

@app.get("/brands/get/{brandid}", response_class=HTMLResponse)
async def get_brand(request: Request, brandid: str):
    vid = None
    vbname = None
    tbrnds = dbase['tBrands']
    search = {"brandid":brandid}
    all = tbrnds.find(search)
    for a in all:
        vid = a['brandid']
        vbname = a['brandname']
    return templates.TemplateResponse("branditemform.html", {"request": request, "id": vid, "brandname":vbname })

@app.get("/models/get/{modelid}", response_class=HTMLResponse)
async def get_model(request: Request, modelid: str):
    tm = dbase['tModels']
    search = {"modelid":modelid}
    all = tm.find(search)
    for a in all:
        vid = a['modelid']
        vbname = a['modelname']
        vdesc = a['desc']
        vprice = a['price']
    return templates.TemplateResponse("modelitemform.html", {"request": request, "id": vid, "modelname":vbname, "desc":vdesc, "price":vprice })

# REST API 
# - Car Brand -
@app.get("/v1/brands")
async def get_all_brands():
    data = []
    tbrnds = dbase['tBrands']
    all = tbrnds.find()
    for a in all:
        data.append( {"brandid":a["brandid"], "brandname":a["brandname"],"brandlogo":a["brandlogo"]} )
    return data

@app.post("/v1/brands")
async def save_new_brand(txtBrandName: str = Form(), fileLogo: UploadFile = File() ):
    fullpath = APP_ROOT+"\static\data\logos\\"+fileLogo.filename
    async with aiofiles.open(fullpath, 'wb') as out_file:
        while content := await fileLogo.read(1024):  # async read file chunk
            await out_file.write(content)  # async write file chunk
    tbrnds = dbase['tBrands']
    res = tbrnds.insert_one({
        "brandid": str(uuid.uuid4()),
        "brandname":txtBrandName,
        "brandlogo":fullpath
    })
    return str(res.inserted_id)

@app.delete("/v1/brands/{brandid}")
async def delete_brand(brandid: str):
    tbrnds = dbase['tBrands']
    res = tbrnds.delete_one({
        "brandid":brandid
    })
    return str(res.deleted_count)

@app.post("/v1/brands/update")
async def update_brand(txtId: str = Form(), txtBrandName: str = Form()):
    tbrnds = dbase['tBrands']
    query = {"brandid":txtId }
    newval = { "$set": { "brandname": txtBrandName } }
    res = tbrnds.update_one(query, newval)
    return str(res.modified_count)

# REST API 
# - Car Model -
@app.get("/v1/models/{brandid}")
async def get_all_models(brandid: str):
    data = []
    tm = dbase['tModels']
    query = {"brandid":brandid }
    all = tm.find(query)
    for a in all:
        data.append( {"modelid":a["modelid"], "modelname":a["modelname"], "modelimage":a["modelimage"], "desc":a["desc"], "price":a["price"]} )
    return data

@app.post("/v1/models")
async def save_new_model(txtModelName: str = Form(), filePic: UploadFile = File(), slcBrandId: str = Form(), txtDescription: str = Form(), txtPrice: str = Form() ):
    fullpath = APP_ROOT+"\static\data\cars\\"+filePic.filename
    async with aiofiles.open(fullpath, 'wb') as out_file:
        while content := await filePic.read(1024):  # async read file chunk
            await out_file.write(content)  # async write file chunk
    tm = dbase['tModels']
    res = tm.insert_one({
        "modelid": str(uuid.uuid4()),
        "modelname":txtModelName,
        "brandid":slcBrandId,
        "modelimage":filePic.filename,
        "desc": txtDescription,
        "price": txtPrice
    })
    return str(res.inserted_id)

@app.delete("/v1/models/{modelid}")
async def delete_model(modelid: str):
    tm = dbase['tModels']
    res = tm.delete_one({
        "modelid":modelid
    })
    return str(res.deleted_count)

@app.post("/v1/model/update")
async def update_model(txtModelId: str = Form(), txtModelName: str = Form(), txtDescription: str = Form(), txtPrice: str = Form()):
    tm = dbase['tModels']
    query = {"modelid": txtModelId }
    newval = { "$set": { "modelname": txtModelName, "desc":txtDescription, "price":txtPrice } }
    res = tm.update_one(query, newval)
    return str(res.modified_count)

@app.get("/v1/search/{srch}")
async def search(srch: str):
    data = []
    srch1 = re.compile(".*"+srch+".*", re.IGNORECASE)
    srch2 = re.compile(".*"+srch, re.IGNORECASE)
    srch1 = re.compile(srch+".*", re.IGNORECASE)
    tm = dbase['tModels']
    all = tm.find({
        "$or":[
            {"modelname":srch1},
            {"modelname":srch2},
            {"modelname":srch2}
        ]
    })
    for a in all:
        data.append( {"modelid":a["modelid"], "modelname":a["modelname"],"desc":a["desc"],"price":a["price"],"image":"http://"+thishost+a["modelimage"]} )
    return data

if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)