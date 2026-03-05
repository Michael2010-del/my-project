import config
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3 

bot = telebot.TeleBot(config.API_TOKEN)

# Функция для инициализации базы данных
def init_database():
    """Создает необходимые таблицы, если их нет"""
    con = sqlite3.connect("project_games.db")
    cur = con.cursor()
    
    # Создаем таблицу для избранного
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            game_id INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, game_id)
        )
    """)
    
    con.commit()
    con.close()
    print(" База данных инициализирована")

# Инициализируем БД при запуске
init_database()

def send_info(bot, message, row):
    """Отправляет информацию об игре с учетом структуры таблицы"""
    
    # В твоей таблице поля:
    # 0 - Rank, 1 - Name, 2 - Platform, 3 - Year, 4 - Genre, 5 - Publisher,
    # 6 - NA_Sales, 7 - EU_Sales, 8 - JP_Sales, 9 - Other_Sales, 10 - Global_Sales
    
    info = f"""
📍 Название игры:   {row[1]}
📍 Год выпуска:      {row[3]}
📍 Платформа:        {row[2]}
📍 Жанр:             {row[4]}
📍 Издатель:         {row[5]}
📍 Продажи в мире:   {row[10]} миллионов

🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻
{row[1]} - это игра в жанре {row[4].lower()}, выпущенная в {row[3]} году для платформы {row[2]}. 
Издатель: {row[5]}. Продано {row[10]} миллионов копий по всему миру.
"""
    bot.send_message(message.chat.id, info, reply_markup=add_to_favorite(row[0]))

def add_to_favorite(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(" Добавить в избранное", callback_data=f'favorite_{id}'))
    return markup

def main_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/random'))
    markup.add(KeyboardButton('/favorites'))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("favorite"):
        game_id = call.data[call.data.find("_")+1:]
        user_id = call.from_user.id
        
        # Подключаемся к твоей БД
        con = sqlite3.connect("project_games.db")
        cur = con.cursor()
        
        # Проверяем, нет ли уже такой игры в избранном
        cur.execute("SELECT * FROM favorites WHERE user_id = ? AND game_id = ?", (user_id, game_id))
        existing = cur.fetchone()
        
        if existing:
            bot.answer_callback_query(call.id, " Эта игра уже в избранном!")
        else:
            # Добавляем в избранное
            cur.execute("INSERT INTO favorites (user_id, game_id) VALUES (?, ?)", (user_id, game_id))
            con.commit()
            bot.answer_callback_query(call.id, " Игра добавлена в избранное!")
        
        con.close()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """Привет! Добро пожаловать в лучший Game-Chat-Бот! 
Здесь ты можешь найти тысячи игр! 

Нажми /random чтобы получить случайную игру
Нажми /favorites чтобы посмотреть избранное
Или просто напиши название игры, и я попробую её найти!  """, reply_markup=main_markup())

@bot.message_handler(commands=['random'])
def random_game(message):
    con = sqlite3.connect("project_games.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM mytable ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    con.close()
    send_info(bot, message, row)

@bot.message_handler(commands=['favorites'])
def show_favorites(message):
    user_id = message.from_user.id
    con = sqlite3.connect("project_games.db")
    cur = con.cursor()
    
    # Получаем избранные игры
    cur.execute("""
        SELECT g.* FROM mytable g
        JOIN favorites f ON g.Rank = f.game_id
        WHERE f.user_id = ?
    """, (user_id,))
    
    favorites = cur.fetchall()
    con.close()
    
    if not favorites:
        bot.send_message(message.chat.id, "🥲 У тебя пока нет избранных игр")
        return
    
    text = " Твои избранные игры:\n\n"
    for i, game in enumerate(favorites, 1):
        text += f"{i}. {game[1]} ({game[3]}) - {game[10]} млн продаж\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: True)
def search_game(message):
    con = sqlite3.connect("project_games.db")
    cur = con.cursor()
    
    # Поиск по названию (без учета регистра)
    cur.execute("SELECT * FROM mytable WHERE LOWER(Name) LIKE ?", ('%' + message.text.lower() + '%',))
    rows = cur.fetchall()
    con.close()
    
    if rows:
        if len(rows) == 1:
            # Нашли одну игру
            bot.send_message(message.chat.id, " Конечно! Я знаю эту игру")
            send_info(bot, message, rows[0])
        else:
            # Нашли несколько игр
            bot.send_message(message.chat.id, f" Нашел {len(rows)} игр. Уточни название:")
            
            # Показываем первые 5
            text = ""
            for i, game in enumerate(rows[:5]):
                text += f"{i+1}. {game[1]} ({game[3]})\n"
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, " Я не знаю такой игры. Попробуй другое название")

if __name__ == "__main__":
    print(" Бот запущен...")
    bot.infinity_polling()