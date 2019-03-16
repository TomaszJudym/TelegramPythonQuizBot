import json
import requests
import urllib
from dbhelper import DBHelper
from token import TOKEN

db = DBHelper()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

'''
download whole webpage at url
decode object as normal utf-8 text
and return it
'''


def get_url(url):
    response = requests.get(url) # get whole webpage under url
    content = response.content.decode("utf8") # content return page in binary form, we decode it 2 utf8
    return content                            # return it as string

'''
json loads() deserializes str or unicode
instance (containing json) to python object using
conversion table which can be found in documentation
'''


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

'''
getUpdates at the end of our bot URL shows
messages received by bot in json format
'''


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

'''
function takes json object which may be interpreted
as map of maps of maps of arrays...
-so under "result" is main array of all messages in json format
-we are indexing from 0, so we make size - 1 in last_update
-text is in result array in [last update] index, in "message" array...
you get the idea
So in this jungle, we find payload (text) and chat_id from which
message came and we return this pair.
'''


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    payload = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return payload, chat_id


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text) # quote plus gets rid of special characters escaping 'em
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id) # send message to our bot
    if reply_markup:    # reply markup may be additionaly keyboard to create
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_updates(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        if text == "/done":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        elif text == "/start":
            send_message("Welcome to personal To Do List. /done -> to remove items", chat)
        elif text.startswith("/"):
            #we dont have that command : ///
            continue
        elif text in items:
            db.delete_item(text, chat)
            items = db.get_items(chat)
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, keyboard)
        else:
            db.add_item(text, chat)
            print("User {} has {} items ".format(chat, db.get_amount_of_tasks_for_owner(chat)))
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message(message, chat)

'''
those stupid braces around [item] are to indicate,
that it's list, so for keyboard it's an entire row!
'''


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        # result may not be in updates if all requests are processed,
        # and page is refreshed, without this condition, we have crash
        if "result" in updates and len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        print("receiving messages...")


if __name__ == '__main__':
    main()
