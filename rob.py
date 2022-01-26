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
        ustats[discorduser.name] = { 'displayname' : discorduser.display_name, 'total_words': 0, 'total_messages': 0, 'total_reactions': 0, "assign1" : "incomplete", "assign2" : "incomplete", "assign3" : "incomplete", "assign4" : "incomplete", "assign5" : "incomplete", "assign6" : "incomplete", "assign7" : "incomplete", "assign8" : "incomplete"   }
        return ustats[discorduser.name]
    return user

def update_user(duser, duserstat):
    ustats.update({duser.name: duserstat})
    ustats.sync()

def update_word_count(duser, count):
    user = require_user(duser)
    cur_count = user['total_words']
    #print(cur_count, count)
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
    columns = ["assign1", "assign2", "assign3", "assign4", "assign5", "assign6", "assign7", "assign8"]
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

def bar_chart(key):
    keys = key or ['assign1', 'assign2', 'assign3', 'assign4', 'assign5', 'assign6', 'assign7', 'assign8', 'total_messages', 'total_reactions', 'total_words']
    #print(keys)
    score = {} #.[2, 1, 4, 6]
    for k,v in ustats.items():
        w = [0,]
        if k not in ('Than', 'sphaero', 'Rob(ot)', 'Disco Rob', 'Arty'):
            for key in keys: # val in v.items():
                val = v.get(key, 0)
                if type(val) == int:
                    #print(w[0], val)
                    w[0] = w[0] + val
                    w.append(val)
                if type(val) == str:
                    if val == "completed":
                        w[0] = w[0] + 100
                        w.append(100)
                    else:
                        w.append(0)

            score[k] = w
            
    # sorteer dict op hoogste score w[0]
    res = {key: val for key, val in sorted(score.items(), key = lambda ele: ele[0][0])}
    #print(res.keys())
    labels = res.keys() # namen op de y as
    pos = range(len(res.keys()))
    #print(res.values())
    numbers = [0] * len(res.keys())
    prevy = [0] * len(res.keys())
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#b7cfbe']
    plt.rcParams["figure.figsize"] = (6,8)
    for x, col in zip(range(len(keys)), colors[:len(keys)]):
        for i,v in enumerate(res.values()):
            if x+1 < len(v):
                numbers[i] = v[x+1]
        #print(x, col, numbers)
        
        plt.barh(pos, numbers, left=prevy, color=col)
        prevy = [prevy[i] + numbers[i] for i in range(len(numbers))]#numbers.copy()

    plt.yticks(ticks=pos, labels=labels)
    handles = [plt.Rectangle((0,0),1,1, color=col) for col in colors]
    plt.legend(handles, keys)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    #plt.show()
    return buf

# assignment 1 : post screenshot
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

# assignment 3: ask for help challenge (in Help-help-helpdesk channel)
def require_assign3(msg):
    if msg.channel.name == "ask-for-help-challenge": # assignment channel, wrong channel to post question --> answer with hint
        return 2
    if (msg.channel.category_id == 917742829336428631): # d.dungeons category, including helpdesk channel
        user = require_user(msg.author)
        if user.get("assign3", "") == "completed":
            return 0
        user["assign3"] = "completed"
        update_user(msg.author, user)
        return 1

#assignment 4: give help proof screenshot
def require_assign4(msg):
    if msg.channel.name != "help-someone-or-a-group":
        return
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


