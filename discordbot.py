import discord
import os
import traceback
from datetime import datetime, timedelta
import sys
import requests
from dispander import dispand
from discord.ext import commands


### イベントハンドラ一覧(client) #################################################
# async def の後を変えるだけで実行されるイベンドが変わる
# メッセージ受信時に実行：   on_message(message)
# Bot起動時に実行：      on_ready(message)
# リアクション追加時に実行:  on_reaction_add(reaction, user)
# 新規メンバー参加時に実行： on_member_join(member)
# ボイスチャンネル出入に実行： on_voice_state_update(member, before, after)
###################################################################

#onlinetoken@heroku
token = os.environ['DISCORD_BOT_TOKEN']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/",intents=intents)

#IDなど
guildid = 916965252896260117
logchannel = 916971090042060830
vclogchannel = 916988601902989373


#Bootmsg-serverlogchannel/console
async def greet():
    channel = bot.get_channel(logchannel)
    await channel.send('起動完了')

@bot.event
async def on_ready():
    print('logged in as {0.user}'.format(bot))
    await greet()



#Dispander
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await dispand(message)
    await bot.process_commands(message)

'''
デフォルトで提供されている on_message をオーバーライドすると、コマンドが実行されなくなります。
これを修正するには on_message の最後に bot.process_commands(message) を追加してみてください。
'''

#VC入退室ログ
@bot.event
async def on_voice_state_update(member,before,after) :
    if member.guild.id == guildid and (before.channel != after.channel):
        now = datetime.utcnow() + timedelta(hours=9)
        alert_channel = bot.get_channel(vclogchannel)
        vclogmention = f'<@{member.id}>'
        if before.channel is None:
            msg = f'{now:%m/%d-%H:%M:%S} に {vclogmention} が "{after.channel.name}" に参加しました。'
            await alert_channel.send(msg)
        elif after.channel is None:
            msg = f'{now:%m/%d-%H:%M:%S} に {vclogmention} が "{before.channel.name}" から退出しました。'
            await alert_channel.send(msg)
        else:
            msg = f'{now:%m/%d-%H:%M:%S} に {vclogmention} が "{before.channel.name}" から "{after.channel.name}" に移動しました。'
            await alert_channel.send(msg)


#oumu
@bot.command()
async def test(ctx):
    await ctx.send('hello')

#fetchuser?

class FetchUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # commands.Botインスタンスを代入

    @commands.command()
    async def fetch_user(self, target_id: int):
        try:
            target = await self.bot.fetch_user(target_id)
        except discord.NotFound:
            # ユーザーが見つからなかった場合の処理（以下は一例）
            await ctx.send("ユーザーが見つかりませんでした。")
            return

        await ctx.send(str(target)) # Username#0000



bot.run(token)