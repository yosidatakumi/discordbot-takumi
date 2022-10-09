import discord
import os

from cogs.bin.daylimit import PushLimit
from core.signal import day_signal,angry_signal

from linebot import (
    LineBotApi
)

from linebot.models import (
    TextSendMessage, ImageSendMessage, VideoSendMessage
)

from discord.ext import commands
from core.start import DBot

class mst_line(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot      

    @commands.slash_command()
    async def test_signal(self,ctx:discord.ApplicationContext):

        servers_name=os.environ['SERVER_NAME']
        server_list=servers_name.split(",")
        for server_name in server_list:
            if int(os.environ[f"{server_name}_GUILD_ID"])==int(ctx.guild.id):
                await ctx.respond("LINE連携の利用状況です。")
                day_signal([server_name],f"<@{ctx.author.id}>\nテストコマンド 現在の上限です")
                angry_signal(PushLimit(server_name),f"<@{ctx.author.id}>\n",server_name)
                

    # DiscordからLINEへ
    @commands.Cog.listener(name='on_message')
    async def on_message(self, message:discord.Message):

        if (message.author.bot is True or
            message.channel.nsfw is True or
            message.type == discord.MessageType.pins_add or
            message.channel.type == "voice"):
            return

        # FIVE_SECONDs,FIVE_HOUR
        # ACCESS_TOKEN,GUILD_ID,TEMPLE_ID (それぞれ最低限必要な環境変数)
        servers_name=os.environ['SERVER_NAME']
        server_list=servers_name.split(",")

        messagelist=[]

        messagetext=f"{message.channel.name}にて、{message.author.name}"

        if message.type == discord.MessageType.new_member:
            messagetext=f"{message.author.name}が参加しました。"

        if message.type == discord.MessageType.premium_guild_subscription:
            messagetext=f"{message.author.name}がサーバーブーストしました。"
        
        if message.type == discord.MessageType.premium_guild_tier_1:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル1になりました！！！！！！！！"
        
        if message.type == discord.MessageType.premium_guild_tier_2:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル2になりました！！！！！！！！！"
        
        if message.type == discord.MessageType.premium_guild_tier_3:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル3になりました！！！！！！！！！！！"

        if message.attachments:

            messagelist,imgcnt,videocnt=file_checker(message.attachments)

            messagetext+="が、"

            if imgcnt>0:
                messagetext+=f"画像を{imgcnt}枚、"

            if videocnt>0:
                messagetext+=f"動画を{videocnt}個"

            if (imgcnt+videocnt)<len(message.attachments):
                for attachment in message.attachments:
                    messagetext+=f"\n{attachment.url} "

            messagetext+="送信しました。"

        messagetext+=f"「 {message.clean_content} 」"

        if message.stickers:
            if message.stickers[0].url.endswith(".json"):
                return
            else:
                messagelist,imgcnt,videocnt=file_checker(message.stickers)
                messagelist.insert(0,TextSendMessage(text=f"{messagetext} スタンプ:{message.stickers[0].name}"))
        else:
            messagelist.insert(0,TextSendMessage(text=messagetext))

        
        for server_name in server_list:
            if int(os.environ[f"{server_name}_GUILD_ID"])==int(message.guild.id):
                limit=PushLimit(name=server_name)
                if (limit.todaypush()>limit.onedaypush() or
                    limit.afterpush()>=1000 or
                    (limit.daylimit()<limit.templelimit() and 
                    int(message.channel.id)!=int(os.environ[f"{server_name}_TEMPLE_ID"]))):
                    return
                ng_channel=os.environ.get(f"{server_name}_NG_CHANNEL").split(",")
                for ng in ng_channel:
                    if ng == message.channel.name:
                        return
                if limit.afterpush()>limit.onedaypush():
                    #print("angry!! fuck you!!")
                    angry_signal(
                        limit,
                        f"<@{message.author.id}>\n",
                        server_name
                    )
                    
                name_tmp=str(server_name)
                line_bot_api = LineBotApi(os.environ[f"{name_tmp}_ACCESS_TOKEN"])
                # グループIDが存在する場合。
                if os.environ.get(f"{name_tmp}_GROUP_ID")!=None:
                    return line_bot_api.push_message(to=os.environ[f"{name_tmp}_GROUP_ID"],messages=messagelist)
                else:
                    return line_bot_api.broadcast(messagelist)
            

def file_checker(attachments):
    image=[".jpg",".png",".JPG",".PNG",".jpeg",".gif",".GIF"]
    eventsdata=[]
    imgcnt=0
    videocnt=0
    for attachment in attachments:
        for file in image:
            iurl=str(attachment.url)
            if iurl.endswith(file):
                eventsdata.append(ImageSendMessage(
                    original_content_url=iurl,
                    preview_image_url=iurl))
                imgcnt+=1

    video=[".mp4",".MP4",".MOV",".mov",".mpg",".avi",".wmv"]
    for attachment in attachments:
        for file in video:
            iurl=str(attachment.url)
            if iurl.endswith(file):
                eventsdata.append(VideoSendMessage(
                    original_content_url=iurl,
                    preview_image_url="https://cdn.discordapp.com/attachments/943046430711480402/987284460070404106/ohime.JPG"))
                videocnt+=1

    # print(eventsdata,flush=True)
   
    return eventsdata,imgcnt,videocnt


def voice_checker(attachments):
    voice=[".wav",".mp3",".flac",".aif",".m4a",".oga",".ogg"]
    eventsdata=[]
    cnt=0
    for attachment in attachments:
        for file in voice:
            iurl=str(attachment.url)
            if iurl.endswith(file):
                eventsdata.append({f"voice{cnt}": iurl})
                cnt+=1
   
    return eventsdata

def setup(bot):
    return bot.add_cog(mst_line(bot))