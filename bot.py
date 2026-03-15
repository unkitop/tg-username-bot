#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import time

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8792343001:AAFsJpRWHvfNw8YCdbAuETosfGYqPfzD_zQ"
ADMIN_ID = 7444090752
# =======================

WAITING_FOR_PRICE = 1

# ==== ТВОЙ СПИСОК ЮЗЕРНЕЙМОВ ====
USERNAMES = [
    {"display": "@qni##", "full": "@qnicy", "price": 2100},
    {"display": "@hoj##", "full": "@hojys", "price": 1900},
    {"display": "@qiq##", "full": "@qiqku", "price": 1800},
    {"display": "@qax##", "full": "@qaxeu", "price": 1800},
    {"display": "@xjq##", "full": "@xjoqe", "price": 1800},
    {"display": "@apl##", "full": "@aplic", "price": 1800},
    {"display": "@qmu##", "full": "@qmuzu", "price": 1800},
    {"display": "@zdy##", "full": "@zdyqu", "price": 1800},
    {"display": "@xyv##", "full": "@xyvyu", "price": 1700},
    {"display": "@kaw##", "full": "@kawen", "price": 1700},
    {"display": "@riw##", "full": "@riwti", "price": 1700},
    {"display": "@axb##", "full": "@axbux", "price": 1700},
    {"display": "@ifv##", "full": "@ifveh", "price": 1700},
    {"display": "@vyf##", "full": "@vyfab", "price": 1700},
    {"display": "@qit##", "full": "@qitcu", "price": 1600},
    {"display": "@saq##", "full": "@saqgo", "price": 1500},
    {"display": "@nut##", "full": "@nutvy", "price": 1500},
    {"display": "@qyb##", "full": "@qybpe", "price": 1500},
    {"display": "@jyk##", "full": "@jykbe", "price": 1500},
    {"display": "@cmy##", "full": "@cmyvo", "price": 1500},
    {"display": "@cyj##", "full": "@cyjpo", "price": 1500},
    {"display": "@qym##", "full": "@qymau", "price": 1500},
    {"display": "@amc##", "full": "@amcyx", "price": 1500},
    {"display": "@xdy##", "full": "@xdyci", "price": 1500},
    {"display": "@uxg##", "full": "@uxgec", "price": 1500},
    {"display": "@gmy##", "full": "@gmyje", "price": 1500},
    {"display": "@qjy##", "full": "@qjycy", "price": 1500},
    {"display": "@ikv##", "full": "@ikvys", "price": 1500},
    {"display": "@guv##", "full": "@guvmu", "price": 1500},
    {"display": "@ipm##", "full": "@ipmif", "price": 1500},
    {"display": "@qav##", "full": "@qavpe", "price": 1500},
    {"display": "@vyj##", "full": "@vyjdo", "price": 1500},
    {"display": "@cuj##", "full": "@cujav", "price": 1500},
    {"display": "@ujx##", "full": "@ujxyt", "price": 1500},
    {"display": "@jap##", "full": "@japby", "price": 1500},
    {"display": "@tgo##", "full": "@tgojy", "price": 1500},
    {"display": "@pyg##", "full": "@pygto", "price": 1500},
    {"display": "@zyf##", "full": "@zyfib", "price": 1500},
    {"display": "@qyk##", "full": "@qykae", "price": 1500},
    {"display": "@qvy##", "full": "@qvynu", "price": 1500},
    {"display": "@hjy##", "full": "@hjyne", "price": 1500},
    {"display": "@ujm##", "full": "@ujmaw", "price": 1500},
    {"display": "@epn##", "full": "@epnyx", "price": 1500},
    {"display": "@pqu##", "full": "@pquga", "price": 1500},
    {"display": "@jfu##", "full": "@jfuke", "price": 1500},
    {"display": "@gag##", "full": "@gagir", "price": 1500},
    {"display": "@byq##", "full": "@byqym", "price": 1500},
    {"display": "@ehw##", "full": "@ehwip", "price": 1500},
    {"display": "@ukm##", "full": "@ukmiq", "price": 1500},
    {"display": "@ucq##", "full": "@ucqax", "price": 1500},
    {"display": "@jyh##", "full": "@jyhso", "price": 1500},
    {"display": "@wug##", "full": "@wugya", "price": 1500},
    {"display": "@ral##", "full": "@ralau", "price": 1500},
    {"display": "@meq##", "full": "@meqyv", "price": 1500},
    {"display": "@guj##", "full": "@gujpy", "price": 1500},
    {"display": "@rfy##", "full": "@rfyha", "price": 1500},
    {"display": "@qve##", "full": "@qvece", "price": 1500},
    {"display": "@afj##", "full": "@afjiv", "price": 1500},
    {"display": "@zok##", "full": "@zoklu", "price": 1500},
    {"display": "@ybz##", "full": "@ybzum", "price": 1500},
    {"display": "@mxu##", "full": "@mxuzu", "price": 1500},
    {"display": "@qoh##", "full": "@qohau", "price": 1500},
    {"display": "@xxu##", "full": "@xxuwy", "price": 1500},
    {"display": "@dyh##", "full": "@dyhud", "price": 1500},
    {"display": "@otg##", "full": "@otgum", "price": 1500},
    {"display": "@zof##", "full": "@zofla", "price": 1500},
    {"display": "@ezx##", "full": "@ezxum", "price": 1500},
    {"display": "@wud##", "full": "@wudva", "price": 1500},
    {"display": "@jux##", "full": "@juxge", "price": 1500},
    {"display": "@wej##", "full": "@wejyw", "price": 1500},
    {"display": "@yvt##", "full": "@yvtev", "price": 1500},
    {"display": "@uhw##", "full": "@uhwuj", "price": 1500},
    {"display": "@lki##", "full": "@lkivo", "price": 1500},
    {"display": "@lyq##", "full": "@lyqyz", "price": 1500},
    {"display": "@omh##", "full": "@omhej", "price": 1500},
]

