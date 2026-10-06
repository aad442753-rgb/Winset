import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

# Конфигурация системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= КОНФИГУРАЦИЯ =================
TOKEN = '8882373875:AAG1VRsDe95bQXf66BL3CFY2OHsW7ZCKCM0'
ADMIN_ID = 8921077599  # Ваш Telegram ID
# =================================================

# Этапы заполнения анкеты (ConversationHandler)
PROBLEM_DESC, OS_INFO, REMOTE_SOFTWARE, REMOTE_ID = range(4)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "🌐 **[GLOBAL NETWORK] Панель управления Anti RCE активна.**\n"
            "🛡 Ожидание входящих инцидентов и запросов.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    welcome_message = (
        "🌐 **ANTI RCE — Глобальная служба нейтрализации угроз**\n\n"
        "Специализированная помощь по обнаружению и удалению вредоносного ПО (RAT, майнеры, стиллеры, бэкдоры).\n\n"
        "📜 **ПРАВИЛА И УСЛОВИЯ ОБСЛУЖИВАНИЯ:**\n"
        "1. Администрация и модераторы сервиса **не несут никакой юридической или материальной ответственности** за состояние вашей операционной системы, потерю данных или сбои оборудования в процессе или после проведения диагностических и восстановительных работ.\n"
        "2. Обращаясь в сервис, вы добровольно предоставляете доступ к своему устройству и подтверждаете, что осознаете все риски удаленного администрирования.\n\n"
        "📝 Для составления полной анкеты ответьте на несколько вопросов.\n\n"
        "**Шаг 1/4:** Опишите подробно, что именно случилось и какие симптомы заражения вы наблюдаете:"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")
    return PROBLEM_DESC

async def step_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['problem'] = update.message.text
    await update.message.reply_text(
        "🌐 **Шаг 2/4:** Укажите вашу операционную систему (например: Windows 10/11, версия сборки) и основные характеристики ПК:",
        parse_mode="Markdown"
    )
    return OS_INFO

async def step_os(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['os_info'] = update.message.text
    await update.message.reply_text(
        "🌐 **Шаг 3/4:** Какое ПО для удаленного доступа вы используете?\n"
        "(Например: **AnyDesk**, **RustDesk** или другое)",
        parse_mode="Markdown"
    )
    return REMOTE_SOFTWARE

async def step_remote_software(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['software'] = update.message.text
    await update.message.reply_text(
        "🌐 **Шаг 4/4:** Укажите **ID подключения** для выбранной программы или ваш прямой контакт (Telegram для связи):",
        parse_mode="Markdown"
    )
    return REMOTE_ID

async def step_finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data['remote_id'] = update.message.text

    # Собираем всю анкету
    data = context.user_data
    user_identifier = f"@{user.username}" if user.username else f"ID: `{user.id}`"

    admin_dispatch_text = (
        f"🌐 **[INCIDENT] ПОСТУПИЛА ПОЛНАЯ АНКЕТА [ANTI RCE]**\n\n"
        f"👤 **Клиент:** {user.first_name} ({user_identifier})\n"
        f"🆔 **Target ID:** `{user.id}`\n\n"
        f"📄 **1. Описание проблемы:**\n{data.get('problem')}\n\n"
        f"💻 **2. ОС / Система:**\n{data.get('os_info')}\n\n"
        f"🛠 **3. Софт для доступа:**\n{data.get('software')}\n\n"
        f"🔑 **4. ID / Контакт:**\n{data.get('remote_id')}"
    )

    action_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Принять инцидент", callback_data=f"accept_{user.id}"),
            InlineKeyboardButton("🛑 Отклонить", callback_data=f"decline_{user.id}")
        ],
        [
            InlineKeyboardButton("💬 Secure-канал (Написать)", url=f"tg://user?id={user.id}")
        ]
    ])

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_dispatch_text,
            reply_markup=action_markup,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "🌐 **Анкета успешно сформирована и передана в глобальную базу.**\n"
            "⏳ Ожидайте проверки специалистом. Уведомление поступит автоматически.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при передаче анкеты оператору: {e}")
        await update.message.reply_text("⚠️ Ошибка отправки пакета данных. Повторите попытку позже (/start).")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Заполнение анкеты отменено. Используйте /start для перезапуска.")
    return ConversationHandler.END

async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    action_type, target_id_str = query.data.split("_")
    target_client_id = int(target_id_str)

    if action_type == "accept":
        try:
            await context.bot.send_message(
                chat_id=target_client_id,
                text="🌐 **Статус инцидента: ПРИНЯТ В РАБОТУ**\n"
                     "🛡 Специалист Anti RCE подключился к задаче. Подготовьте сеанс связи.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление клиенту {target_client_id}: {e}")

        updated_log = query.message.text + "\n\n🌐 **СТАТУС: ИНЦИДЕНТ В РАБОТЕ**"
        await query.edit_message_text(text=updated_log, parse_mode="Markdown")

    elif action_type == "decline":
        try:
            await context.bot.send_message(
                chat_id=target_client_id,
                text="🛑 **Статус инцидента: ОТКЛОНЕН**\n"
                     "⚠️️ Запрос отклонен службой безопасности (высокая нагрузка сети или недостаточно данных в анкете).",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление клиенту {target_client_id}: {e}")

        updated_log = query.message.text + "\n\n🛑 **СТАТУС: ИНЦИДЕНТ ОТКЛОНЕН**"
        await query.edit_message_text(text=updated_log, parse_mode="Markdown")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # Пошаговый диалог для заполнения анкеты клиентом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            PROBLEM_DESC: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_problem)],
            OS_INFO: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_os)],
            REMOTE_SOFTWARE: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_remote_software)],
            REMOTE_ID: [MessageHandler(filters.TEXT & (~filters.COMMAND), step_finish_application)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_admin_decision))

    logger.info("Глобальная сеть Anti RCE с пошаговой анкетой успешно запущена.")
    application.run_polling()