import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# ==================== НАСТРОЙКИ ====================

BOT_TOKEN = "8755825898:AAGqUoGs8YtOY3IZ_YMYMUHWkG5gk4GYjik"
ADMIN_IDS = [7034951533, 7444090752]

# ===================================================

# Инициализация БД
conn = sqlite3.connect('stats.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS messages
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     username TEXT,
     display_name TEXT,
     chat_id INTEGER,
     timestamp DATETIME)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS nicknames
    (user_id INTEGER PRIMARY KEY,
     custom_nick TEXT)''')
conn.commit()

# ==================== ФУНКЦИЯ ЭКРАНИРОВАНИЯ ====================

def escape_markdown(text):
    """Экранирует спецсимволы для Markdown V2"""
    if not text:
        return ""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_display_name(user_id, username, display_name):
    cursor.execute('SELECT custom_nick FROM nicknames WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    if username:
        return username
    if display_name:
        return display_name
    return "Пользователь"

def get_profile_link(user_id, username, display_name):
    name = get_display_name(user_id, username, display_name)
    name_escaped = escape_markdown(name)
    if username:
        return f"[{name_escaped}](https://t.me/{username})"
    else:
        return f"[{name_escaped}](tg://user?id={user_id})"

def get_period_dates(period):
    now = datetime.now()
    
    if period == 'day':
        since = now - timedelta(hours=24)
        until = now
        period_name = "за 24 часа"
        
    elif period == 'week':
        today = now.date()
        monday = today - timedelta(days=today.weekday())
        since = datetime.combine(monday, datetime.min.time())
        until = now
        monday_str = monday.strftime('%d.%m').replace('.', '\\.')
        today_str = today.strftime('%d.%m').replace('.', '\\.')
        period_name = f"за текущую неделю \\({monday_str} – {today_str}\\)"
        
    elif period == 'last_week':
        today = now.date()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        since = datetime.combine(last_monday, datetime.min.time())
        until = datetime.combine(last_sunday, datetime.max.time())
        monday_str = last_monday.strftime('%d.%m').replace('.', '\\.')
        sunday_str = last_sunday.strftime('%d.%m').replace('.', '\\.')
        period_name = f"за прошлую неделю \\({monday_str} – {sunday_str}\\)"
        
    elif period == 'all':
        since = datetime(2000, 1, 1)
        until = now
        period_name = "за всё время"
        
    else:
        since = now - timedelta(hours=24)
        until = now
        period_name = "за 24 часа"
    
    return since, until, period_name

def get_stats_data(since, until, chat_id):
    query = '''
        SELECT user_id, username, display_name, COUNT(*) as msg_count
        FROM messages
        WHERE timestamp BETWEEN ? AND ?
        AND chat_id = ?
        GROUP BY user_id
    '''
    cursor.execute(query, [since, until, chat_id])
    rows = cursor.fetchall()
    
    stats = []
    for user_id, username, display_name, count in rows:
        link = get_profile_link(user_id, username, display_name)
        stats.append({
            'user_id': user_id,
            'username': username,
            'link': link,
            'count': count
        })
    
    stats.sort(key=lambda x: x['count'], reverse=True)
    return stats

def format_stats_page(stats, page, per_page, period_name):
    total = len(stats)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    if total == 0:
        return f"📊 Нет сообщений {period_name}", 0, 0
    
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    lines = [f"📊 *Статистика {period_name}:*\n"]
    
    for i in range(start, end):
        stat = stats[i]
        lines.append(f"{i+1}\\. {stat['link']} — {stat['count']} сообщ\\.")
    
    lines.append(f"\n📄 Страница {page}/{total_pages}")
    
    return "\n".join(lines), page, total_pages

def get_keyboard(page, total_pages, period, chat_id):
    keyboard = []
    nav_row = []
    
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{period}_{page-1}_{chat_id}"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"page_{period}_{page+1}_{chat_id}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    
    return InlineKeyboardMarkup(keyboard)

# ==================== ОБРАБОТЧИКИ ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user = update.message.from_user
    chat_type = update.message.chat.type
    
    # ===== ЛИЧНЫЕ СООБЩЕНИЯ =====
    if chat_type == 'private':
        user_name = escape_markdown(user.full_name or "Пользователь")
        welcome_text = f"""👋 *Привет, {user_name}\\!*

Я — бот\\-статистик для групповых чатов Telegram\\.

📊 *Что я умею:*
• Считаю сообщения участников в группе
• Показываю топ по командам
• Поддерживаю кастомные ники
• Работаю с перевёрнутым восклицательным знаком ¡

📌 *Как меня добавить в группу:*
1\\. Нажмите на мой профиль
2\\. Выберите *"Добавить в группу"*
3\\. Выберите нужную группу
4\\. *Обязательно выдайте мне права администратора* с правом *"Чтение сообщений"*

⚡ *Команды в группе:*
`¡стата день` — статистика за 24 часа
`¡стата неделя` — за текущую неделю \\(пн–вс\\)
`¡стата прошлая неделя` — за прошлую неделю
`¡стата вся` — за всё время
`¡новый ник "Имя"` — установить псевдоним
`¡удали ник` — удалить псевдоним

❓ *Важно:* В личных сообщениях команды не работают — добавьте меня в группу\\!

Спасибо, что пользуетесь мной\\! 🚀"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )
        return
    
    # ===== ГРУППОВЫЕ СООБЩЕНИЯ =====
    if chat_type in ['group', 'supergroup']:
        # Запись сообщения в БД
        timestamp = datetime.now()
        cursor.execute('''
            INSERT INTO messages (user_id, username, display_name, chat_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.full_name, chat_id, timestamp))
        conn.commit()
        
        # Обработка команд с ¡ или i (если телефон заменил)
        first_char = message_text[0]
        if first_char in ['¡', 'i', 'I']:
            # Убираем первый символ и разбираем
            parts = message_text[1:].strip().split()
            if not parts:
                return
            
            cmd = parts[0].lower()
            
            # ¡стата ...
            if cmd in ['стата', 'статистика']:
                if len(parts) >= 2:
                    sub = parts[1].lower()
                    if sub in ['день', 'дня', 'day']:
                        await send_stats(update, context, 'day')
                    elif sub in ['неделя', 'неделю', 'week']:
                        await send_stats(update, context, 'week')
                    elif sub in ['прошлая', 'прошлую']:
                        await send_stats(update, context, 'last_week')
                    elif sub in ['вся', 'всё', 'все', 'all']:
                        await send_stats(update, context, 'all')
                    else:
                        await send_stats(update, context, 'day')
                else:
                    await send_stats(update, context, 'day')
            
            # ¡новый ник ... (сохраняем ОРИГИНАЛЬНЫЙ регистр из message_text)
            elif cmd in ['новый', 'ник']:
                # Ищем ник в оригинальном сообщении
                original_text = message_text[1:].strip()
                nick = None
                
                if cmd == 'новый' and len(parts) >= 3 and parts[1].lower() == 'ник':
                    # Берём всё после "новый ник"
                    nick = " ".join(original_text.split()[2:])
                elif cmd == 'ник' and len(parts) >= 2:
                    # Берём всё после "ник"
                    nick = " ".join(original_text.split()[1:])
                else:
                    nick = " ".join(original_text.split()[1:])
                
                # Убираем кавычки если есть
                nick = nick.strip('"\'')
                
                if nick:
                    # Сохраняем ОРИГИНАЛЬНЫЙ регистр!
                    cursor.execute('INSERT OR REPLACE INTO nicknames (user_id, custom_nick) VALUES (?, ?)',
                                   (user.id, nick))
                    conn.commit()
                    await update.message.reply_text(f"✅ Ник установлен: {nick}")
                else:
                    await update.message.reply_text('❌ Укажите ник: ¡новый ник "Ваше Имя"')
            
            # ¡удали ник
            elif cmd in ['удали', 'удалить'] and len(parts) >= 2 and parts[1].lower() == 'ник':
                cursor.execute('DELETE FROM nicknames WHERE user_id = ?', (user.id,))
                conn.commit()
                await update.message.reply_text("✅ Ник удалён")

