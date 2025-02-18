import logging
from threading import Lock
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    CallbackContext
)

# ========== تنظیمات اصلی ========== #
TOKEN = ""
GROUP_ID =   # جایگزین کن با آیدی گروه
ATOUSA = 4
# ================================= #

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
update_lock = Lock()

def calculate_name(members: int) -> str:
    """محاسبه نام جدید بر اساس تعداد اعضا"""
    diff = members - ATOUSA
    if diff > 0:
        return f"atousa+{diff}"
    elif diff < 0:
        return f"atousa-{abs(diff)}"
    return "atousa"

async def update_group_name(application: Application):
    """به‌روزرسانی نام گروه بر اساس تعداد اعضا"""
    try:
        if not update_lock.acquire(blocking=False):
            logger.warning("⏳ درخواست آپدیت نادیده گرفته شد")
            return
        
        count = await application.bot.get_chat_member_count(GROUP_ID)
        new_name = calculate_name(count)
        await application.bot.set_chat_title(GROUP_ID, new_name)
        logger.info(f"✅ نام گروه تغییر کرد: {new_name}")

    except Exception as e:
        logger.error(f"❌ خطا در تغییر نام گروه: {str(e)}")

    finally:
        update_lock.release()

async def track_members(update: Update, context: CallbackContext):
    """تشخیص تغییر اعضای گروه"""
    if isinstance(update.chat_member, ChatMemberUpdated):
        if update.chat_member.chat.id == GROUP_ID:
            logger.info("🔄 تغییر در اعضا شناسایی شد")
            await update_group_name(context.application)

async def start(update: Update, context: CallbackContext):
    """دستور /update برای به‌روزرسانی دستی"""
    await update_group_name(context.application)
    await update.message.reply_text("✅ نام گروه آپدیت شد!")

async def init_bot(application: Application):
    """بعد از استارت ربات، اولین نام گروه را تنظیم کن"""
    await update_group_name(application)
    logger.info("🚀 نام اولیه گروه تنظیم شد.")

def main():
    """اجرای ربات"""
    app = Application.builder().token(TOKEN).build()

    # اجرای تابع init_bot بدون post_init
    app.add_handler(CommandHandler("start", lambda u, c: app.create_task(init_bot(app))))
    
    # هندلرها
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("update", start))

    logger.info("🚀 ربات فعال شد و در حال اجراست!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
