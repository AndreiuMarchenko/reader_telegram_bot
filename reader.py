import asyncio
import re
from telethon.sync import TelegramClient, events
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

async def filters(event):
    matches = re.findall(r'@(\w+)', event.message.text)
    number = re.findall(r'(?:\+380|066|050|093|099|073|095|063|063|097|096)\w+', event.message.text)

    return matches, number

async def handle_channel(event, tracked_posts_sheet, blacklist_sheet, post_name, mention, number_phone, is_channel):

    current_date = datetime.now().strftime("%Y-%m-%d")

    #check black_list
    blacklisted_usernames = blacklist_sheet.col_values(1)
    if str(mention) in blacklisted_usernames:
        print(f"Повідомлення від блек-листа: {mention}")
        return
    
    if is_channel:
        post_link = f"https://t.me/c/{post_name}/{event.message.id}"
        username = event.chat.id
    else:
        post_link = f"https://t.me/{post_name}/{event.message.id}"
        username = event.chat.username

    post_details = [
        current_date,
        f"@{str(mention)}" if mention else "Немає згадок замовника",
        f"{number_phone}" if number_phone else "Немає номеру телефону",
        f"{post_link}", f"{username}"
    ]

    tracked_posts_sheet.append_rows([post_details])

def get_blacklist_sheet(gc, google_sheets_url, blacklist_sheet_name):
    try:
        blacklist_sheet = gc.open_by_url(google_sheets_url).worksheet(blacklist_sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        gc.open_by_url(google_sheets_url).add_worksheet(title=blacklist_sheet_name, rows=1, cols=1)
        blacklist_sheet = gc.open_by_url(google_sheets_url).worksheet(blacklist_sheet_name)

    return blacklist_sheet

async def closed_channel_handler(event, tracked_posts_sheet, blacklist_sheet, link, matches, number):
    post_name = link
    mention = matches[0] if matches else None
    number_phone = number[0] if number else None

    await handle_channel(event, tracked_posts_sheet, blacklist_sheet, post_name, mention, number_phone, is_channel=True)

async def open_channel_handler(event, tracked_posts_sheet, blacklist_sheet,  matches, number):
    post_name = event.chat.username
    mention = matches[0] if matches else None
    number_phone = number[0] if number else None

    await handle_channel(event, tracked_posts_sheet, blacklist_sheet, post_name, mention, number_phone, is_channel=False)

async def main():
    api_id = '20683998'
    api_hash = '5ac53baa5f37fda3a03e172d3ccba45d'

    gc = gspread.service_account(filename='teltgram_bot_ads/ads_maneger/sylvan-overview-408508-2f1a257b96de.json')
    google_sheets_url = 'https://docs.google.com/spreadsheets/d/1k953noZq8hTZLItKZLJtDZWPPJ0wLkX2Y6zlHJZiC3w/edit?usp=sharing'
    tracked_posts_sheet_name = 'TrackedPosts'
    advertisers_sheet_name = 'Advertisers'
    blacklist_sheet_name = 'BlackList'
    blacklist_sheet = get_blacklist_sheet(gc, google_sheets_url, blacklist_sheet_name)

    
    try:
        tracked_posts_sheet = gc.open_by_url(google_sheets_url).worksheet(tracked_posts_sheet_name)
        advertisers_sheet = gc.open_by_url(google_sheets_url).worksheet(advertisers_sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        gc.open_by_url(google_sheets_url).add_worksheet(title=tracked_posts_sheet_name, rows=1, cols=1)
        tracked_posts_sheet = gc.open_by_url(google_sheets_url).worksheet(tracked_posts_sheet_name)

    # Init channel names
    

    async with TelegramClient('userbot', api_id, api_hash) as client:
        @client.on(events.NewMessage)
        
        async def handle_new_message(event):


            channel_names = advertisers_sheet.col_values(1)


            if event.chat and event.chat_id:
                identifier = event.chat_id
                iden = str(identifier).lstrip('-100')
                sum_id = len(iden)
                link = None
                if sum_id == 9:
                    link = "1" + iden
                    

                if link in channel_names or iden in channel_names:
                    matches, number = await filters(event)
                    if matches or number:
                        await closed_channel_handler(event, tracked_posts_sheet, blacklist_sheet, link, matches, number)
                elif event.chat.username in channel_names:
                    matches, number = await filters(event)
                    if matches or number:
                        await open_channel_handler(event, tracked_posts_sheet, blacklist_sheet, matches, number)
                else:
                    # Нічого не записувати, оскільки не виконано жодної з умов
                    pass



        print("Userbot запущено. Очікування нових повідомлень...")
        await client.run_until_disconnected()

asyncio.run(main())
