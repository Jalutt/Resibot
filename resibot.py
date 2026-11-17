import os
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Fetch token from Render Environment Variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "9066180553:AAGR1tZ-bYcHvk0zeA7I4hjWFe351jVpF9w")

# Render automatically sets RENDER_EXTERNAL_URL (e.g., https://your-app.onrender.com)
# If not set, replace the fallback string with your actual Render URL
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://resibot-1-7npe.onrender.com")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

DB_FILE = "budget_bot.db"

# Temporary state storage for calculator inputs
user_states = {}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            cash REAL DEFAULT 0.0,
            ewallet REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            category TEXT,
            subcategory TEXT,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_funds(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT cash, ewallet FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    else:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, cash, ewallet) VALUES (?, 0.0, 0.0)", (user_id,))
        conn.commit()
        conn.close()
        return 0.0, 0.0

def update_funds(user_id, cash_delta=0.0, ewallet_delta=0.0):
    cash, ewallet = get_user_funds(user_id)
    new_cash = max(0.0, cash + cash_delta)
    new_ewallet = max(0.0, ewallet + ewallet_delta)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET cash = ?, ewallet = ? WHERE user_id = ?", (new_cash, new_ewallet, user_id))
    conn.commit()
    conn.close()
    return new_cash, new_ewallet

def get_welcome_message(user_id, cash, ewallet):
    total = cash + ewallet
    if user_id == 5238049566:
        return (
            f"✨💖 Hiii Pretut! Welcome back to your Budget Bestie! 💖✨\n"
            f"Here’s a quick peek at your funds today, queen:\n"
            f"👛 Current Funds\n"
            f"💵 Cash on Hand: ₱{cash:,.2f}\n"
            f"📱 E-Wallet: ₱{ewallet:,.2f}\n"
            f"💎 Total: ₱{total:,.2f}\n\n"
            f"🎀 Bestie Reminder: Smart budgeting isn't about restricting yourself—it's about making "
            f"sure you always have enough for your needs AND your well-deserved treats! Track every peso and watch your savings glow! ✨💅"
        )
    elif user_id == 743663528:
        return (
            f"🏎️🔥 Yo JL! Welcome back to your Budget Tracker! 🔥🏎️\n"
            f"Here’s where your stats stand right now:\n"
            f"💼 Current Funds\n"
            f"💵 Cash on Hand: ₱{cash:,.2f}\n"
            f"💳 E-Wallet: ₱{ewallet:,.2f}\n"
            f"🏆 Total: ₱{total:,.2f}\n\n"
            f"🛡️ Pro Tip: Discipline beats impulse. Know where every peso goes, prioritize your essentials first, "
            f"and keep stacking your wins. Stay on track, boss! 💪🚀"
        )
    else:
        return (
            f"👋 Welcome to your Personal Budget Tracker!\n\n"
            f"👛 Current Funds:\n"
            f"💵 Cash on Hand: ₱{cash:,.2f}\n"
            f"📱 E-Wallet: ₱{ewallet:,.2f}\n"
            f"💎 Total: ₱{total:,.2f}"
        )

def main_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ Add Income", callback_data="menu_income"),
        InlineKeyboardButton("📉 Input Expenses", callback_data="menu_expense")
    )
    markup.row(
        InlineKeyboardButton("💵 Set Cash", callback_data="set_cash"),
        InlineKeyboardButton("📱 Set E-Wallet", callback_data="set_ewallet")
    )
    return markup

