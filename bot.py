import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv
from handlers.start import start_command
from handlers.handlers_message import cancel
from handlers.handlers_message import handle_message
from handlers.handlers_keyboards import STEP_2, STEP_3, STEP_4, STEP_9, STEP_5, STEP_6, STEP_7, STEP_8, STEP_10, STEP_1, STEP_11, RaffleCreator, new_version, add_channel_command
#handle_webapp_callback
from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update
from datetime import datetime
from handlers.channel_handlers_keyboards import (my_channels, STEP_CHANNEL_1, tg_channels, back_channel, MAIN_STATE, vk_channels)
#from handlers.my_raffles_keyboard import my_raffles_start, handle_raffle_selection, STEP_RAFFLES_1, STEP_RAFFLES_2, handle_raffle_actions, handle_edit_choice,  handle_edit_input, STEP_EDIT_1, STEP_EDIT_2, STEP_DELETE_CONFIRM
#from miniapp.handle_webapp.start import start_command
#from miniapp.handle_webapp.handler import handle_webapp_data
from telegram.ext import CallbackQueryHandler
from telegram.ext import ApplicationBuilder

load_dotenv()

# В начале файла добавьте импорт:
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
import json

def bot():

    application = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cancel", cancel))

#    app.add_handler(CallbackQueryHandler(handle_webapp_callback, pattern=r"^open_webapp:"))



    raffle_creator = RaffleCreator()
    draw_conv_handler=ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Создать розыгрыш 🎁$"), raffle_creator.start),
        ],
        states={
            STEP_1: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(type_auto|type_me)$"),
            ],
            STEP_2: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_4: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(time_start|time_end)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_5: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_6: [
                MessageHandler(filters.ALL, raffle_creator.handle_step_6),
            ],
            STEP_7: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^referral_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input)
                ],
            STEP_8: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^select_channel_"),
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^continue_to_next_step$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND,raffle_creator.handle_input),
            ],
            STEP_9: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^select_channel_"),
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^continue_to_next_step$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_10: [
                CallbackQueryHandler(raffle_creator.handle_input,
                                     pattern="^(toggle_boost|toggle_captcha|save_options)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
            STEP_11: [
                CallbackQueryHandler(raffle_creator.handle_input, pattern="^(luck_boost|captcha|save_raffle)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_creator.handle_input),
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("^(❌Отменить создание|/cancel)$"), raffle_creator.cancel),
        ],
        map_to_parent={
            ConversationHandler.END: MAIN_STATE
        },
    )


    """application.add_handler(draw_conv_handler)
    draw_channels_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Мои розыгрыши 🗒$"), my_raffles_start)
        ],
        states={
            STEP_RAFFLES_1: [
                CallbackQueryHandler(handle_raffle_selection)
            ],
            STEP_RAFFLES_2: [
                CallbackQueryHandler(handle_raffle_actions)
            ],
            STEP_EDIT_1: [
                CallbackQueryHandler(handle_edit_choice)
            ],
            STEP_EDIT_2: [
                MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.ANIMATION,
                               handle_edit_input)
            ],
            STEP_DELETE_CONFIRM: [
                CallbackQueryHandler(handle_raffle_actions)
            ]
        },

        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("^⬅️ Назад$"), lambda u, c: ConversationHandler.END),
            MessageHandler(filters.TEXT & filters.Regex("^❌ Отмена$"), lambda u, c: ConversationHandler.END),
        ],
        name="raffles_conversation",
        persistent=False
    )
    application.add_handler(draw_channels_handler)"""


    draw_raffles_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Мои каналы 📢$"), my_channels)
        ],
        states={
            STEP_CHANNEL_1: [
                MessageHandler(filters.TEXT & filters.Regex("^🔸 Каналы Телеграмм$"), tg_channels),
                MessageHandler(filters.TEXT & filters.Regex("^🔹 Каналы Вконтакте$"), vk_channels),
                MessageHandler(filters.TEXT & filters.Regex("^⬅️Назад$"), back_channel)
            ],
        },

        fallbacks=[],
        map_to_parent={
            ConversationHandler.END: MAIN_STATE
        }
    )
    application.add_handler(draw_raffles_handler)


    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(add_channel_command, pattern="add_channel"))
    application.add_handler(CallbackQueryHandler(new_version, pattern="get_new_version"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("бот запущен")
    application.run_polling()

if __name__ == "__main__":
    bot()