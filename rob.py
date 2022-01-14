import sys
import discord
from discord.ext import commands
import shelve


#ustats = {}
ustats = shelve.open("userstats", writeback=True)

client = commands.Bot(command_prefix='?')

def require_user(discorduser):
    user = ustats.get(discorduser.name, None)
    if not user:
        ustats[discorduser.name] = { 'displayname' : discorduser.display_name, 'total_words': 0 }
        return ustats[discorduser.name]
    return user

def update_user(duser, duserstat):
    ustats.update({duser.name: duserstat})
    ustats.sync()

def update_word_count(duser, count):
    user = require_user(duser)
    cur_count = user['total_words']
    print(cur_count, count)
    user['total_words'] = cur_count + count
    update_user(duser, user)

def dump_stats(username):
    user = ustats.get(username, None)
    if not user:
        return "User {0} not found".format(username)
        
    statskeys = sorted(user.keys())
    ret = "Stats for user: {}\n".format(username)
    for key in statskeys:
        ret += "{} : {}\n".format(key, user[key])
    return ret

def require_assign1(msg):
    if msg.channel.name != "opdracht-1-screenshot-dag-1":
        return
    print("we're in")
    user = require_user(msg.author)
    if user.get("assign1", "") == "completed":
        return
    print("check attach", msg.attachments)
    if len(msg.attachments) and msg.attachments[0].content_type.startswith("image"):
        print(msg.attachments[0])
        user["assign1url"] = msg.attachments[0].url
        user["assign1"] = "completed"
        update_user(msg.author, user)

@client.command()
async def stat(ctx, user):
    print(user, ctx)
    await ctx.send(dump_stats(user))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    print(message)
    if message.author == client.user:
        return

    await client.process_commands(message)
    
    require_assign1(message)

    if message.content.lower().startswith('hello'):
        await message.channel.send('Hello {}!'.format(message.author.name))

    require_user(message.author)

    # count words
    words = len(message.content.strip().split(" "))
    update_word_count(message.author, words)


if __name__ == "__main__":
    token = sys.argv[1]
    try:
        client.run(token)
    finally:
        ustats.close()
