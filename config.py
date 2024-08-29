import json
import os

# 配置文件路径
CONFIG_FILE_PATH = 'config.json'
# 设置 Bot API Token
BOT_API_TOKEN = ""

# 初始化全局变量
config_data = {
    "TARGET_CHANNEL_ID": None,
    "ALLOWED_USER_LIST": [],
    "BOT_OWNER": None,
    "BOT_API_TOKEN": BOT_API_TOKEN
}

# 加载配置
def load_config():
    global config_data
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as file:
            config_data = json.load(file)

# 保存配置
def save_config():
    global config_data
    with open(CONFIG_FILE_PATH, 'w') as file:
        json.dump(config_data, file)

def get_target_channel_id():
    return config_data["TARGET_CHANNEL_ID"]

def set_target_channel_id(new_id):
    global config_data
    config_data["TARGET_CHANNEL_ID"] = new_id
    save_config()

def add_user_to_allowed_list(user_id):
    global config_data
    if user_id not in config_data["ALLOWED_USER_LIST"]:
        config_data["ALLOWED_USER_LIST"].append(user_id)
        save_config()

def remove_user_from_allowed_list(user_id):
    global config_data
    if user_id in config_data["ALLOWED_USER_LIST"]:
        config_data["ALLOWED_USER_LIST"].remove(user_id)
        save_config()

def get_allowed_user_list():
    global config_data
    return config_data["ALLOWED_USER_LIST"]

def get_bot_owner():
    return config_data["BOT_OWNER"]

def set_bot_owner(owner_id):
    global config_data
    config_data["BOT_OWNER"] = owner_id
    add_user_to_allowed_list(owner_id)  # 默认将 owner 添加到允许用户列表
    save_config()

def get_bot_api_token():
    return config_data["BOT_API_TOKEN"]

# 启动时加载配置
load_config()
