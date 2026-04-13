import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

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

def get_display_name(user_id, username, display_name):
    """Получить отображаемое имя (псевдоним или реальное)"""
    cursor.execute('SELECT custom_nick FROM nicknames WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return username or display_name

def get_period_dates(period):
    """Получить начальную и конечную дату для периода"""
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
    """Получить статистику за период"""
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
    
    # Сортировка по количеству сообщений (по убыванию)
    stats.sort(key=lambda x: x['count'], reverse=True)
    return stats

def format_stats_page(stats, page, per_page, period_name):
    """Форматировать страницу статистики"""
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
    
    lines.append(f"\nСтраница {page}/{total_pages}")
    
    return "\n".join(lines), page, total_pages

def get_keyboard(page, total_pages, period, chat_id):
    """Создать клавиатуру с кнопками навигации"""
    keyboard = []
    row = []
    
    if page > 1:
        row.append(InlineKeyboardButton("🠐 Назад", callback_data=f"page_{period}_{page-1}_{chat_id}"))
    
    if page < total_pages:
        row.append(InlineKeyboardButton("Вперёд ➔", callback_data=f"page_{period}_{page+1}_{chat_id}"))
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    
    return InlineKeyboardMarkup(keyboard)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пассивный трекинг всех сообщений"""
    if update.message and update.message.from_user and update.message.chat.type in ['group', 'supergroup']:
        user = update.message.from_user
        timestamp = datetime.now()
        
        cursor.execute('''
            INSERT INTO messages (user_id, username, display_name, chat_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.full_name, update.message.chat_id, timestamp))
        conn.commit()

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
    
    # Сохраняем данные в context для callback
    context.chat_data[f'stats_{period}'] = stats
    context.chat_data[f'period_name_{period}'] = period_name
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def stats_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, 'day')

async def stats_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, 'week')

async def stats_last_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, 'last_week')

async def stats_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update, context, 'all')

async def set_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить псевдоним"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ник: ¡новый ник \"Ваш ник\"")
        return
    
    user_id = update.message.from_user.id
    nick = " ".join(context.args)
    
    cursor.execute('INSERT OR REPLACE INTO nicknames (user_id, custom_nick) VALUES (?, ?)',
                   (user_id, nick))
    conn.commit()
    await update.message.reply_text(f"✅ Ник установлен: {nick}")

async def delete_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить псевдоним"""
    user_id = update.message.from_user.id
    cursor.execute('DELETE FROM nicknames WHERE user_id = ?', (user_id,))
    conn.commit()
    await update.message.reply_text("✅ Ник удалён, используется реальное имя")

# ==================== ОБРАБОТЧИК КНОПОК ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "close":
        await query.message.delete()
        return
    
    # Разбираем callback_data: page_week_2_123456789
    parts = data.split('_')
    if len(parts) >= 4 and parts[0] == 'page':
        period = parts[1]
        page = int(parts[2])
        original_chat_id = int(parts[3])
        
        # Проверяем, что кнопку нажал тот же пользователь в том же чате
        if query.message.chat_id != original_chat_id:
            return
        
        # Получаем сохранённые данные
        stats = context.chat_data.get(f'stats_{period}')
        period_name = context.chat_data.get(f'period_name_{period}', '')
        
        if not stats:
            # Если данные потеряны, пересчитываем
            since, until, period_name = get_period_dates(period)
            stats = get_stats_data(since, until, original_chat_id)
            context.chat_data[f'stats_{period}'] = stats
            context.chat_data[f'period_name_{period}'] = period_name
        
        text, current_page, total_pages = format_stats_page(stats, page, 10, period_name)
        keyboard = get_keyboard(page, total_pages, period, original_chat_id)
        
        await query.edit_message_text(text, reply_markup=keyboard)

# ==================== ЗАПУСК БОТА ====================

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError("Укажите BOT_TOKEN в переменных окружения")
    
    app = Application.builder().token(token).build()
    
    # Команды статистики
    app.add_handler(CommandHandler("стата", stats_day))
    app.add_handler(CommandHandler("стата_день", stats_day))
    app.add_handler(CommandHandler("стата_неделя", stats_week))
    app.add_handler(CommandHandler("стата_вся", stats_all))
    app.add_handler(CommandHandler("стата_прошлая_неделя", stats_last_week))
    
    # Управление никами
    app.add_handler(CommandHandler("новый_ник", set_nick))
    app.add_handler(CommandHandler("удали_ник", delete_nick))
    
    # Трекинг сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    
    # Обработка кнопок
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
