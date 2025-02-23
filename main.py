import logging
import datetime
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CommandHandler
import requests
from random import randint, choice
from data.users import User
from data.db_session import global_init
from data import db_session
from settings import TOKEN, API_KEY


# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

WEEK_DAYS = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']

pictures = ['https://mobimg.b-cdn.net/v3/fetch/6d/6d542f0e7cbf4d48d08f8b50e5cefea5.jpeg',
            'https://pm1.narvii.com/7683/ff931311be74708aa61260b163bf9fcbc5d13f3er1-1080-1350v2_hq.jpg',
            'https://trikky.ru/wp-content/blogs.dir/1/files/2021/02/23/ejvs1fhwaaiembx.jpg',
            'https://sub-cult.ru/images/2016/literatura/hjvjhvjhvjh.jpg',
            'https://i.pinimg.com/originals/ad/a6/5e/ada65e929b7f8a40d44bd2c2224e5cc3.jpg',
            'https://p0.pxfuel.com/preview/471/474/517/black-books-brown-clocks.jpg',
            'https://i.pinimg.com/originals/d5/50/b8/d550b854441bf461b0a208f648df8f46.jpg',
            'https://i.pinimg.com/originals/a9/3a/57/a93a570d1a2332f27f42f7ed4f394f1e.jpg',
            'https://i.pinimg.com/originals/b1/c9/d9/b1c9d95ed6656ca3a2dbbee05e5ab718.jpg',
            'https://i.pinimg.com/originals/a7/bc/9d/a7bc9d5aad9c2bf511c3a76aef1d8ec6.jpg',
            'https://i.pinimg.com/originals/55/34/a8/5534a89f14db8b481552059e2b5208e2.jpg']


def random_book(word):
    response = requests.get("http://openlibrary.org/search.json?q=" + word)
    if response:
        json_response = response.json()
        try:
            a = json_response['docs'][randint(0, len(json_response['docs']) - 1)]
            authors = ''
            try:
                authors = '\nАвторы: ' + ', '.join(a['author_name'])
            except:
                pass
            return 'Название: ' + a['title'] + authors
        except:
            return 'Не найдено'


def id(update):
    user = update.message.from_user
    return user['id']


def find_2(update, context):
    word = update.message.text
    update.message.reply_text(random_book(word))
    return ConversationHandler.END


def stop(update, context):
    return ConversationHandler.END


def start(update, context):
    update.message.reply_text(
        "Привет! Я Альбус, бот-библиотекарь. "
        "Чтобы узнать мои возможности, пропиши /help", reply_markup=k())


def help(update, context):
    update.message.reply_text(
        "На данный момент я могу:\n"
        "Найти книгу по названию - /bookname\n"
        "Найти книги определённого автора - /writerbooks\n"
        "Найти книгу по жанру- /genrebooks\n"
        "Познакомиться с тобой - /friend\n"
        "Установить читательский будильник - /reader_clocks\n"
        "Удалить читательский будильник - /unset\n"
        "Сказать текущее время - /time\n"
        "Сказать текущую дату - /date\n"
        "Сказать, какой сегодня день недели - /days\n"
        "Вдохновляющая на чтение картинка - /photo")


def days(update, context):
    update.message.reply_text(f'Сегодняшний день недели - {WEEK_DAYS[datetime.datetime.today().weekday()]}')


def pphoto(update, context):
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=choice(pictures))


def friend(update, context):
    id_user = id(update)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter((User.telegramm_id == id_user)).all()
    if not user:
        update.message.reply_text(
            "Давай знакомиться, странник! Как я могу называть тебя?")
        return 4
    else:
        update.message.reply_text(f'Кажется, мы уже знакомы, {user[0].name}')


def bookname(update, context):
    update.message.reply_text(
        "Как называется книга, которую ты хочешь найти?")
    return 1


def writerbooks(update, context):
    update.message.reply_text(
        "Книги какого автора ты бы хотел найти?")
    return 2


def genrebooks(update, context):
    update.message.reply_text(
        "Книги какого жанра ты бы хотел найти?")
    return 3