async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, period):
    chat_id = update.effective_chat.id
    
    since, until, period_name = get_period_dates(period)
    stats = get_stats_data(since, until, chat_id)
    
    text, page, total_pages = format_stats_page(stats, 1, 10, period_name)
    
    if total_pages == 0:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return
    
    keyboard = get_keyboard(1, total_pages, period, chat_id)
    
    context.chat_data[f'stats_{period}'] = stats
    context.chat_data[f'period_name_{period}'] = period_name
    
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "close":
        await query.message.delete()
        return
    
    parts = query.data.split('_')
    if len(parts) >= 4 and parts[0] == 'page':
        period = parts[1]
        page = int(parts[2])
        original_chat_id = int(parts[3])
        
        stats = context.chat_data.get(f'stats_{period}')
        period_name = context.chat_data.get(f'period_name_{period}', '')
        
        if not stats:
            since, until, period_name = get_period_dates(period)
            stats = get_stats_data(since, until, original_chat_id)
        
        text, page, total_pages = format_stats_page(stats, page, 10, period_name)
        keyboard = get_keyboard(page, total_pages, period, original_chat_id)
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True
        )

# ==================== ЗАПУСК ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот запущен!")
    print("📋 Личка: инструкция")
    print("📋 Группа: сбор статистики и команды ¡стата")
    
    app.run_polling()

if __name__ == "__main__":
    main()
