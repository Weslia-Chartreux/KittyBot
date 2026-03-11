import os
import datetime
import random
import requests
import logging
from telebot import TeleBot, types

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создаём папку для логов, если её нет
log_dir = 'logging'
os.makedirs(log_dir, exist_ok=True)

# Обработчик для файла: пишет всё (DEBUG и выше) в папку logging
file_handler = logging.FileHandler(os.path.join(log_dir, 'bot.log'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Обработчик для консоли: пишет только INFO и выше
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Настраиваем логирование для библиотек
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

auth_token = os.getenv('TOKEN')
bot = TeleBot(token=auth_token)

CAT_API_URL = 'https://api.thecatapi.com/v1/images/search'


@bot.message_handler(commands=['start'])
def wake_up(message):
    chat = message.chat
    name = chat.first_name
    logger.info(f'Пользователь {name} (id: {chat.id}) запустил бота командой /start')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        types.KeyboardButton('Который час?'),
        types.KeyboardButton('Случайный котик'),
    )
    keyboard.row(
        types.KeyboardButton('/random_digit'),
    )

    bot.send_message(
        chat_id=chat.id,
        text=f'Спасибо, что вы включили меня, {name}!',
        reply_markup=keyboard,
    )
    logger.debug(f'Отправлено приветствие пользователю {chat.id}')


@bot.message_handler(commands=['random_digit'])
def random_digit_command(message):
    chat_id = message.chat.id
    logger.info(f'Команда /random_digit от пользователя {chat_id}')
    digit = random.randint(0, 9)
    bot.send_message(chat_id, f'Случайная цифра: {digit}')
    logger.debug(f'Сгенерирована цифра {digit} для {chat_id}')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat = message.chat
    text = message.text.strip()
    logger.info(f'Получено текстовое сообщение от {chat.id}: "{text}"')

    if text == 'Который час?':
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        bot.send_message(chat.id, f'Текущее время: {now}')
        logger.debug(f'Отправлено время {now} пользователю {chat.id}')

    elif text == 'Случайный котик':
        logger.debug(f'Запрос котика для {chat.id}')
        try:
            response = requests.get(CAT_API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            cat_url = data[0].get('url')
            if cat_url:
                bot.send_photo(chat.id, cat_url)
                logger.info(f'Котик отправлен пользователю {chat.id}, URL: {cat_url}')
            else:
                bot.send_message(chat.id, 'Не удалось получить ссылку на котика.')
                logger.warning(f'Пустой URL котика для {chat.id}')
        except requests.exceptions.RequestException as e:
            bot.send_message(chat.id, f'Ошибка при запросе к API: {e}')
            logger.error(f'Ошибка запроса к API котиков для {chat.id}: {e}', exc_info=True)
        except (KeyError, IndexError) as e:
            bot.send_message(chat.id, 'Неожиданный формат ответа от API.')
            logger.error(f'Ошибка парсинга ответа API для {chat.id}: {e}', exc_info=True)

    else:
        bot.send_message(chat.id, 'Привет, я KittyBot! Используй кнопки для команд.')
        logger.debug(f'Неизвестная команда от {chat.id}: "{text}"')


def main():
    logger.info('Бот запущен и начинает polling')
    try:
        bot.polling()
    except Exception as e:
        logger.critical(f'Критическая ошибка в polling: {e}', exc_info=True)
    finally:
        logger.info('Бот остановлен')


if __name__ == '__main__':
    main()