# Преобразуем в словарь для быстрого доступа
usernames_dict = {u["full"]: u for u in USERNAMES}

# Хранилище предложений
user_offers = {}
# Хранилище активных чатов
active_chats = {}

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт для пользователя"""
    await update.message.reply_text(
        f"👋 Привет, {update.effective_user.first_name}!\n\n"
        "Я помогу купить короткий Telegram-юзернейм.\n\n"
        "📋 Список доступных: /list\n"
        "❓ Помощь: /help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "🔍 **Как купить:**\n"
        "1. /list — посмотреть доступные имена\n"
        "2. Нажми на понравившееся\n"
        "3. Напиши свою цену\n"
        "4. Дождись ответа администратора"
    )

async def list_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список доступных имён"""
    available = USERNAMES
    
    if not available:
        await update.message.reply_text("😔 Сейчас нет доступных имён.")
        return
    
    # Разбиваем на страницы по 20 имён
    page = context.user_data.get("page", 0)
    start_idx = page * 20
    end_idx = min(start_idx + 20, len(available))
    
    text = f"📋 **Доступные юзернеймы (страница {page + 1}):**\n\n"
    keyboard = []
    
    for u in available[start_idx:end_idx]:
        keyboard.append([InlineKeyboardButton(
            f"{u['display']} — {u['price']}₽", 
            callback_data=f"select_{u['full']}"
        )])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="prev_page"))
    if end_idx < len(available):
        nav_buttons.append(InlineKeyboardButton("Вперёд ▶️", callback_data="next_page"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Навигация по страницам"""
    query = update.callback_query
    await query.answer()
    
    page = context.user_data.get("page", 0)
    
    if query.data == "next_page":
        context.user_data["page"] = page + 1
    elif query.data == "prev_page":
        context.user_data["page"] = max(0, page - 1)
    
    await list_usernames(update, context)

async def select_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал имя"""
    query = update.callback_query
    await query.answer()
    
    full_username = query.data.replace("select_", "")
    context.user_data["selected_username"] = full_username
    
    u = usernames_dict[full_username]
    
    await query.edit_message_text(
        f"✅ Ты выбрал: {u['display']}\n\n"
        f"💰 Базовая цена: {u['price']}₽\n\n"
        "✍️ **Напиши свою цену** (только число, в рублях):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_list")]
        ])
    )
    return WAITING_FOR_PRICE

