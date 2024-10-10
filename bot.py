import logging
import re
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

import os
from dotenv import load_dotenv

import paramiko

# для postgresql
import psycopg2
from psycopg2 import Error

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def exec_remote_cmd(cmd: str) -> str:
    ip = os.getenv("RM_HOST")
    port = os.getenv("RM_PORT")
    username = os.getenv("RM_USER")
    password = os.getenv("RM_PASSWORD")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=username, password=password, port=port)

        stdin, stdout, stderr = client.exec_command(cmd) # выполняем
        data = str(stdout.read().decode()) + str(stderr.read().decode()) # сохраняем stdout и stderr в data

        client.close() # отключаемся 
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')
        return data
    except paramiko.ssh_exception.NoValidConnectionsError: # не удалось подключиться к хосту
        return f"Хост {ip}:{port} недоступен!"
    except Exception as err: # какая-то другая проблема
        return 'Возникло исключение: ' + str(err)


def send_msg_by_chunks(msg: str, update: Update):
    if len(msg) >= 4095:
        sent = 0
        while sent < len(msg):
            update.message.reply_text(msg[sent:sent+4095])
            sent += 4095
    else:
        update.message.reply_text(msg)

def get_release(update: Update, context):
    result = exec_remote_cmd("cat /etc/*-release")
    send_msg_by_chunks(result, update)

def get_uname(update: Update, context):
    result = exec_remote_cmd("uname -a")
    send_msg_by_chunks(result, update)

def get_uptime(update: Update, context):
    result = exec_remote_cmd("uptime")
    send_msg_by_chunks(result, update)

def get_df(update: Update, context):
    result = exec_remote_cmd("df -H")
    send_msg_by_chunks(result, update)

def get_free(update: Update, context):
    result = exec_remote_cmd("free -h")
    send_msg_by_chunks(result, update)

def get_mpstat(update: Update, context):
    result = exec_remote_cmd("mpstat -P ALL")
    send_msg_by_chunks(result, update)

def get_w(update: Update, context):
    result = exec_remote_cmd("w")
    send_msg_by_chunks(result, update)

def get_auths(update: Update, context):
    result = exec_remote_cmd("last | head -n 10")
    send_msg_by_chunks(result, update)

def get_critical(update: Update, context):
    result = exec_remote_cmd("journalctl -p crit -n 5 -xn --no-pager")
    send_msg_by_chunks(result, update)

def get_ps(update: Update, context):
    result = exec_remote_cmd("ps aux")
    send_msg_by_chunks(result, update)

def get_ss(update: Update, context):
    result = exec_remote_cmd("ss -ta")
    send_msg_by_chunks(result, update)

def get_services(update: Update, context):
    result = exec_remote_cmd("systemctl --type=service --state=running")
    send_msg_by_chunks(result, update)

def get_repl_logs(update: Update, context):
    result = exec_remote_cmd("cat /var/log/postgresql/postgresql-15-main.log | grep \"repl\"")
    send_msg_by_chunks(result, update)

def get_result_from_table(table_name: str) -> str:
    result = "Результаты: "
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"),
                                  password=os.getenv("DB_PASSWORD"),
                                  host=os.getenv("DB_HOST"),
                                  port=os.getenv("DB_PORT"), 
                                  database=os.getenv("DB_DATABASE"))
        sql_request = "SELECT * FROM " + table_name
        cursor = connection.cursor()
        cursor.execute(sql_request)
        data = cursor.fetchall()
        
        for row in data:
            result += str(row[0]) + " - " + str(row[1]) + '\n'

    except Exception as err:
        result = str(err)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return result

# postgresql
def get_emails(update: Update, context):
    result = get_result_from_table("first")
    send_msg_by_chunks(result, update)

def get_phone_numbers(update: Update, context):
    result = get_result_from_table("second")
    send_msg_by_chunks(result, update)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')
    
def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'findPhoneNumbers'

def findEmailCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска email: ")
    return "findEmail"

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text("Введите пароль: ")
    return "verifyPassword"

def get_apt_list_command(update: Update, context):
    update.message.reply_text("Введите имя пакета или ALL для отображения всех пакетов: ")
    return "get_apt_list"