def calculator_markup(current_val="0"):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"Value: {current_val}", callback_data="noop"))
    markup.row(
        InlineKeyboardButton("1", callback_data="calc_1"),
        InlineKeyboardButton("2", callback_data="calc_2"),
        InlineKeyboardButton("3", callback_data="calc_3")
    )
    markup.row(
        InlineKeyboardButton("4", callback_data="calc_4"),
        InlineKeyboardButton("5", callback_data="calc_5"),
        InlineKeyboardButton("6", callback_data="calc_6")
    )
    markup.row(
        InlineKeyboardButton("7", callback_data="calc_7"),
        InlineKeyboardButton("8", callback_data="calc_8"),
        InlineKeyboardButton("9", callback_data="calc_9")
    )
    markup.row(
        InlineKeyboardButton(".", callback_data="calc_dot"),
        InlineKeyboardButton("0", callback_data="calc_0"),
        InlineKeyboardButton("⌫", callback_data="calc_back")
    )
    markup.row(
        InlineKeyboardButton("❌ Cancel", callback_data="calc_cancel"),
        InlineKeyboardButton("✅ Confirm", callback_data="calc_confirm")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    cash, ewallet = get_user_funds(user_id)
    text = get_welcome_message(user_id, cash, ewallet)
    bot.send_message(message.chat.id, text, reply_markup=main_menu_markup())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if data == "menu_income":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Tulong", callback_data="inc_Tulong"), InlineKeyboardButton("Salary", callback_data="inc_Salary"))
        markup.row(InlineKeyboardButton("Part time", callback_data="inc_Part time"), InlineKeyboardButton("Bonus", callback_data="inc_Bonus"))
        markup.row(InlineKeyboardButton("Others", callback_data="inc_Others"))
        markup.row(InlineKeyboardButton("« Back", callback_data="back_main"))
        bot.edit_message_text("💰 Select Income Category:", chat_id, message_id, reply_markup=markup)

    elif data == "menu_expense":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Kapilya", callback_data="exp_Kapilya"), InlineKeyboardButton("Basic Needs", callback_data="exp_Basic Needs"))
        markup.row(InlineKeyboardButton("Others", callback_data="exp_Others"))
        markup.row(InlineKeyboardButton("« Back", callback_data="back_main"))
        bot.edit_message_text("📉 Select Expense Category:", chat_id, message_id, reply_markup=markup)

    elif data.startswith("exp_"):
        cat = data.split("_")[1]
        if cat == "Kapilya":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("Abuloy", callback_data="sub_Kapilya_Abuloy"), InlineKeyboardButton("TH", callback_data="sub_Kapilya_TH"))
            markup.row(InlineKeyboardButton("Lingap", callback_data="sub_Kapilya_Lingap"), InlineKeyboardButton("Lagak", callback_data="sub_Kapilya_Lagak"))
            markup.row(InlineKeyboardButton("« Back", callback_data="menu_expense"))
            bot.edit_message_text("⛪ Select Kapilya Subcategory:", chat_id, message_id, reply_markup=markup)
        elif cat == "Basic Needs":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("Food", callback_data="sub_Basic_Food"), InlineKeyboardButton("Transportation", callback_data="sub_Basic_Transport"))
            markup.row(InlineKeyboardButton("Medical", callback_data="sub_Basic_Medical"), InlineKeyboardButton("Others", callback_data="sub_Basic_Others"))
            markup.row(InlineKeyboardButton("« Back", callback_data="menu_expense"))
            bot.edit_message_text("🛒 Select Basic Needs Subcategory:", chat_id, message_id, reply_markup=markup)
        else:
            user_states[user_id] = {"type": "expense", "category": "Others", "sub": "", "amount": "0"}
            bot.edit_message_text("Enter amount for Others (Expense):", chat_id, message_id, reply_markup=calculator_markup("0"))

    elif data.startswith("sub_"):
        parts = data.split("_")
        cat = parts[1]
        sub = parts[2]
        user_states[user_id] = {"type": "expense", "category": cat, "sub": sub, "amount": "0"}
        bot.edit_message_text(f"Enter amount for {cat} > {sub}:", chat_id, message_id, reply_markup=calculator_markup("0"))

    elif data.startswith("inc_"):
        cat = data.split("_")[1]
        user_states[user_id] = {"type": "income", "category": cat, "sub": "", "amount": "0"}
        bot.edit_message_text(f"Enter amount for Income ({cat}):", chat_id, message_id, reply_markup=calculator_markup("0"))

    elif data in ["set_cash", "set_ewallet"]:
        target = "Cash" if data == "set_cash" else "E-Wallet"
        user_states[user_id] = {"type": "set", "target": target, "amount": "0"}
        bot.edit_message_text(f"Set initial {target} amount:", chat_id, message_id, reply_markup=calculator_markup("0"))

    elif data.startswith("calc_"):
        action = data.split("_")[1]
        state = user_states.get(user_id)
        if not state:
            bot.answer_callback_query(call.id, "Session expired. Please use /start.")
            return

        current_val = state["amount"]

        if action.isdigit():
            current_val = action if current_val == "0" else current_val + action
        elif action == "dot":
            if "." not in current_val:
                current_val += "."
        elif action == "back":
            current_val = current_val[:-1] if len(current_val) > 1 else "0"
        elif action == "cancel":
            user_states.pop(user_id, None)
            cash, ewallet = get_user_funds(user_id)
            bot.edit_message_text(get_welcome_message(user_id, cash, ewallet), chat_id, message_id, reply_markup=main_menu_markup())
            return
        elif action == "confirm":
            try:
                amt = float(current_val)
            except ValueError:
                amt = 0.0

            st_type = state["type"]
            if st_type == "income":
                update_funds(user_id, cash_delta=amt)
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (user_id, type, category, subcategory, amount) VALUES (?, 'INCOME', ?, '', ?)", (user_id, state["category"], amt))
                conn.commit()
                conn.close()
            elif st_type == "expense":
                update_funds(user_id, cash_delta=-amt)
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (user_id, type, category, subcategory, amount) VALUES (?, 'EXPENSE', ?, ?, ?)", (user_id, state["category"], state["sub"], amt))
                conn.commit()
                conn.close()
            elif st_type == "set":
                if state["target"] == "Cash":
                    cash, ewallet = get_user_funds(user_id)
                    update_funds(user_id, cash_delta=(amt - cash))
                else:
                    cash, ewallet = get_user_funds(user_id)
                    update_funds(user_id, ewallet_delta=(amt - ewallet))

            user_states.pop(user_id, None)
            cash, ewallet = get_user_funds(user_id)
            bot.edit_message_text(f"✅ Transaction Saved Successfully!\n\n" + get_welcome_message(user_id, cash, ewallet), chat_id, message_id, reply_markup=main_menu_markup())
            return

        state["amount"] = current_val
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=calculator_markup(current_val))

    elif data == "back_main":
        cash, ewallet = get_user_funds(user_id)
        bot.edit_message_text(get_welcome_message(user_id, cash, ewallet), chat_id, message_id, reply_markup=main_menu_markup())

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/", methods=['GET'])
def index():
    return "Bot is running!", 200

# Register the webhook when the app is loaded by Gunicorn/Render
if RENDER_URL and TOKEN != "YOUR_NEW_BOT_TOKEN_HERE":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL.rstrip('/')}/{TOKEN}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
