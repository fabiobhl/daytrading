import discord
import discord_cred
from concurrent import futures

def send(message_dict, token, channel_id):
    #check if dictionary is empty
    if not message_dict:
        return 

    #create the client
    client = discord.Client()

    #main function
    async def main(message_dict):
        #wait for client to be ready
        await client.wait_until_ready()
        channel = client.get_channel(channel_id)

        #send all messages
        for key in message_dict:
            #create the message
            message = f"{key}: {message_dict[key][0]}"
            for i in range(1, len(message_dict[key])):
                message += f"\n {message_dict[key][i]}"
            
            await channel.send(message)

        #log out
        await client.logout()

    #run the bot
    client.loop.create_task(main(message_dict))
    client.run(token)