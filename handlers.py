import logging
import random
import time
import json
import os
from datetime import date
import data_manager
from config import MEMBERS_FILE

logger = logging.getLogger(__name__)

def register_handlers(bot):
    """Регистрирует все обработчики команд"""
    
    @bot.message_handler(commands=['start'])
    def start(message):
        logger.info(f"/start от {message.from_user.id} в чате {message.chat.id}")
        help_text = """
🤖 <b>Бот для определения клоуна/пидора дня!</b>

🎪 <b>Основные команды:</b>
/clown или /pidor - Определить победителя дня (раз в сутки)
/clownstats или /pidorstats - Показать полную статистику

📝 <b>Саморегистрация:</b>
/register - Добавить себя в список участников
/unregister - Удалить себя из списка участников

⚙️ <b>Настройка режима:</b>
/setmode clown - режим "Клоун дня"
/setmode pidor - режим "Пидор дня"

👥 <b>Управление участниками:</b>
/addmember @username имя - добавить участника
/removemember @username - удалить участника
/listmembers - показать список участников
/initmembers - создать список из администраторов
"""
        bot.reply_to(message, help_text)

    @bot.message_handler(commands=['help'])
    def help_cmd(message):
        start(message)

    @bot.message_handler(commands=['clown', 'pidor'])
    def clown(message):
        chat_id = str(message.chat.id)
        today = str(date.today())
        
        logger.info(f"🎪 /clown от {message.from_user.id} в чате {chat_id}")
        
        # Используем data_manager.last_used ВЕЗДЕ
        if chat_id in data_manager.last_used and data_manager.last_used[chat_id] == today:
            logger.info(f"В чате {chat_id} уже выбирали сегодня")
            show_stats(message, chat_id)
            return
        
        members = data_manager.get_members_for_chat(chat_id)
        if not members:
            bot.reply_to(message, 
                "❌ Нет списка участников!\n"
                "/addmember @username - добавить участника\n"
                "/initmembers - создать список из админов"
            )
            return
        
        winner = random.choice(members)
        logger.info(f"Победитель: {winner.get('name')} (@{winner.get('username')})")
        
        phrases = data_manager.get_phrases_for_chat(message.chat.id)
        pre_phrases = phrases.get('pre', ["Кто же сегодня будет выбран? 🤔"])
        bot.reply_to(message, random.choice(pre_phrases))
        
        time.sleep(1)
        
        winner_name = winner.get('name', 'Неизвестный')
        winner_username = winner.get('username', '')
        username_display = f"@{winner_username}" if winner_username else winner_name
        
        result_template = phrases.get('result', "{name} ({username})")
        result_text = result_template.format(name=winner_name, username=username_display)
        bot.send_message(message.chat.id, result_text)
        
        stats = data_manager.load_stats()
        if chat_id not in stats:
            stats[chat_id] = {}
        
        user_key = winner_username or str(winner.get('id', winner_name))
        if user_key not in stats[chat_id]:
            stats[chat_id][user_key] = {
                'name': winner_name,
                'username': winner_username,
                'count': 0
            }
        stats[chat_id][user_key]['count'] += 1
        data_manager.save_stats(stats)
        
        data_manager.last_used[chat_id] = today
        data_manager.save_all_data()
        logger.info(f"✅ clown выполнен для чата {chat_id}")

    def show_stats(message, chat_id):
        stats = data_manager.load_stats()
        if chat_id not in stats or not stats[chat_id]:
            bot.reply_to(message, "Статистика пока пуста!")
            return
        
        sorted_stats = sorted(stats[chat_id].items(), key=lambda x: x[1]['count'], reverse=True)
        mode = data_manager.get_chat_mode(chat_id)
        mode_names = {'clown': '🤡 клоун', 'pidor': '🏳️‍🌈 пидор', 'default': '🎯 победитель'}
        mode_name = mode_names.get(mode, 'победитель')
        
        response = f"📊 Сегодняшний {mode_name} уже выбран!\n\nСтатистика:\n"
        for i, (uid, udata) in enumerate(sorted_stats[:10], 1):
            uname = f"@{udata['username']}" if udata.get('username') else udata['name']
            response += f"{i}. {udata['name']} ({uname}) - {udata['count']} раз(а)\n"
        bot.reply_to(message, response)

    @bot.message_handler(commands=['clownstats', 'pidorstats'])
    def stats_cmd(message):
        chat_id = str(message.chat.id)
        stats = data_manager.load_stats()
        
        if chat_id not in stats or not stats[chat_id]:
            bot.reply_to(message, "Статистика пока пуста! Используйте /clown")
            return
        
        sorted_stats = sorted(stats[chat_id].items(), key=lambda x: x[1]['count'], reverse=True)
        mode = data_manager.get_chat_mode(chat_id)
        mode_names = {'clown': '🤡 клоунов', 'pidor': '🏳️‍🌈 пидоров', 'default': '🎯 победителей'}
        mode_name = mode_names.get(mode, 'победителей')
        
        response = f"🏆 Статистика {mode_name}:\n\n"
        for i, (uid, udata) in enumerate(sorted_stats, 1):
            uname = f"@{udata['username']}" if udata.get('username') else udata['name']
            response += f"{i}. {udata['name']} ({uname}) - {udata['count']} раз(а)\n"
        bot.reply_to(message, response)

    @bot.message_handler(commands=['register'])
    def register(message):
        chat_id = str(message.chat.id)
        user = message.from_user
        
        logger.info(f"📝 /register: user={user.id} (@{user.username}) в чате {chat_id}")
        
        if user.is_bot:
            bot.reply_to(message, "❌ Боты не могут регистрироваться!")
            return
        
        if chat_id not in data_manager.chat_members:
            data_manager.chat_members[chat_id] = []
            logger.info(f"  Создан новый список для чата {chat_id}")
        
        for member in data_manager.chat_members[chat_id]:
            if member.get('id') == user.id:
                bot.reply_to(message, "❌ Вы уже зарегистрированы!")
                return
        
        new_member = {
            'id': user.id,
            'username': user.username or "",
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени",
            'active': True,
            'added_by': 'self_registration',
            'added_date': str(date.today())
        }
        data_manager.chat_members[chat_id].append(new_member)
        data_manager.save_all_data()
        
        logger.info(f"  ✅ Зарегистрирован: {new_member['name']}")
        logger.info(f"  Всего в чате {chat_id}: {len(data_manager.chat_members[chat_id])} участников")
        bot.reply_to(message, f"✅ Зарегистрирован: {new_member['name']}")

    @bot.message_handler(commands=['unregister'])
    def unregister(message):
        chat_id = str(message.chat.id)
        user_id = message.from_user.id
        
        if chat_id not in data_manager.chat_members:
            bot.reply_to(message, "❌ Нет списка участников!")
            return
        
        old_len = len(data_manager.chat_members[chat_id])
        data_manager.chat_members[chat_id] = [
            m for m in data_manager.chat_members[chat_id] 
            if m.get('id') != user_id
        ]
        
        if len(data_manager.chat_members[chat_id]) < old_len:
            data_manager.save_all_data()
            bot.reply_to(message, "✅ Вы удалены из списка")
        else:
            bot.reply_to(message, "❌ Вы не найдены в списке")

    @bot.message_handler(commands=['addmember'])
    def addmember(message):
        chat_id = str(message.chat.id)
        args = message.text.split()[1:]
        
        if not args:
            bot.reply_to(message, "/addmember @username [имя]")
            return
        
        username = args[0].replace('@', '')
        name = args[1] if len(args) > 1 else username
        
        if chat_id not in data_manager.chat_members:
            data_manager.chat_members[chat_id] = []
        
        for member in data_manager.chat_members[chat_id]:
            if member.get('username') == username:
                bot.reply_to(message, f"❌ @{username} уже в списке!")
                return
        
        data_manager.chat_members[chat_id].append({
            'username': username,
            'name': name,
            'active': True,
            'added_by': message.from_user.username or message.from_user.first_name,
            'added_date': str(date.today())
        })
        data_manager.save_all_data()
        bot.reply_to(message, f"✅ Добавлен: {name} (@{username})")

    @bot.message_handler(commands=['removemember'])
    def removemember(message):
        chat_id = str(message.chat.id)
        args = message.text.split()[1:]
        
        if not args:
            bot.reply_to(message, "/removemember @username")
            return
        
        username = args[0].replace('@', '')
        
        if chat_id not in data_manager.chat_members:
            bot.reply_to(message, "❌ Нет списка участников!")
            return
        
        old_len = len(data_manager.chat_members[chat_id])
        data_manager.chat_members[chat_id] = [
            m for m in data_manager.chat_members[chat_id] 
            if m.get('username') != username
        ]
        
        if len(data_manager.chat_members[chat_id]) < old_len:
            data_manager.save_all_data()
            bot.reply_to(message, f"✅ @{username} удалён")
        else:
            bot.reply_to(message, f"❌ @{username} не найден")

    @bot.message_handler(commands=['listmembers'])
    def listmembers(message):
        chat_id = str(message.chat.id)
        
        if chat_id not in data_manager.chat_members or not data_manager.chat_members[chat_id]:
            bot.reply_to(message, "📭 Список пуст!")
            return
        
        members = data_manager.chat_members[chat_id]
        active = len([m for m in members if m.get('active', True)])
        
        response = f"👥 Участники ({active} из {len(members)}):\n\n"
        for i, m in enumerate(members, 1):
            status = "✅" if m.get('active', True) else "❌"
            username = f"@{m['username']}" if m.get('username') else "без @"
            response += f"{i}. {status} {m.get('name', '?')} {username}\n"
        
        bot.reply_to(message, response)

    @bot.message_handler(commands=['initmembers'])
    def initmembers(message):
        chat_id = str(message.chat.id)
        
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            
            if chat_id not in data_manager.chat_members:
                data_manager.chat_members[chat_id] = []
            
            added = 0
            for admin in admins:
                user = admin.user
                if user.is_bot or not user.username:
                    continue
                
                if not any(m.get('username') == user.username for m in data_manager.chat_members[chat_id]):
                    data_manager.chat_members[chat_id].append({
                        'id': user.id,
                        'username': user.username,
                        'name': user.first_name or "Без имени",
                        'active': True,
                        'added_by': 'system',
                        'added_date': str(date.today())
                    })
                    added += 1
            
            data_manager.save_all_data()
            bot.reply_to(message, f"✅ Добавлено {added} администраторов" if added else "ℹ️ Все уже в списке")
            
        except Exception as e:
            logger.error(f"initmembers error: {e}")
            bot.reply_to(message, "❌ Бот должен быть администратором чата!")

    @bot.message_handler(commands=['setmode'])
    def setmode(message):
        chat_id = str(message.chat.id)
        args = message.text.split()[1:]
        
        if not args:
            mode = data_manager.get_chat_mode(chat_id)
            bot.reply_to(message, f"Текущий режим: {mode}\nДоступные: clown, pidor")
            return
        
        mode = args[0].lower()
        if mode not in ['clown', 'pidor']:
            bot.reply_to(message, "❌ clown или pidor")
            return
        
        data_manager.group_settings[chat_id] = mode
        data_manager.save_group_settings()
        bot.reply_to(message, f"✅ Режим: {mode}")