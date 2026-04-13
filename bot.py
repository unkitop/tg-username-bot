import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_display_name(user_id, username, display_name):
    cursor.execute('SELECT custom_nick FROM nicknames WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return username or display_name

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
        period_name = f"за текущую неделю ({monday.strftime('%d.%m')} – {today.strftime('%d.%m')})"
    elif period == 'last_week':
        today = now.date()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        since = datetime.combine(last_monday, datetime.min.time())
        until = datetime.combine(last_sunday, datetime.max.time())
        period_name = f"за прошлую неделю ({last_monday.strftime('%d.%m')} – {last_sunday.strftime('%d.%m')})"
    elif period == 'all':
        since = datetime(2000, 1, 1)
        until = now
        period_name = "за всё время"
    else:
        since = now - timedelta(hours=24)
        until = now
        period_name = "за 24 часа"
    
    return since, until, period_name

def get_stats_data(since, until, chat_id=None):
    query = '''
        SELECT user_id, username, display_name, COUNT(*) as msg_count
        FROM messages
        WHERE timestamp BETWEEN ? AND ?
    '''
    params = [since, until]
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    stats = []
    for user_id, username, display_name, count in rows:
        name = get_display_name(user_id, username, display_name)
        stats.append({
            'user_id': user_id,
            'name': name,
            'username': username,
            'count': count
        })
    
    stats.sort(key=lambda x: x['count'], reverse=True)
    return stats

def format_stats_page(stats, page, per_page, period_name):
    total = len(stats)
    total_pages = (total + per_page - 1) // per_page
    
    if total == 0:
        return f"📊 Нет сообщений {period_name}", 0, 0
    
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    lines = [f"📊 Статистика {period_name}:\n"]
    
    for i in range(start, end):
        stat = stats[i]
        lines.append(f"{i+1}. {stat['name']} — {stat['count']} сообщ.")
    
    lines.append(f"\n📄 Страница {page}/{total_pages}")
    
    return "\n".join(lines), page, total_pages

def get_keyboard(page, total_pages, period, chat_id):
    keyboard = []
    row = []
    
    if page > 1:
        row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{period}_{page-1}_{chat_id}"))
    
    if page < total_pages:
        row.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"page_{period}_{page+1}_{chat_id}"))
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    
    return InlineKeyboardMarkup(keyboard)

# ==================== ОБРАБОТЧИКИ СООБЩЕНИЙ ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    message_text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id
    user = update.message.from_user
    
    # Сначала записываем сообщение в статистику (если это группа)
    if update.message.chat.type in ['group', 'supergroup']:
        timestamp = datetime.now()
        cursor.execute('''
            INSERT INTO messages (user_id, username, display_name, chat_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.full_name, chat_id, timestamp))
        conn.commit()
    
    # Проверяем команды с ¡
    if message_text.startswith('¡'):
        # Убираем ¡ и разбиваем на части
        command_text = message_text[1:].strip()
        parts = command_text.split()
        
        if not parts:
            return
        
        cmd = parts[0]
        
        # ¡стата день
        if cmd in ['стата', 'статистика']:
            if len(parts) >= 2:
                subcmd = parts[1]
                if subcmd in ['день', 'day']:
                    await send_stats(update, context, 'day')
                elif subcmd in ['неделя', 'неделю', 'week']:
                    await send_stats(update, context, 'week')
                elif subcmd in ['прошлая', 'прошлую'] and len(parts) >= 3 and parts[2] in ['неделя', 'неделю']:
                    await send_stats(update, context, 'last_week')
                elif subcmd in ['вся', 'всё', 'all']:
                    await send_stats(update, context, 'all')
                else:
                    # По умолчанию - день
                    await send_stats(update, context, 'day')
            else:
                # Просто "¡стата" - показываем день
                await send_stats(update, context, 'day')
        
        # ¡новый ник "Имя"
        elif cmd in ['новый', 'ник', 'новый_ник']:
            # Ищем ник в кавычках или все слова после команды
            if 'ник' in cmd and len(parts) >= 2:
                nick_part = " ".join(parts[1:])
            elif len(parts) >= 3 and parts[1] == 'ник':
                nick_part = " ".join(parts[2:])
            else:
                nick_part = " ".join(parts[1:])
            
            # Убираем кавычки если есть
            nick = nick_part.strip('"\'')
            
            if nick:
                cursor.execute('INSERT OR REPLACE INTO nicknames (user_id, custom_nick) VALUES (?, ?)',
                               (user.id, nick))
                conn.commit()
                await update.message.reply_text(f"✅ Ник установлен: {nick}")
            else:
                await update.message.reply_text('❌ Укажите ник: ¡новый ник "Ваше Имя"')
        
        # ¡удали ник
        elif cmd in ['удали', 'удалить'] and len(parts) >= 2 and parts[1] == 'ник':
            cursor.execute('DELETE FROM nicknames WHERE user_id = ?', (user.id,))
            conn.commit()
            await update.message.reply_text("✅ Ник удалён, используется реальное имя")

async def send_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, period):
    """Отправить статистику с кнопками"""
    chat_id = update.effective_chat.id
    
    since, until, period_name = get_period_dates(period)
    stats = get_stats_data(since, until, chat_id)
    
    text, page, total_pages = format_stats_page(stats, 1, 10, period_name)
    
    if total_pages == 0:
        await update.message.reply_text(text)
        return
    
    keyboard = get_keyboard(1, total_pages, period, chat_id)
    
    context.chat_data[f'stats_{period}'] = stats
    context.chat_data[f'period_name_{period}'] = period_name
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "close":
        await query.message.delete()
        return
    
    parts = data.split('_')
    if len(parts) >= 4 and parts[0] == 'page':
        period = parts[1]
        page = int(parts[2])
        original_chat_id = int(parts[3])
        
        if query.message.chat_id != original_chat_id:
            return
        
        stats = context.chat_data.get(f'stats_{period}')
        period_name = context.chat_data.get(f'period_name_{period}', '')
        
        if not stats:
            since, until, period_name = get_period_dates(period)
            stats = get_stats_data(since, until, original_chat_id)
            context.chat_data[f'stats_{period}'] = stats
            context.chat_data[f'period_name_{period}'] = period_name
        
        text, current_page, total_pages = format_stats_page(stats, page, 10, period_name)
        keyboard = get_keyboard(page, total_pages, period, original_chat_id)
        
        await query.edit_message_text(text, reply_markup=keyboard)

# ==================== ЗАПУСК БОТА ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик всех текстовых сообщений (ловит ¡команды)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот запущен!")
    print("📋 Доступные команды в чате:")
    print("   ¡стата день - статистика за 24 часа")
    print("   ¡стата неделя - статистика за текущую неделю")
    print("   ¡стата прошлая неделя - статистика за прошлую неделю")
    print("   ¡стата вся - статистика за всё время")
    print('   ¡новый ник "Имя" - установить псевдоним')
    print("   ¡удали ник - удалить псевдоним")
    print(f"👑 Администраторы: {ADMIN_IDS}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