def get_apt_list (update: Update, context):
    user_input = update.message.text
    result = ""
    if user_input == "ALL":
        result = exec_remote_cmd("apt list --installed")
        send_msg_by_chunks(result, update)
        return ConversationHandler.END
    
    whitelist_characters = "qwertyuiopasdfghjklzxcvbnm-1234567890."
    for character in user_input.lower():
        if character not in whitelist_characters:
            update.message.reply_text("RCE DETECTED!!!!")
            return ConversationHandler.END
    result = exec_remote_cmd("apt list --installed | grep '" + user_input + "'")
    send_msg_by_chunks(result, update)
    return ConversationHandler.END

def findPhoneNumbers (update: Update, context: CallbackContext):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    phoneNumRegex = re.compile(r'(\+7|8)[\s-]?(\(?\d{3}\)?|(\d{3}))[\s-]?(\d{3})[\s-]?(\d{2})[\s-]?(\d{2})')
    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END

    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    phones = []
    for i in range(len(phoneNumberList)):
        phone = ""
        for x in phoneNumberList[i]:
            phone += x
        phones.append(phone)
        phoneNumbers += f'{i+1}. {phone}\n' # Записываем очередной номер

    send_msg_by_chunks(phoneNumbers, update)
    update.message.reply_text('Желаете ли вы сохранить найденные телефонные номера? (да/нет):')
    context.user_data['contacts'] = phones
    return 'save_phones'

def insert_data_sql(table_name: str, column_name: str, values: list) -> str:
    ret = "Записи успешно добавлены"
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"),
                                  password=os.getenv("DB_PASSWORD"),
                                  host=os.getenv("DB_HOST"),
                                  port=os.getenv("DB_PORT"), 
                                  database=os.getenv("DB_DATABASE"))
        sql_request = "INSERT INTO " + table_name + f"({column_name}) values (%s);"
        cursor = connection.cursor()
        for val in values:
            cursor.execute(sql_request, (val,))
        connection.commit()
        
    except Exception as err:
        ret = str(err)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ret

def save_phones(update: Update, context: CallbackContext):
    user_input = update.message.text.lower()
    if user_input == "да":
        update.message.reply_text(insert_data_sql("second", "phone", context.user_data["contacts"]))
    elif user_input == "нет":
        update.message.reply_text("Записи не будут добавлены!")
    else:
        update.message.reply_text('Ответьте да или нет:')
        return 'save_phones'
    
    return ConversationHandler.END

def findEmail(update: Update, context):
    user_input = update.message.text
    email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailsList = email_regex.findall(user_input)

    if not emailsList:
        update.message.reply_text('Email адреса не найдены!')
        return ConversationHandler.END

    output = '' 
    for i in range(len(emailsList)):
        output += f'{i+1}. {emailsList[i]}\n'
    send_msg_by_chunks(output, update)
    update.message.reply_text('Желаете ли вы сохранить найденные почтовые адреса? (да/нет):')
    context.user_data['contacts'] = emailsList
    return 'save_email'

def save_email(update: Update, context: CallbackContext):
    user_input = update.message.text.lower()
    if user_input == "да":
        update.message.reply_text(insert_data_sql("first", "email", context.user_data["contacts"]))
    elif user_input == "нет":
        update.message.reply_text("Записи не будут добавлены!")
    else:
        update.message.reply_text('Ответьте да или нет:')
        return 'save_email'
    
    return ConversationHandler.END

def verifyPassword(update: Update, context):
    user_input = update.message.text
    pwd = re.search(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$",  user_input)

    if not pwd:
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END

    update.message.reply_text('Пароль сложный')
    return ConversationHandler.END



def main():
		# Создайте программу обновлений и передайте ей токен вашего бота
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'save_phones': [MessageHandler(Filters.text & ~Filters.command, save_phones)],
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
            entry_points=[CommandHandler('find_email', findEmailCommand)],
            states={
                'findEmail' : [MessageHandler(Filters.text & ~Filters.command, findEmail)],
                'save_email' : [MessageHandler(Filters.text & ~Filters.command, save_email)],
                },
            fallbacks=[]
            )
    convHandlerVerifyPassword = ConversationHandler(
            entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
            states={
                'verifyPassword' : [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
                },
            fallbacks=[]
            )
    convHandlerFindPackets = ConversationHandler(
            entry_points=[CommandHandler('get_apt_list', get_apt_list_command)],
            states={
                'get_apt_list' : [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
                },
            fallbacks=[]
            )

		# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))


    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerFindPackets)
    dp.add_handler(convHandlerVerifyPassword)
    

		# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
		# Запускаем бота
    updater.start_polling()

		# Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