async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к списку"""
    query = update.callback_query
    await query.answer()
    await list_usernames(update, context)
    return ConversationHandler.END

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает цену от пользователя"""
    try:
        price = int(update.message.text.strip())
        if price < 100:
            await update.message.reply_text("❌ Цена должна быть от 100₽")
            return WAITING_FOR_PRICE
    except ValueError:
        await update.message.reply_text("❌ Напиши число (например: 2500)")
        return WAITING_FOR_PRICE
    
    username = context.user_data.get("selected_username")
    user_id = update.effective_user.id
    u = usernames_dict[username]
    
    # Сохраняем предложение
    user_offers[user_id] = {
        "username": username,
        "offer_price": price,
        "display": u["display"],
        "user_name": update.effective_user.full_name
    }
    
    # Отправляем админу
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
        ],
        [InlineKeyboardButton("💬 Написать покупателю", callback_data=f"chat_{user_id}")]
    ]
    
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 **Новое предложение!**\n\n"
            f"👤 Покупатель: {update.effective_user.full_name}\n"
            f"📛 Юзернейм: {u['display']}\n"
            f"💰 Предложенная цена: {price}₽",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")
    
    await update.message.reply_text(
        f"✅ Твоё предложение по {u['display']} отправлено!\n"
        "Администратор скоро ответит."
    )
    return ConversationHandler.END