def find_libraries(update, context):
    loc = update.message.location
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = API_KEY

    address_ll = f'{str(loc["longitude"])},{str(loc["latitude"])}'

    search_params = {
        "apikey": api_key,
        "text": "библиотека",
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz",
        "results": "5"
    }

    response = requests.get(search_api_server, params=search_params)
    json_response = response.json()
    if not json_response['features']:
        update.message.reply_text('Не найдено библиотек рядом')
    else:
        update.message.reply_text('Ближайшие к вам библиотеки:')
        for organization in json_response["features"]:
            # Название организации.
            org_name = organization["properties"]["CompanyMetaData"]["name"]
            # Адрес организации.
            org_address = organization["properties"]["CompanyMetaData"]["address"]

            update.message.reply_text(f'{org_address} \n{org_name}')


def k():
    lb = KeyboardButton('Найти ближайшую библиотеку', request_location=True)
    return ReplyKeyboardMarkup([[lb]], resize_keyboard=True)


def time_config(time):
    if len(time) != 8:
        return 'Неверный формат, попробуйте снова'
    else:
        if int(time[0:2]) > 23:
            return 'Неверный формат часов, попробуйте снова'
        elif int(time[3:5]) > 59:
            return 'Неверный формат минут, попробуйте снова'
        elif int(time[6:8]) > 59:
            return 'Неверный формат секунд, попробуйте снова'
        else:
            return 'ok'


def time(update, context):
    update.message.reply_text(
        f"Текущее время {datetime.datetime.today().strftime('%H:%M')}")


def date(update, context):
    update.message.reply_text(
        f"Текущая дата {datetime.datetime.today().date()}")


def first_response(update, context):
    bookk = update.message.text
    book_str = '%20'.join(bookk.split())
    update.message.reply_text(
        f"Кажется, эти книги могут Вам подойти: https://search.rsl.ru/ru/search#q={book_str}")
    return ConversationHandler.END


def second_response(update, context):
    # Это ответ на первый вопрос.
    # Мы можем использовать его во втором вопросе.
    authorr = update.message.text
    author_str = '%20'.join(authorr.split())
    update.message.reply_text(
        f"Работы Вашего автора: https://search.rsl.ru/ru/search#q={author_str}")
    return ConversationHandler.END


def four_response(update, context):
    print(1)
    db_sess = db_session.create_session()
    user_name = update.message.text
    user = User()
    user.telegramm_id = id(update)
    user.name = user_name
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text(f'Приятно познакомиться, {user_name}')
    return ConversationHandler.END


def unset(update, context):
    """Удаляет задачу, если пользователь передумал"""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Будильник отменен!' if job_removed else 'У вас нет активных будильников'
    update.message.reply_text(text)


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def task(context):
    job = context.job
    context.bot.send_message(job.context, text='Кажется, самое время почитать!')


def set_timer(update, context):
    chat_id = update.message.chat_id
    try:
        configurates = time_config(context.args[0])
        if configurates != 'ok':
            update.message.reply_text(configurates)
            update.message.reply_text('Введите заново')
            return
        clock_hours = int(context.args[0][0:2])
        clock_minutes = int(context.args[0][3:5])
        clock_seconds = int(context.args[0][6:8])
        time_now = datetime.datetime.now()
        due = abs(clock_seconds + clock_minutes * 60 + clock_hours * 60 * 60 -
                  (time_now.second + time_now.minute * 60 + time_now.hour * 60 * 60))
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(task, due, context=chat_id, name=str(chat_id))

        text = f'Будильник поставлен на время {context.args[0]}'
        if job_removed:
            text += ' Старая задача удалена.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Использование: /reader_clocks <часы:минуты:секунды>')


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("time", time))
    dp.add_handler(CommandHandler("date", date))
    dp.add_handler(CommandHandler("days", days))
    dp.add_handler(CommandHandler("photo", pphoto))
    dp.add_handler(MessageHandler(Filters.location, find_libraries))
    dp.add_handler(CommandHandler("reader_clocks", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset,
                                  pass_chat_data=True)
                   )
    conv_handler_3 = ConversationHandler(
        entry_points=[CommandHandler('genrebooks', genrebooks)],
        states={
            3: [MessageHandler(Filters.text & ~Filters.command, find_2, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler_3)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('bookname', bookname)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, first_response)],
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler)

    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('writerbooks', writerbooks)],

        states={
            2: [MessageHandler(Filters.text & ~Filters.command, second_response)],
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler2)

    conv_handler_4 = ConversationHandler(
        entry_points=[CommandHandler('friend', friend)],
        states={
            4: [MessageHandler(Filters.text & ~Filters.command, four_response)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler_4)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    global_init('db/user.sqlite')
    main()