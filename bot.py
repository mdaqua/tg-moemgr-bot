import logging
import random
import string
import nest_asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from config import (
    get_target_channel_id,
    set_target_channel_id,
    add_user_to_allowed_list,
    remove_user_from_allowed_list,
    get_bot_owner,
    set_bot_owner, get_allowed_user_list, get_bot_api_token
)

# 应用 nest_asyncio
nest_asyncio.apply()

# 启动日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 生成32位随机序列
def generate_random_sequence() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

# 启动命令处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 moemgrBot！")

# 设置 Bot Owner
async def set_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if get_bot_owner() is not None:
        await update.message.reply_text("Bot owner 已经设置，无法再次设置。")
        return

    owner_id = update.message.from_user.id
    set_bot_owner(owner_id)
    await update.message.reply_text(f"Bot owner 已设置为: {owner_id}")

# 设置目标频道 ID
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != get_bot_owner():
        await update.message.reply_text("你没有权限执行此操作！")
        return

    if not context.args:
        await update.message.reply_text("请提供新的频道 ID！")
        return

    new_channel_id = context.args[0]
    set_target_channel_id(new_channel_id)
    await update.message.reply_text(f"频道已更新为: {new_channel_id}")

# 允许用户上传文件
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != get_bot_owner():
        await update.message.reply_text("你没有权限执行此操作！")
        return

    if not context.args:
        await update.message.reply_text("请提供要允许的用户 ID！")
        return

    user_id = int(context.args[0])
    add_user_to_allowed_list(user_id)
    await update.message.reply_text(f"用户 {user_id} 已被允许转发文件。")

# 处理文件
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in get_allowed_user_list():
        await update.message.reply_text("你没有权限转发文件！")
        return

    # 获取文件信息
    file = update.message.document or update.message.video or (update.message.photo[-1] if update.message.photo else None)

    if not file:
        await update.message.reply_text("无法处理此文件类型！")
        return

    if type(file).__name__ == "PhotoSize":
        file_name = f"file_{file.file_id}.jpg"  # Mod1
    elif hasattr(file, 'file_name'):
        file_name = file.file_name
    else:
        file_name = f"file_{file.file_id}"

    file_type = classify_file_type(file_name)

    random_sequence = generate_random_sequence()

    # 获取时间
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # 获取描述
    await update.message.reply_text("请提供文件描述：")
    context.user_data['file_name'] = file_name
    context.user_data['file_type'] = file_type
    context.user_data['random_sequence'] = random_sequence
    context.user_data['date_str'] = date_str
    context.user_data['time_str'] = time_str
    context.user_data['file_id'] = file.file_id

    context.user_data['awaiting'] = 'description'

# 处理输入并转发
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    awaiting = context.user_data.get('awaiting')

    if awaiting == 'description':
        context.user_data['description'] = update.message.text

        # 获取标签
        await update.message.reply_text("请提供文件标签（如有多个请用空格分隔）：")
        context.user_data['awaiting'] = 'tags'

    elif awaiting == 'tags':
        tags = update.message.text.split()
        context.user_data['tags'] = tags

        # 构建备注
        caption = build_caption(context.user_data)
        file_id = context.user_data['file_id']
        file_type = context.user_data['file_type']

        # 根据文件类型转发文件
        if file_type == "photo":
            await context.bot.send_photo(
                parse_mode='html',
                chat_id=get_target_channel_id(),
                photo=file_id,
                caption=caption
            )
        elif file_type == "video":
            await context.bot.send_video(
                parse_mode='html',
                chat_id=get_target_channel_id(),
                video=file_id,
                caption=caption
            )
        else:
            await context.bot.send_document(
                parse_mode='html',
                chat_id=get_target_channel_id(),
                document=file_id,
                caption=caption
            )

        await update.message.reply_text("文件已转发到频道！")
        context.user_data.clear()

# 异常处理
async def error_handler(update: Update, context: CallbackContext):
    logger.error(f'Update {update} caused error {context.error}')

# 构建文件备注
def build_caption(user_data) -> str:
    extension = user_data['file_name'].split('.')[-1].lower()
    file_id_name = f"{user_data['random_sequence']}.{extension}"
    date_str = user_data['date_str']
    time_str = user_data['time_str']
    description = user_data['description']
    file_type = user_data['file_type']
    tags = ' '.join([f"#{tag.replace('#', '')}" for tag in user_data.get('tags', [])])

    return f"<pre>{file_id_name}\n{date_str} {time_str}</pre>\n{description}\n#{file_type} {tags}"

# 根据后缀分类
def classify_file_type(file_name: str) -> str:
    # 定义各类文件的后缀
    video_extensions = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv']
    photo_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
    pak_extensions = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', '001', '002', '003']
    doc_extensions = ['docx', 'pptx', 'xlsx', 'pdf', 'doc', 'ppt', 'xls']

    # 获取文件的后缀名（小写）
    extension = file_name.split('.')[-1].lower()

    # 判断文件类型
    if extension in video_extensions:
        return 'video'
    elif extension in photo_extensions:
        return 'photo'
    elif extension in pak_extensions:
        return 'pak'
    elif extension in doc_extensions:
        return 'doc'
    else:
        return 'unknown'

# 主程序
async def main():
    application = Application.builder().token(get_bot_api_token()).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_owner", set_owner))
    application.add_handler(CommandHandler("set_channel", set_channel))
    application.add_handler(CommandHandler("allow_user", allow_user))

    application.add_handler(MessageHandler(filters.ATTACHMENT, handle_file))
    application.add_handler(MessageHandler(filters.TEXT, handle_text_input))

    # 添加异常处理器
    application.add_error_handler(error_handler)

    await application.run_polling()

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
