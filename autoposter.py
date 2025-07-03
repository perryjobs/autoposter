import os, yaml, time, pytz, datetime as dt
from pathlib import Path
from tweepy import Client, OAuth1UserHandler, API
import requests

TZ = pytz.timezone("America/Jamaica")

def iter_posts():
    for post_dir in Path("posts").iterdir():
        meta = yaml.safe_load((post_dir / "meta.yml").read_text())
        meta['path'] = post_dir
        yield meta

def due(meta):
    if meta['status'] != 'pending': return False
    ts = TZ.localize(dt.datetime.strptime(meta['datetime'], "%Y-%m-%d %H:%M"))
    return dt.datetime.now(TZ) >= ts

def post_to_twitter(meta, image_path):
    auth = OAuth1UserHandler(
        os.getenv("TW_CONSUMER_KEY"), os.getenv("TW_CONSUMER_SECRET"),
        os.getenv("TW_ACCESS_TOKEN"), os.getenv("TW_ACCESS_SECRET"))
    api = API(auth)
    media = api.media_upload(filename=image_path)
    api.update_status(status=meta['caption'], media_ids=[media.media_id_string])

def post_to_instagram(meta, image_path):
    acc = os.getenv("IG_ACCOUNT_ID")
    token = os.getenv("IG_ACCESS_TOKEN")
    # 1. create container
    url = f"https://graph.facebook.com/v19.0/{acc}/media"
    resp = requests.post(url, data={
        "image_url": f"https://raw.githubusercontent.com/<USER>/<REPO>/main/{image_path}",
        "caption": meta['caption'],
        "access_token": token
    }).json()
    container_id = resp["id"]
    # 2. publish
    pub = requests.post(
        f"https://graph.facebook.com/v19.0/{acc}/media_publish",
        data={ "creation_id": container_id, "access_token": token}).json()
    return pub

for meta in iter_posts():
    img = next(Path(meta['path']).glob("*.[jp][pn]*g"))   # first image
    if due(meta):
        if 'twitter' in meta['platforms']:  post_to_twitter(meta, img)
        if 'instagram' in meta['platforms']: post_to_instagram(meta, img)
        meta['status'] = 'posted'
        (Path(meta['path']) / "meta.yml").write_text(yaml.dump(meta))

