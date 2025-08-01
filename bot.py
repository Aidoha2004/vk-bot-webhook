import requests
import time
import json

TOKEN = '001.3277213606.1546113568:1011921225'
BASE_URL = 'https://myteam.mail.ru/bot/v1'

# Состояния пользователя
users_state = {}

# Возможные города и лекторы
CITIES = ['Астана', 'Алматы', 'Шымкент']
LECTORS = ['Турманова Д.А.', 'Секуова Ш.Б.']

LINKS = {
    'Каталог залов': 'https://delicate-klepon-16140e.netlify.app/',
    'Консультация': 'https://example.com/consultation',
    'Явка на семинар': 'https://comforting-torrone-5273b1.netlify.app/'
}

OPTIONS = list(LINKS.keys()) + ['Финансовый отчет']

def send_message(chat_id, text):
    url = f'{BASE_URL}/messages/sendText'
    params = {'token': TOKEN}
    data = {
        'chatId': chat_id,
        'text': text
    }
    requests.post(url, params=params, data=data)


def send_options(chat_id):
    options_list = '\n'.join(f"{i+1}. {opt}" for i, opt in enumerate(OPTIONS))
    send_message(chat_id, f"👋 Добро пожаловать! Я бот компании Astana Orleu.Выберите нужный раздел ниже:\n{options_list}\nВведите номер:")
    users_state[chat_id] = {'step': 'choose_option'}


def start_report(chat_id):
    users_state[chat_id] = {
        'step': 'choose_city',
        'data': {}
    }
    cities_list = '\n'.join(f"{i+1}. {c}" for i, c in enumerate(CITIES))
    send_message(chat_id, f"Выберите город:\n{cities_list}\nВведите номер города:")


def process_message(chat_id, text):
    state = users_state.get(chat_id)

    if not state:
        send_options(chat_id)
        return

    step = state['step']

    if step == 'choose_option':
        if text.isdigit() and 1 <= int(text) <= len(OPTIONS):
            selected = OPTIONS[int(text) - 1]
            if selected == 'Финансовый отчет':
                start_report(chat_id)
            else:
                send_message(chat_id, f"Вот ваша ссылка: {LINKS[selected]}")
                users_state.pop(chat_id, None)
        else:
            send_message(chat_id, "Введите корректный номер из списка.")

    elif step == 'choose_city':
        data = state['data']
        if text.isdigit() and 1 <= int(text) <= len(CITIES):
            city = CITIES[int(text) - 1]
            data['city'] = city
            state['step'] = 'choose_lector'
            lectors_list = '\n'.join(f"{i+1}. {l}" for i, l in enumerate(LECTORS))
            send_message(chat_id, f"Выбран город: {city}\nВыберите лектора:\n{lectors_list}\nВведите номер лектора:")
        else:
            send_message(chat_id, "Пожалуйста, введите корректный номер города.")

    elif step == 'choose_lector':
        data = state['data']
        if text.isdigit() and 1 <= int(text) <= len(LECTORS):
            lector = LECTORS[int(text) - 1]
            data['lector'] = lector
            state['step'] = 'enter_date'
            send_message(chat_id, f"Выбран лектор: {lector}\nВведите дату семинара (например, 30 мая):")
        else:
            send_message(chat_id, "Пожалуйста, введите корректный номер лектора.")

    elif step == 'enter_date':
        data = state['data']
        data['date'] = text.strip()
        state['step'] = 'enter_start_sum'
        send_message(chat_id, "Введите сумму на начало дня (тг):")

    elif step == 'enter_start_sum':
        data = state['data']
        if text.isdigit():
            data['start_sum'] = int(text)
            data['expenses'] = []
            state['step'] = 'enter_expense'
            send_message(chat_id, "Введите затраты в формате:\nОписание: сумма\nНапример:\nТакси до зала: 960\nДля завершения введите слово 'готово'")
        else:
            send_message(chat_id, "Введите сумму числом без пробелов.")

    elif step == 'enter_expense':
        data = state['data']
        if text.lower() == 'готово':
            total_expenses = sum(e[1] for e in data['expenses'])
            remainder = data['start_sum'] - total_expenses
            report_lines = [
                f"г. {data['city']}",
                f"Лектор: {data['lector']}",
                f"{data['date']}\n",
                f"Сумма на начало дня:\n{data['start_sum']} тг\n",
                "Затраты:"
            ]
            for desc, amount in data['expenses']:
                report_lines.append(f"{desc}: {amount} тг")
            report_lines.append(f"\nИтого расходы: {total_expenses} тг")
            report_lines.append(f"Сумма остатка: {remainder} тг")
            send_message(chat_id, '\n'.join(report_lines))
            users_state.pop(chat_id)
        else:
            if ':' in text:
                parts = text.split(':', 1)
                desc = parts[0].strip()
                amount_str = parts[1].strip().replace('тг', '').strip()
                if amount_str.isdigit():
                    amount = int(amount_str)
                    data['expenses'].append((desc, amount))
                    send_message(chat_id, f"Добавлено: {desc} — {amount} тг\nВведите следующую затрату или 'готово' для завершения.")
                else:
                    send_message(chat_id, "Сумма должна быть числом. Попробуйте снова.")
            else:
                send_message(chat_id, "Неправильный формат. Используйте 'Описание: сумма'.")

def main():
    print("✅ Бот запущен. Ожидание событий...")
    last_event_id = 0
    while True:
        updates = get_updates(last_event_id)
        events = updates.get("events", [])

        if events:
            for event in events:
                last_event_id = event["eventId"]
                if event["type"] == "newMessage":
                    chat_id = event["payload"]["chat"]["chatId"]
                    message = event["payload"].get("text", "")

                    print(f"✉️ Сообщение от {chat_id}: {message}")

                    process_message(chat_id, message)
        else:
            time.sleep(1)

def get_updates(last_event_id):
    url = f'{BASE_URL}/events/get'
    params = {
        'token': TOKEN,
        'lastEventId': last_event_id,
        'pollTime': 25
    }
    response = requests.get(url, params=params, timeout=30)
    return response.json()

if __name__ == '__main__':
    main()