# ========== АДМИН-КОМАНДЫ ==========

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Панель администратора"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён")
        return
    
    waiting_users = list(user_offers.keys())
    
    text = "👨‍💻 **Панель администратора**\n\n"
    text += f"📊 Всего имён в базе: {len(USERNAMES)}\n"
    text += f"👥 Ожидают ответа: {len(waiting_users)}\n\n"
    
    if waiting_users:
        text += "**Ожидающие пользователи:**\n"
        for user_id in waiting_users[:5]:
            offer = user_offers[user_id]
            text += f"• {offer['user_name']} — {offer['display']} — {offer['offer_price']}₽\n"
    
    keyboard = [
        [InlineKeyboardButton("👥 Список ожидающих", callback_data="waiting_list")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def waiting_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список ожидающих пользователей"""
    query = update.callback_query
    await query.answer()
    
    if not user_offers:
        await query.edit_message_text("😴 Нет ожидающих пользователей.")
        return
    
    text = "👥 **Пользователи, ожидающие ответа:**\n\n"
    keyboard = []
    
    for user_id, offer in user_offers.items():
        text += f"• {offer['user_name']} — {offer['display']} — {offer['offer_price']}₽\n"
        keyboard.append([InlineKeyboardButton(
            f"Ответить {offer['user_name']}", 
            callback_data=f"reply_{user_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_back")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик админских callback'ов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("accept_"):
        user_id = int(data.replace("accept_", ""))
        offer = user_offers.get(user_id)
        
        if offer:
            # Отправляем пользователю полное имя
            full_username = offer['username']
            await context.bot.send_message(
                user_id,
                f"✅ **Поздравляю! Твой юзернейм готов!**\n\n"
                f"📛 **Имя:** {full_username}\n"
                f"💰 Цена: {offer['offer_price']}₽\n\n"
                f"🔐 **Как занять:**\n"
                f"1. Открой Telegram\n"
                f"2. Настройки → Имя пользователя\n"
                f"3. Введи {full_username} и нажми сохранить\n\n"
                f"Имя твоё! Приятного использования 🚀"
            )
            
            await query.edit_message_text(
                f"✅ Имя {full_username} передано пользователю {offer['user_name']}"
            )
            del user_offers[user_id]
    
    elif data.startswith("reject_"):
        user_id = int(data.replace("reject_", ""))
        offer = user_offers.get(user_id)
        
        if offer:
            await context.bot.send_message(
                user_id,
                f"❌ **Администратор отклонил твоё предложение**\n\n"
                f"Юзернейм: {offer['display']}"
            )
            await query.edit_message_text(f"❌ Предложение от {offer['user_name']} отклонено")
            del user_offers[user_id]
    
    elif data.startswith("chat_"):
        user_id = int(data.replace("chat_", ""))
        offer = user_offers.get(user_id)
        
        if offer:
            # Активируем чат
            active_chats[user_id] = True
            context.user_data["chatting_with"] = user_id
            
            await context.bot.send_message(
                user_id,
                f"💬 **Администратор начал с тобой чат!**\n"
                f"Теперь ты можешь писать сюда, и сообщения будут доставлены."
            )
            
            await query.edit_message_text(
                f"💬 Ты начал чат с {offer['user_name']}\n"
                f"Пиши сюда — сообщения будут пересылаться пользователю.\n\n"
                f"Чтобы выйти из чата, напиши /endchat"
            )
    
    elif data == "waiting_list":
        await waiting_list(update, context)
    elif data == "admin_back":
        await admin_panel(update, context)

# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик всех текстовых сообщений"""
    user_id = update.effective_user.id
    
    # Админ
    if user_id == ADMIN_ID:
        # Проверяем, есть ли активный чат
        chat_with = context.user_data.get("chatting_with")
        if chat_with:
            text = update.message.text
            await context.bot.send_message(chat_with, f"💬 **Администратор:**\n\n{text}")
            await update.message.reply_text("✅ Отправлено")
        else:
            await update.message.reply_text(
                "👋 Используй /admin для панели управления"
            )
        return
    
    # Пользователь
    # Проверяем, активен ли чат
    if active_chats.get(user_id, False):
        text = update.message.text
        await context.bot.send_message(
            ADMIN_ID,
            f"💬 **Сообщение от пользователя {update.effective_user.full_name}:**\n\n{text}"
        )
        await update.message.reply_text("✅ Отправлено администратору")
    else:
        # Проверяем, не находится ли пользователь в диалоге
        if context.user_data.get("selected_username"):
            # Уже в диалоге, просто игнорируем (ConversationHandler сам обработает)
            return
        else:
            await update.message.reply_text(
                "👋 Чтобы начать, используй /list и выбери понравившееся имя."
            )

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает чат с пользователем"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Эта команда только для администратора")
        return
    
    chat_with = context.user_data.get("chatting_with")
    if chat_with:
        # Деактивируем чат
        if chat_with in active_chats:
            del active_chats[chat_with]
        context.user_data.pop("chatting_with", None)
        await update.message.reply_text("✅ Чат завершён")
    else:
        await update.message.reply_text("❌ Нет активного чата")

# ========== ЗАПУСК ==========

def main():
    print("🚀 Запуск бота...")
    print(f"🔑 Токен: {BOT_TOKEN[:15]}... (скрыт)")
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Диалог с покупателем
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_username, pattern="^select_")],
        states={
            WAITING_FOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)]
        },
        fallbacks=[CallbackQueryHandler(back_to_list, pattern="^back_to_list$")]
    )
    
    # Основные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_usernames))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("endchat", end_chat))
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(page_navigation, pattern="^(next_page|prev_page)$"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(accept_|reject_|chat_|waiting_list|admin_back|reply_).*"))
    application.add_handler(CallbackQueryHandler(back_to_list, pattern="^back_to_list$"))
    application.add_handler(CallbackQueryHandler(select_username, pattern="^select_"))
    
    # Единый обработчик для всех текстовых сообщений (должен быть последним)
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот готов к работе!")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print("📋 Команды: /list - для покупателей, /admin - для вас")
    
    # Запускаем polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапуск через 10 секунд...")
        time.sleep(10)
        main()
