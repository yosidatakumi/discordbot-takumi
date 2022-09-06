from flask import Flask,request,abort
from threading import Thread

import os
import subprocess

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, VideoMessage, StickerMessage, FileMessage
)

from servers.five_hour import app2
from servers.bin.disreq import message_find,img_message,download

app = Flask(__name__)

app.register_blueprint(app2)

servers_name=os.environ['SERVER_NAME']
server_list=servers_name.split(",")

server_name=server_list[0]

line_bot_api = LineBotApi(os.environ[f'{server_name}_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ[f'{server_name}_CHANNEL_SECRET'])

@app.route(f"/{server_name}", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

	profile = line_bot_api.get_profile(event.source.user_id)

	message_find(
        event.message.text,
        os.environ[f"{server_name}_GUILD_ID"],
        os.environ[f"{server_name}_TEMPLE_ID"],
        profile
        )

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):

	profile = line_bot_api.get_profile(event.source.user_id)

	message_find(
        f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{event.message.sticker_id}/iPhone/sticker_key@2x.png",
        os.environ[f"{server_name}_GUILD_ID"],
        os.environ[f"{server_name}_TEMPLE_ID"],
        profile
        )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):

	profile = line_bot_api.get_profile(event.source.user_id)
	# message_idから画像のバイナリデータを取得
	message_content = line_bot_api.get_message_content(event.message.id).content

	gyazo=img_message(message_content)

	message_find(
        gyazo,
        os.environ[f"{server_name}_GUILD_ID"],
        os.environ[f"{server_name}_TEMPLE_ID"],
        profile
        )

@handler.add(MessageEvent, message=VideoMessage)
def handle_video(event):

	profile = line_bot_api.get_profile(event.source.user_id)
	# message_idから動画のバイナリデータを取得
	message_content = line_bot_api.get_message_content(event.message.id)

	download(message_content)
	res = subprocess.run(['python', 'upload_video.py', f'--title="{profile.display_name}の動画"','--description="LINEからの動画"'], capture_output=True)
	message_find(
        f'https://youtu.be/{res.stdout.decode()}',
        os.environ[f"{server_name}_GUILD_ID"],
        os.environ[f"{server_name}_TEMPLE_ID"],
        profile
        )

if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)

def run():
  app.run("0.0.0.0", port=8080, threaded=True)
  #app.run()

def keep_alive():
  t = Thread(target=run)
  t.start()