#assignment 5: pdf presentation upload
def require_assign5(msg):
    if msg.channel.name != "your-presentation-week-1":
        return
    user = require_user(msg.author)
    if user.get("assign5", "") == "completed":
        return False
    if "http" in msg.content or ( len(msg.attachments) and msg.attachments[0].content_type.startswith("application/pdf") ):
        #user["assign5url"] = msg.attachments[0].url
        user["assign5"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign5"] = "incomplete"
        update_user(msg.author, user)

#assignment 6: faceswap proof screenshot
def require_assign6(msg):
    if msg.channel.name != "faceswap":
        return
    user = require_user(msg.author)
    if user.get("assign6", "") == "completed":
        return False
    if len(msg.attachments) and ( msg.attachments[0].content_type.startswith("video") or msg.attachments[0].content_type.startswith("image") ):
        user["assign6url"] = msg.attachments[0].url
        user["assign6"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign6"] = "incomplete"
        update_user(msg.author, user)

#assignment 7: play with Runway proof screenshot
def require_assign7(msg):
    if msg.channel.name != "play-with-runway-proof":
        return
    user = require_user(msg.author)
    if user.get("assign7", "") == "completed":
        return False
    if len(msg.attachments) and ( msg.attachments[0].content_type.startswith("video") or msg.attachments[0].content_type.startswith("image") ):
        user["assign7url"] = msg.attachments[0].url
        user["assign7"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign7"] = "incomplete"
        update_user(msg.author, user)

#assignment 8: link/pdf/docx or zip of end documentation
def require_assign8(msg):
    if msg.channel.name != "end-documentation":
        return
    user = require_user(msg.author)
    if user.get("assign8", "") == "completed":
        return False
    if "http" in msg.content or len(msg.attachments):
        #user["assign5url"] = msg.attachments[0].url
        user["assign8"] = "completed"
        update_user(msg.author, user)
        return True
    else:
        user["assign8"] = "incomplete"
        update_user(msg.author, user)


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
async def hiscore(ctx, *args):        
    print("generate chart for {}".format(args))
    if len(args) == 0:
        args = None
    img = bar_chart(args)
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
        reps = ['Hallo {}, misschien kun je beter om hulp vragen in een van de d.dungeons kanalen, zoals <#917742829529362476>?',
                'Goede post {}! Maar als het voor de "hulp-vraag-challenge" is, kun je die beter posten in de <#917742829529362476> (in de Dungeons)',
                'ja, okay, maar beste {} . . ., misschien kun je hulpvragen beter in een van de dungeons kanalen posten, zoals de  <#917742829529362476>?',
                'Great post {}, but . . ., if its a help question, you could better ask it in the dungeons? Then you might score a point!',
                'Rob likes your style {}, but if it is concerning a helpdesk question, you might better post in the HelpDesk (in the dungeons) ',
                'Wow, just wow {}. . .',
                'Denk je dat Rob(ot) slim genoeg is om hier wat mee te doen, {}?',
                'Wat denk je zelf, {}?',
                'Ja, maar wat denk je er zelf van, {}?',
                '{}! Wat leuk dat je hier post, hoe is het met je?',
                'I am afraid I can\'t do that, Dave, eh. . . {} ',
                'prachtig geformuleerd {}, maar ik snap er niks van. . . wie weet kunnen we het in het help-help-helpdesk kanaal proberen?  <#917742829529362476>',
                'Poeh, daar zeg je wat, {}. . . Zullen we het ergens in de Dungeons voortzetten? Daar is vast iemand die er (nog) beter antwoord op kan geven!',
                'Eeehhh...',
                'Just a minute {}, I\'m Computing (and working on) my best answer. . .',
                'Unknown variable {}. Who is {}? Who are you? Who is Rob? Who am I. . ?'
                ]
        await message.channel.send(random.choice(reps).format(message.author.name), reference=message)

    if require_assign4(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    if require_assign5(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    if require_assign6(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    if require_assign7(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    if require_assign8(message):
        emoji = '\N{White Heavy Check Mark}'
        await message.add_reaction(emoji)

    #print(message.content)
    if message.content.lower().startswith('hallo'):
        #emoji = '\N{Waving Hand Sign}'
        #await message.add_reaction(emoji)
        reps = ["Hello {}!","Ha {}, ook hallo!","Hoi {}, hoe is het?","Je klinkt enthousiast, {}! Zoek je een chatbot?"]
        rep = random.choice(reps)
        await message.channel.send(rep.format(message.author.name))

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
    #print(channel.members)
    for user in channel.members:
        print("channel {} member {}".format(channel.name, user))
        ustat = require_user(user)
        ustat["assign2"] = "completed"
        ustat["assign2channel"] = channel.name
        update_user(user, ustat)

@client.event
async def on_guild_channel_update(before, after):
    print("channel {} update".format(before))
    #print(before.members, after.members)
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
