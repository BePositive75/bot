import telebot
import re
import requests
import os

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = os.environ['BOT_TOKEN']
ALLOWED_USERS_FILE = "allow.txt"

bot = telebot.TeleBot(BOT_TOKEN)


def add_allowed_user(user_id):
  with open(ALLOWED_USERS_FILE, "a") as file:
    file.write(str(user_id) + "\n")


def is_user_allowed(user_id):
  with open(ALLOWED_USERS_FILE, "r") as file:
    allowed_users = file.read().splitlines()
  return str(user_id) in allowed_users


def send_response_message(chat_id, result_message):
  bot.send_chat_action(chat_id, 'typing')
  bot.send_message(chat_id, result_message)


@bot.message_handler(commands=['start'])
def handle_start(message):
  user_id = message.from_user.id
  if not is_user_allowed(user_id):
    add_allowed_user(user_id)
    welcome_message = f"Hey, {message.from_user.first_name}, welcome to AAP DLE (Drive Link Extractor). Just send me the URL, and I will give you the drive link."
    bot.reply_to(message, welcome_message)
  else:
    bot.reply_to(
        message,
        "Welcome back! Just send me the URL, and I will give you the drive link."
    )


@bot.message_handler(commands=['users'])
def handle_users_command(message):
  if is_user_allowed(message.from_user.id):
    with open(ALLOWED_USERS_FILE, "r") as file:
      allowed_users = file.read().splitlines()

    users_message = "List of allowed users:\n"
    for user_id in allowed_users:
      try:
        user_info = bot.get_chat(int(user_id))
        users_message += f"Name: {user_info.first_name}\nUser ID: {user_info.id}\n\n"
      except telebot.apihelper.ApiTelegramException:
        # Handle the case when the user cannot be retrieved
        users_message += f"User ID: {user_id} (unable to retrieve user info)\n\n"

    send_response_message(message.from_user.id, users_message)
  else:
    bot.reply_to(message, "You are not allowed to use this command.")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
  user_id = message.from_user.id

  # Show typing status
  bot.send_chat_action(user_id, 'typing')

  numbers = re.findall(r'\d+', message.text)
  if numbers:
    for number in numbers:
      url = "https://aapathshala.com/list-g-files"
      params = {"file_id": number}
      response = requests.get(url, params=params)
      if response.status_code == 200:
        data = response.json()
        drive_urls = [entry["webViewLink"] for entry in data]
        names = [entry["name"] for entry in data]
        result = list(zip(names, drive_urls))

        result_message = "\n \nHere is the Links  👇\n\n"
        for name, drive_url in result:
          result_message += f"✅ {name}\n {drive_url}\n\n"

        send_response_message(user_id, result_message)

      else:
        result_text = f"Error: {response.status_code}, {response.text}\n"
        bot.send_message(user_id, result_text)  # Send the error message
  else:
    bot.reply_to(message, "Enter a valid URL.")


if __name__ == '__main__':
  bot.polling()
