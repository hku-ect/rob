import sys
import json
import random
import discord
from discord.ext import commands
import shelve
import matplotlib.pyplot as plt
import io

#ustats = {}
ustats = shelve.open("userstats", writeback=True)

client = commands.Bot(command_prefix='?')

def require_user(discorduser):
    user = ustats.get(discorduser.name, None)
    if not user:
        ustats[discorduser.name] = { 'displayname' : discorduser.display_name, 'total_words': 0, 'total_messages': 0, 'total_reactions': 0, "assign1" : "incomplete", "assign2" : "incomplete", "assign3" : "incomplete", "assign4" : "incomplete" }
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

def update_message_count(duser):
    user = require_user(duser)
    cur_count = user.get('total_messages', 0)
    user['total_messages'] = cur_count + 1
    update_user(duser, user)

def update_reaction_count(duser):
    user = require_user(duser)
    cur_count = user.get('total_reactions', 0)
    user['total_reactions'] = cur_count + 1
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

def dumpdbcsv():
    ret = "username;"
    columns = ["assign1", "assign2", "assign3", "assign4"]
    for v in columns:
        ret += "{};".format(v)
    ret+="\n"
    for user, entry in ustats.items():
        ret += "{};".format(user)
        for c in columns:
            ret += entry.get(c, "not found")
            ret += ";"
        ret += "\n"
    return ret

def bar_chart(numbers, labels, pos):
    plt.barh(pos, numbers, color='green')
    plt.barh(pos, numbers, color='red')
    plt.yticks(ticks=pos, labels=labels)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    #im = Image.open(buf)    
    #plt.show()
    return buf   

def require_assign1(msg):
    if msg.channel.name != "opdracht-1-screenshot-dag-1":
        return
    user = require_user(msg.author)
    if user.get("assign1", "") == "completed":
        return
    if len(msg.attachments) and msg.attachments[0].content_type.startswith("image"):
        user["assign1url"] = msg.attachments[0].url
        user["assign1"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign1"] = "incomplete"
        update_user(msg.author, user)

# assign 3: ask for help challenge
def require_assign3(msg):
    if msg.channel.name == "ask-for-help-challenge":
        return 2
    if (msg.channel.category_id == 917742829336428631): # d.dungeons category
        user = require_user(msg.author)
        if user.get("assign3", "") == "completed":
            return 0
        user["assign3"] = "completed"
        update_user(msg.author, user)
        return 1

#assign4: give help proof screenshot
def require_assign4(msg):
    user = require_user(msg.author)
    if user.get("assign4", "") == "completed":
        return False
    if len(msg.attachments) and msg.attachments[0].content_type.startswith("image"):
        user["assign4url"] = msg.attachments[0].url
        user["assign4"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign4"] = "incomplete"
        update_user(msg.author, user)

        
#assign5: pdf presentation upload
def require_assign5(msg):
    if msg.channel.name != "your-presentation-week-1":
        return        
    user = require_user(msg.author)
    if user.get("assign5", "") == "completed":
        return False
    if ( len(msg.attachments) and msg.attachments[0].content_type.startswith("application/pdf") ) or "http" in msg.content:
        user["assign5url"] = msg.attachments[0].url
        user["assign5"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign4"] = "incomplete"
        update_user(msg.author, user)

#assign6: faceswap proof screenshot
def require_assign6(msg):
    user = require_user(msg.author)
    if user.get("assign4", "") == "completed":
        return False
    if len(msg.attachments) and msg.attachments[0].content_type.startswith("image"):
        user["assign4url"] = msg.attachments[0].url
        user["assign4"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign4"] = "incomplete"
        update_user(msg.author, user)

#assign7: play with runway proof screenshot
#assign8: link/pdf/docx of zip
#assign9: end presentation pdf/pptp/ group???

@client.command()
async def stat(ctx, user):
    await ctx.send(dump_stats(user))

@client.command()
async def dumpdb(ctx):
    await ctx.send("```json\n" + json.dumps(dict(ustats)) + "```")

@client.command()
async def dumpcsv(ctx):
    await ctx.send(dumpdbcsv())

@client.command()
async def hiscore(ctx, iets=None):
    iets = iets or "total_words"
    print("generate chart for {}".format(iets))
    score = {}
    for k,v in ustats.items():
        w = v.get(iets, 0)
        score[k] = w
    res = {key: val for key, val in sorted(score.items(), key = lambda ele: ele[0])}
    #print(numbers)
    labels = res.keys() #['Electric', 'Solar', 'Diesel', 'Unleaded']
    #print(labels)
    pos = range(len(res))
    img = bar_chart(res.values(), labels, pos)
    await ctx.send(file=discord.File(img, filename="hiscore.png"))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    #print(message)
    if message.author == client.user:
        return

    await client.process_commands(message)
    
    if require_assign1(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)
    
    ret = require_assign3(message)
    if ret == 1:
        #emoji = get(message.server.emojis, name="img000000093")
        emoji = '\N{White Heavy Check Mark}'
        #'\N{THUMBS UP SIGN}'
        await message.add_reaction(emoji)
    elif ret == 2:
        reps = ['Hallo {}, misschien kun je beter om hulp vragen in een van de dungeons kanalen?', 
                'Goede post {}! Maar als het voor de "hulp-vraag-challenge" is, kun je die beter posten in de Help-help-helpdesk (in de Dungeons)'
                'ja, okay, maar {} . . ., misschien kun je hulpvragen beter in een van de dungeons kanalen posten, zoals de HelpDesk?']        
        await message.channel.send(random.choice(reps).format(message.author.name), reference=message)

    if require_assign4(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    if require_assign5(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)
    
    #print(message.content)
    if message.content.lower().startswith('hello'):
        #emoji = '\N{Waving Hand Sign}'
        #await message.add_reaction(emoji)
        await message.channel.send('Hello {}!'.format(message.author.name))

    # count words
    words = len(message.content.strip().split(" "))
    update_word_count(message.author, words)

    update_message_count(message.author)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    update_reaction_count(user)


### TODO: how to get who created the channel as it is not in members list
@client.event
async def on_guild_channel_create(channel):
    print(channel)
    for user in channel.members:
        print("channel {} member {}".format(channel.name, user))
        ustat = require_user(user)
        ustat["assign2"] = "completed"
        ustat["assign2channel"] = channel.name
        update_user(user, ustat)

@client.event
async def on_guild_channel_update(before, after):
    print("channel {} update".format(before))
    for user in after.members:
        print("channel {} member {}".format(after.name, user))
        ustat = require_user(user)
        ustat["assign2"] = "completed"
        ustat["assign2channel"] = after.name
        update_user(user, ustat)

if __name__ == "__main__":
    token = sys.argv[1]
    try:
        client.run(token)
    finally:
        ustats.close()
