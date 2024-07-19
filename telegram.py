#!/usr/bin/env python3

import telethon
import json
import asyncio
import datetime

class Telegram():
    def __init__(self, json_config_file, json_data_file):
        with open(json_config_file, 'r') as json_file:
            config = json.load(json_file)
        self.config = config

        try:
            with open(json_data_file, 'r') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as error:
            with open(json_data_file, 'w') as json_file:
                json.dump({"chat_ids":[]}, json_file, indent=4)
                data = {"chat_ids":[]}
        self.json_data_file = json_data_file
        self.data = data
        
        self.client = telethon.TelegramClient('bot', self.config['api_id'], self.config['api_hash'])
            
    async def start(self):
        await self.client.start(bot_token=self.config['api_bottoken'])
        self.client.add_event_handler(self.message_handler, telethon.events.NewMessage(incoming=True))
        await self.client.connect()
            
    async def message_send_all_chats(self, message):
        for chat_id in self.data["chat_ids"]:
            await self.send_message(chat_id, message)
    
    async def message_handler(self, event):
        sender = await event.get_sender()
        print(f"""{str(datetime.datetime.now())}
Chat ID: {event.chat_id}, {sender.first_name} with ID: {sender.id} and username: {sender.username} spoken {sender.lang_code} wrote:
{event.message.raw_text}
""")
        # Work
        if(event.message.raw_text == "/help"):
            await self.send_message(event.chat_id, "Hi, I am ETIT course notifier bot and I am here to notify new ETIT courses!\n[Check me out!](https://github.com/gremirarunico/ETIT_TelegramBot_courses_notifier)")
        if(event.message.raw_text == "/start"):
            is_allowed = await self.is_user_admin_or_owner(event)
            if is_allowed:
                if self.add_chat_to_track(event.chat_id):
                    await self.send_message(event.chat_id, "Started tracking ETIT courses")
                else:
                    await self.send_message(event.chat_id, "Error starting tracking ETIT courses, maybe we are doint it yet?")
                
            else:
                await self.send_message(event.chat_id, "Can't start tracking ETIT courses, user has not superusers")

        if(event.message.raw_text == "/stop"):
            is_allowed = await self.is_user_admin_or_owner(event)
            if is_allowed:
                if self.del_chat_to_track(event.chat_id):
                    await self.send_message(event.chat_id, "Stopped tracking ETIT courses")
                else:
                    await self.send_message(event.chat_id, "Error stopping tracking ETIT courses, maybe we aren't doint it?")
            else:
                await self.send_message(event.chat_id, "Can't stop tracking ETIT courses, user has not superusers")
        """print(event.chat_id)
        print(sender.first_name)
        print(sender.id)
        print(sender.username)
        print(sender.lang_code)
        
        print(event.message)
        
        message = event.message
        
        print(message.media)
        print(message.date)
        
        print(event.raw_text)"""
        """if(event.photo):
            text = "A photo is sent"
        elif(event.audio):
            text = "An audio is sent"
        elif(event.voice):
            text = "An audio is voice"
        else:
            text = "A text is sent"
        print(text)
        await event.reply(text)"""
        
    async def send_message(self, to, content):
        #print(f"Send to {to}: {content}")
        await self.client.send_message(to, content)

    async def send_message_delay(self, to, content, delay):
        #print("Pre sleep")
        await asyncio.sleep(delay)
        #print("Post sleep")
        await self.client.send_message(to, content)

    async def is_user_admin_or_owner(self, event):
        try:
            permissions = await self.client.get_permissions(event.chat_id, event.sender_id)
            return((permissions.is_admin or permissions.is_creator) and not (permissions.is_banned))
        except ValueError: # we are in a chat, so
            return True

    def add_chat_to_track(self, chat_id):
        data = set(self.data["chat_ids"])
        
        lenght = len(data)
        data.add(chat_id)

        self.data["chat_ids"] = list(data)

        if(lenght == len(self.data["chat_ids"])):
            return False
        else:
            self.updateJson()
            return True

    def del_chat_to_track(self, chat_id):
        data = set(self.data["chat_ids"])
        
        try:
            data.remove(chat_id)
            self.data["chat_ids"] = list(data)
            self.updateJson()
            return True
        except KeyError:
            return False
            

    def updateJson(self):
        with open(self.json_data_file, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)