import discord

TOKEN = ""
GUILD = ""

client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    
    if message.content.startswith('!hello'):
        response = "hello world"
        await message.channel.send(response)
    
    # Reply with !hey
    if message.content.startswith('!hey'):
        msg = 'Hello {0.author.mention}'.format(message)
        await message.channel.send(msg)
        
    # Reply and file with !mg
    if message.content.startswith('!mg'):
        #msg = 'Hello {0.author.mention}'.format(message)
        await message.channel.send('Hello', file=discord.File('tophat.png'))


client.run(TOKEN)
