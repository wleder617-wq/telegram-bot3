
import telebot
from telebot import types
import sqlite3
import os
import time
import queue
import threading
from flask import Flask
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import urllib.parse

from premium_emojis import get_emoji_tag
from i18n import get_string, PREMIUM_EMOJI_LINE

# Premium Emojis - Kept exactly as original
E_HAND = get_emoji_tag('WAVE', '👋')
E_HEART = get_emoji_tag('HEART_RED', '❤️')
E_STAR = get_emoji_tag('STAR_GOLD', '⭐')
E_WOW = get_emoji_tag('WOW_FACE', '😮')
E_FIRE = get_emoji_tag('FIRE', '🔥')
E_GIFT = get_emoji_tag('GIFT', '🎁')
E_CHECK = get_emoji_tag('CHECK_MARK', '✅')
E_CHECK_ALT = get_emoji_tag('CHECK_MARK_ALT', '✔️')
E_PLANE = get_emoji_tag('PLANE', '✈️')
E_WINK = get_emoji_tag('WINK', '😉')
E_KISS = get_emoji_tag('KISS', '😘')
E_PLEASE = get_emoji_tag('PLEADING_FACE', '🥺')
E_SPARKLES = get_emoji_tag('STAR_GOLD', '✨')

# Configuration - Kept as original
TOKEN = "8721285488:AAH8XG2wT8Mi3JyUD6jzRWjVnyUWKi6Iysk"
PAYMENT_BOT_TOKEN = "8638636800:AAE8HebDVlk5N28kxiWIgKZdaWSWRdVQHqk"
DATABASE = 'payments_advanced.db'
PROVIDER_TOKEN = '187703658:TEST:5d5b04968f5d1a03e9fc853d6895cf8f8f5254fb'
ADMIN_IDS = [7972155518]
NOTIFY_IDS = [7972155518]

# Enhanced Referral Tiers with Stars from 100+
REFERRAL_TIERS = [
    (1, 3, "🥉 Starter"),
    (2, 5, "🥈 Bronze"),
    (5, 12, "🥇 Silver"),
    (10, 25, "💎 Gold"),
    (25, 62, "👑 Platinum"),
    (50, 125, "💠 Diamond"),
    (100, 250, "🌟 Legend"),
    (200, 500, "🔥 Ultimate"),
    (250, 750, "⚡ Supreme"),
]

# Star Price Packs (Starting from 100 stars)
STAR_PACKS = {
    150: 100,    # 150 Videos = 100 Stars
    250: 150,    # 250 Videos = 150 Stars
    400: 250,    # 400 Videos = 250 Stars
    800: 500,    # 800 Videos = 500 Stars
    1700: 1000,  # 1700 Videos = 1000 Stars
    5000: 3000,  # 5000 Videos = 3000 Stars
    175000: 5000 # 175000 Videos = 5000 Stars
}

def is_admin(user_id):
    return user_id in ADMIN_IDS

bot = telebot.TeleBot(TOKEN)
bot_payment = telebot.TeleBot(PAYMENT_BOT_TOKEN)
BOT_USERNAME = None
app = Flask(__name__)

def setup_bot_commands():
    commands = [
        types.BotCommand("start", "🚀 Start Bot"),
        types.BotCommand("offer", "💎 Special Offers"),
        types.BotCommand("referrals", "👥 Referral System"),
        types.BotCommand("leaderboard", "🏆 Top Referrers"),
        types.BotCommand("stats", "📊 Your Statistics"),
        types.BotCommand("help", "❓ Help & Support"),
        types.BotCommand("motivate", "🔥 Daily Motivation")
    ]
    try:
        bot.set_my_commands(commands)
    except Exception as e:
        print(f"Error setting commands: {e}")

setup_bot_commands()

@app.route('/')
def home():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def init_db():
    print(f"DEBUG: Initializing database at {os.path.abspath(DATABASE)}")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Core tables with enhancements
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT, 
            language TEXT DEFAULT 'en',
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_videos_received INTEGER DEFAULT 0
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER, 
            payment_id TEXT, 
            amount INTEGER, 
            currency TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, payment_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            file_id TEXT NOT NULL, 
            file_name TEXT, 
            file_size INTEGER, 
            duration INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS sent_videos (
            user_id INTEGER, 
            video_id INTEGER,
            sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, video_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER, 
            referred_id INTEGER,
            referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (referred_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS share_rewards (
            user_id INTEGER PRIMARY KEY, 
            rewarded BOOLEAN DEFAULT FALSE,
            reward_date TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY, 
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS gift_claims (
            user_id INTEGER PRIMARY KEY, 
            last_claim_time TIMESTAMP NOT NULL
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_subscriptions (
            user_id INTEGER PRIMARY KEY, 
            days_remaining INTEGER, 
            last_sent_date TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS processed_deep_links (
            link_id TEXT PRIMARY KEY, 
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS milestones (
            user_id INTEGER PRIMARY KEY, 
            total_spent INTEGER DEFAULT 0, 
            rewarded BOOLEAN DEFAULT FALSE
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            admin_id INTEGER, 
            action TEXT, 
            target_id INTEGER, 
            details TEXT, 
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS referral_rewards (
            user_id INTEGER, 
            tier_invites INTEGER, 
            claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            PRIMARY KEY (user_id, tier_invites)
        )''')
        
        # New tables for enhanced features
        cursor.execute('''CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER,
            achievement_name TEXT,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, achievement_name)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_earned_videos INTEGER DEFAULT 0,
            total_purchased_videos INTEGER DEFAULT 0,
            total_spent_stars INTEGER DEFAULT 0,
            days_active INTEGER DEFAULT 0,
            last_activity_date DATE
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS motivation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_text TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            active BOOLEAN DEFAULT TRUE
        )''')
        
        # Indexes for performance
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_sent_videos_user ON sent_videos(user_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_videos_file_id ON videos(file_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)''')
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN language TEXT')
        except sqlite3.OperationalError:
            pass
            
        # Insert default motivation messages if table is empty
        cursor.execute('SELECT COUNT(*) FROM motivation_messages')
        if cursor.fetchone()[0] == 0:
            default_messages = [
                ("🔥 Success is not final, failure is not fatal: it is the courage to continue that counts!", "success"),
                ("💪 The only way to do great work is to love what you do!", "motivation"),
                ("🌟 Believe you can and you're halfway there!", "inspiration"),
                ("🚀 Your limitation—it's only your imagination!", "motivation"),
                ("💎 The harder you work for something, the greater you'll feel when you achieve it!", "success"),
                ("⚡ Push yourself, because no one else is going to do it for you!", "motivation"),
                ("🎯 Dream it. Wish it. Do it!", "inspiration"),
                ("🏆 Success doesn't just find you. You have to go out and get it!", "success"),
                ("🌈 Sometimes later becomes never. Do it now!", "motivation"),
                ("💫 Great things never come from comfort zones!", "inspiration")
            ]
            cursor.executemany('INSERT INTO motivation_messages (message_text, category) VALUES (?, ?)', default_messages)
        
        conn.commit()

def is_banned(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

def ban_user(user_id, reason=""):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO banned_users (user_id, reason) VALUES (?, ?)', (user_id, reason))
        conn.commit()

def unban_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()

def mark_link_used(link_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO processed_deep_links (link_id) VALUES (?)', (link_id,))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

ADMIN_STATES = {}

def save_user(user_id, username):
    is_new = False
    with sqlite3.connect(DATABASE, isolation_level=None) as conn:
        cursor = conn.cursor()
        cursor.execute('BEGIN TRANSACTION')
        try:
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                is_new = True
                cursor.execute('INSERT INTO users (user_id, username, last_seen) VALUES (?, ?, CURRENT_TIMESTAMP)', (user_id, username))
                cursor.execute('INSERT OR IGNORE INTO user_stats (user_id, last_activity_date) VALUES (?, DATE("now"))', (user_id,))
            else:
                cursor.execute('UPDATE users SET username = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?', (username, user_id))
                cursor.execute('UPDATE user_stats SET last_activity_date = DATE("now") WHERE user_id = ?', (user_id,))
            cursor.execute('COMMIT')
        except Exception as e:
            cursor.execute('ROLLBACK')
            print(f"Error saving user: {e}")
    
    if is_new:
        for admin_id in NOTIFY_IDS:
            try:
                bot.send_message(admin_id,
                    f"{E_HEART} <b>New Member Joined!</b>\n\n"
                    f"👤 <b>User:</b> @{escape_html(username) if username else 'N/A'}\n"
                    f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                    f"{E_SPARKLES} <b>Welcome them to the club!</b>",
                    parse_mode='HTML')
            except: pass

def escape_html(text):
    if not text: return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def add_referral(referrer_id, referred_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM referrals WHERE referred_id = ?', (referred_id,))
        if cursor.fetchone(): return False
        cursor.execute('INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)', (referrer_id, referred_id))
        conn.commit()
        
        # Check for achievements
        ref_count = get_referral_count(referrer_id)
        if ref_count >= 1:
            unlock_achievement(referrer_id, 'first_referral')
        if ref_count >= 10:
            unlock_achievement(referrer_id, 'referral_master')
        if ref_count >= 50:
            unlock_achievement(referrer_id, 'referral_king')
        if ref_count >= 100:
            unlock_achievement(referrer_id, 'referral_legend')
        
        return True

def get_referral_count(referrer_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (referrer_id,))
        return cursor.fetchone()[0]

def get_claimed_tiers(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT tier_invites FROM referral_rewards WHERE user_id = ?', (user_id,))
        return [row[0] for row in cursor.fetchall()]

def claim_tier(user_id, tier_invites):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO referral_rewards (user_id, tier_invites) VALUES (?, ?)', (user_id, tier_invites))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def unlock_achievement(user_id, achievement_name):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO achievements (user_id, achievement_name) VALUES (?, ?)', 
                         (user_id, achievement_name))
            if cursor.rowcount > 0:
                conn.commit()
                # Notify user about achievement
                achievement_info = {
                    'first_referral': f"{E_TROPHY} First Referral Achieved!",
                    'referral_master': f"{E_CROWN} Referral Master!",
                    'referral_king': f"{E_DIAMOND} Referral King!",
                    'referral_legend': f"{E_FIRE} Referral Legend!"
                }
                if achievement_name in achievement_info:
                    try:
                        bot.send_message(user_id, 
                            f"{E_PARTY} <b>ACHIEVEMENT UNLOCKED!</b> {E_PARTY}\n\n"
                            f"{achievement_info[achievement_name]}\n"
                            f"{E_SPARKLES} Keep up the great work!",
                            parse_mode='HTML')
                    except: pass
                return True
    except: pass
    return False

def get_user_achievements(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT achievement_name FROM achievements WHERE user_id = ?', (user_id,))
        return [row[0] for row in cursor.fetchall()]

def get_next_tier(ref_count, claimed_tiers):
    for invites_needed, reward, name in REFERRAL_TIERS:
        if invites_needed not in claimed_tiers:
            return (invites_needed, reward, name)
    return None

def get_referral_leaderboard(limit=10):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.referrer_id, u.username, COUNT(*) as ref_count
            FROM referrals r
            LEFT JOIN users u ON r.referrer_id = u.user_id
            GROUP BY r.referrer_id
            ORDER BY ref_count DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

def save_video(file_id, file_name=None, file_size=None, duration=None):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM videos WHERE file_id = ?', (file_id,))
            exists = cursor.fetchone()
            if exists:
                return exists[0]
            cursor.execute('INSERT INTO videos (file_id, file_name, file_size, duration) VALUES (?, ?, ?, ?)', 
                         (file_id, file_name, file_size, duration))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"DB error save_video: {e}")
        return None

def get_unsent_videos(user_id, limit=50):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))

            # First try to get truly unsent videos
            query_unsent = '''
                SELECT v.id, v.file_id 
                FROM videos v 
                LEFT JOIN sent_videos sv ON v.id = sv.video_id AND sv.user_id = ? 
                WHERE sv.video_id IS NULL 
                ORDER BY RANDOM() 
                LIMIT ?
            '''
            cursor.execute(query_unsent, (user_id, limit))
            videos = cursor.fetchall()

            # If we don't have enough unsent videos, fill the rest with random videos (recycling)
            if len(videos) < limit:
                needed = limit - len(videos)
                exclude_ids = [v[0] for v in videos]
                placeholders = ','.join(['?'] * len(exclude_ids))

                query_recycle = f'''
                    SELECT id, file_id 
                    FROM videos 
                    {f"WHERE id NOT IN ({placeholders})" if exclude_ids else ""}
                    ORDER BY RANDOM() 
                    LIMIT ?
                '''
                params = exclude_ids + [needed]
                cursor.execute(query_recycle, params)
                videos.extend(cursor.fetchall())

            return videos[:limit]
    except Exception as e:
        print(f"DB error get_unsent_videos: {e}")
        return []

def save_sent_video(user_id, video_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO sent_videos (user_id, video_id) VALUES (?, ?)', (user_id, video_id))
            cursor.execute('UPDATE user_stats SET total_earned_videos = total_earned_videos + 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    except Exception as e:
        print(f"DB error save_sent_video: {e}")

# Enhanced delivery system with better queue management
delivery_queue = queue.Queue()
delivery_pool = ThreadPoolExecutor(max_workers=20)

def process_delivery(task):
    try:
        if len(task) == 5:
            user_id, video_list, success_callback, failure_callback, admin_msg_id = task
        else:
            user_id, video_list, success_callback, failure_callback = task
            admin_msg_id = None

        total_vids = len(video_list)
        success_count = 0
        
        # Enhanced caption with premium feel
        CAPTION = f"{E_SPARKLES} Premium Video Delivery {E_SPARKLES}\n{E_FIRE} Enjoy your exclusive content!"

        for idx, (v_id, f_id) in enumerate(video_list):
            try:
                time.sleep(0.2)  # Slightly faster delivery
                bot.send_video(user_id, f_id, caption=CAPTION)
                save_sent_video(user_id, v_id)
                success_count += 1

                if admin_msg_id and (success_count % 10 == 0 or success_count == total_vids):
                    for admin_id in NOTIFY_IDS:
                        try:
                            bot.edit_message_text(
                                f"{E_ROCKET} <b>Delivery Progress</b>\n"
                                f"{'═' * 30}\n"
                                f"User ID: <code>{user_id}</code>\n"
                                f"Progress: <b>{success_count}/{total_vids}</b> videos\n"
                                f"Status: <b>Sending...</b>",
                                admin_id, admin_msg_id, parse_mode='HTML'
                            )
                        except: pass
            except Exception as e:
                print(f"Delivery error: {e}")
                if "blocked" in str(e).lower(): 
                    break

        if admin_msg_id:
            for admin_id in NOTIFY_IDS:
                try:
                    bot.edit_message_text(
                        f"{E_CHECK} <b>Delivery Complete!</b>\n"
                        f"{'═' * 30}\n"
                        f"User ID: <code>{user_id}</code>\n"
                        f"Total: <b>{success_count}/{total_vids}</b> videos sent.\n"
                        f"{E_PARTY} Success Rate: {(success_count/total_vids)*100:.1f}%",
                        admin_id, admin_msg_id, parse_mode='HTML'
                    )
                except: pass

        if success_count > 0:
            if success_callback: 
                success_callback(user_id, success_count)
            # Update user stats
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET total_videos_received = total_videos_received + ? WHERE user_id = ?', 
                             (success_count, user_id))
                conn.commit()
        else:
            if failure_callback: 
                failure_callback(user_id)
    except Exception as e:
        print(f"Delivery worker error: {e}")

def delivery_dispatcher():
    while True:
        try:
            task = delivery_queue.get()
            delivery_pool.submit(process_delivery, task)
            delivery_queue.task_done()
        except Exception as e:
            print(f"Dispatcher error: {e}")

threading.Thread(target=delivery_dispatcher, daemon=True).start()

def get_user_language(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else 'en'

def set_user_language(user_id, lang):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
        conn.commit()

def language_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("English 🇺🇸", callback_data="set_lang_en"),
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="set_lang_ru"),
        types.InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="set_lang_hi"),
        types.InlineKeyboardButton("Español 🇪🇸", callback_data="set_lang_es"),
        types.InlineKeyboardButton("Deutsch 🇩🇪", callback_data="set_lang_de"),
        types.InlineKeyboardButton("Português 🇵🇹", callback_data="set_lang_pt")
    )
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def handle_set_lang(call):
    lang = call.data.replace("set_lang_", "")
    set_user_language(call.from_user.id, lang)
    bot.answer_callback_query(call.id, f"Language set to {lang}!")
    handle_back_to_start(call)

def notify_delivery_success(user_id, count):
    lang = get_user_language(user_id)
    try:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(styled_button(get_string('referral_menu', lang), callback_data="referral_menu", style="success"))
        keyboard.add(styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary"))

        bot.send_message(user_id, 
            f"{E_PARTY} {get_string('delivery_success', lang, count=count)}", 
            parse_mode='HTML', reply_markup=keyboard)
    except: pass

def notify_delivery_failure(user_id):
    lang = get_user_language(user_id)
    try: 
        bot.send_message(user_id, get_string('delivery_failed', lang, user_id=user_id), parse_mode='HTML')
    except: pass

def get_total_users():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    except:
        return 0

def get_total_videos():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM videos')
            return cursor.fetchone()[0]
    except:
        return 0

def get_active_users_today():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE date(last_seen) = date('now')")
            return cursor.fetchone()[0]
    except:
        return 0

def styled_button(text, callback_data=None, url=None, style="primary", emoji_id=None):
    btn = types.InlineKeyboardButton(text=text, callback_data=callback_data, url=url)
    original_to_dict = btn.to_dict
    def to_dict():
        data = original_to_dict()
        data['style'] = style
        if emoji_id:
            data['icon_custom_emoji_id'] = emoji_id
        return data
    btn.to_dict = to_dict
    return btn

def get_user_milestone(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT total_spent, rewarded FROM milestones WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row: return row
        return (0, False)

def update_user_milestone(user_id, amount):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO milestones (user_id, total_spent) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET total_spent = total_spent + EXCLUDED.total_spent
        ''', (user_id, amount))
        conn.commit()
        cursor.execute('SELECT total_spent, rewarded FROM milestones WHERE user_id = ?', (user_id,))
        total, rewarded = cursor.fetchone()
        if total >= 750 and not rewarded:
            cursor.execute('UPDATE milestones SET rewarded = TRUE WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
    return False

def log_admin_action(admin_id, action, target_id=None, details=None):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO admin_logs (admin_id, action, target_id, details) VALUES (?, ?, ?, ?)',
                         (admin_id, action, target_id, details))
            conn.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")

def build_referral_progress(ref_count, claimed_tiers):
    lines = []
    for invites_needed, reward, name in REFERRAL_TIERS:
        if invites_needed in claimed_tiers:
            lines.append(f"✅ <b>{name}</b> │ {invites_needed} invites │ {reward} videos │ <b>CLAIMED</b>")
        elif ref_count >= invites_needed:
            lines.append(f"🎁 <b>{name}</b> │ {invites_needed} invites │ {reward} videos │ <b>READY!</b>")
        else:
            progress = min(ref_count / invites_needed * 100, 100)
            lines.append(f"🔒 <b>{name}</b> │ {invites_needed} invites │ {reward} videos │ {ref_count}/{invites_needed} ({progress:.0f}%)")
    return "\n".join(lines)

def get_random_motivation():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT message_text FROM motivation_messages WHERE active = TRUE ORDER BY RANDOM() LIMIT 1')
        result = cursor.fetchone()
        return result[0] if result else f"{E_FIRE} Stay motivated and keep pushing forward!"

def start_keyboard(user_id=None):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    lang = get_user_language(user_id) if user_id else 'en'
    
    # Star emoji for premium feel
    star_id = None
    
    # Row 1: Join Group (Full Width)
    keyboard.add(types.InlineKeyboardButton(
        text=f"{E_ROCKET} Join Our Premium Group {E_ROCKET}", 
        url="https://t.me/+ARG5VlNBj4NhYWE0"
    ))

    # Row 2: Mega Pack (Full Width) - Most attractive offer
    keyboard.add(styled_button(
        text=f"{E_DIAMOND} 175,000 Videos {E_DIAMOND} 💎 5000 Stars", 
        callback_data="buy_175000", 
        style="success"
    ))

    # Row 3: Standard Packs (Two Columns)
    keyboard.add(
        styled_button(text=f"🔥 150 Videos\n⭐ 100 Stars", callback_data="buy_150", style="primary"),
        styled_button(text=f"🔥 400 Videos\n⭐ 250 Stars", callback_data="buy_400", style="primary")
    )
    
    keyboard.add(
        styled_button(text=f"⚡ 800 Videos\n⭐ 500 Stars", callback_data="buy_800", style="primary"),
        styled_button(text=f"💎 1700 Videos\n⭐ 1000 Stars", callback_data="buy_1700", style="primary")
    )

    if user_id:
        ref_count = get_referral_count(user_id)
        claimed_tiers = get_claimed_tiers(user_id)
        next_tier = get_next_tier(ref_count, claimed_tiers)

        global BOT_USERNAME
        if not BOT_USERNAME:
            try:
                me = bot.get_me()
                BOT_USERNAME = me.username
            except:
                BOT_USERNAME = "bot"

        invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        share_text = f"🔥 Premium Video Bot Alert! 🎬\n\nGet FREE exclusive videos!\nInvite friends & earn rewards!\nInstant premium delivery!\n\nJoin now 👇\n{invite_link}"
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text={urllib.parse.quote(share_text)}"

        has_claimable = any(ref_count >= inv and inv not in claimed_tiers for inv, _, _ in REFERRAL_TIERS)

        # Row 4: Claim Rewards (if available)
        if has_claimable:
            keyboard.add(styled_button(
                text=f"{E_GIFT} Claim Your Rewards Now! {E_GIFT}", 
                callback_data="claim_rewards", 
                style="danger"
            ))

        # Row 5: Invite Friends
        if next_tier:
            invites_needed, reward, name = next_tier
            keyboard.add(styled_button(
                text=f"{E_WAVE} Invite Friends & Earn ({ref_count}/{invites_needed})", 
                url=share_url, 
                style="success"
            ))
        else:
            keyboard.add(styled_button(
                text=f"{E_CROWN} All Tiers Complete! ({ref_count})", 
                url=share_url, 
                style="success"
            ))

        # Row 6: Referral Menu & Leaderboard
        keyboard.add(
            styled_button(text=f"{E_HEART} Referrals ({ref_count})", callback_data="referral_menu", style="primary"),
            styled_button(text=f"{E_TROPHY} Leaderboard", callback_data="leaderboard", style="primary")
        )

    # Row 7: Offers & Achievements
    keyboard.add(
        styled_button(text=f"{E_FIRE} Special Offers", callback_data="offer_menu", style="success"),
        styled_button(text=f"{E_STAR} Achievements", callback_data="achievements_menu", style="primary")
    )

    # Row 8: Language & Help
    keyboard.add(
        types.InlineKeyboardButton(f"🌐 Language", callback_data="change_lang"),
        types.InlineKeyboardButton(f"❓ Help", callback_data="help_menu")
    )

    if user_id and is_admin(user_id):
        total_users = get_total_users()
        total_vids = get_total_videos()
        keyboard.add(styled_button(
            text=f"👑 Admin Panel [Users: {total_users} | Videos: {total_vids}]", 
            callback_data="admin_panel", 
            style="danger"
        ))

    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def handle_back_to_start(call):
    lang = get_user_language(call.from_user.id)
    welcome_text = get_string('welcome', lang)
    
    # Add random motivation
    motivation = get_random_motivation()
    welcome_text += f"\n\n{motivation}"
    
    try:
        bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=start_keyboard(call.from_user.id),
            parse_mode='HTML'
        )
    except:
        try: 
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, 
                                        reply_markup=start_keyboard(call.from_user.id))
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "change_lang")
def handle_change_lang(call):
    lang = get_user_language(call.from_user.id)
    bot.edit_message_text(
        get_string('select_language', lang),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=language_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == "help_menu")
def handle_help_menu(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    
    help_text = f"""
{E_SPARKLES} <b>PREMIUM VIDEO BOT HELP</b> {E_SPARKLES}

<b>📚 Available Commands:</b>

🚀 /start - Start the bot
💎 /offer - View special offers
👥 /referrals - Referral system
🏆 /leaderboard - Top referrers
📊 /stats - Your statistics
🏅 /achievements - Your achievements
🔥 /motivate - Daily motivation
❓ /help - This help menu

<b>💡 How to Earn Videos:</b>
• Invite friends using your referral link
• Complete achievement milestones
• Purchase premium packs
• Claim referral rewards

<b>⭐ Stars System (100+ stars):</b>
• 100 Stars = 150 Videos
• 250 Stars = 400 Videos
• 500 Stars = 800 Videos
• 1000 Stars = 1700 Videos
• 5000 Stars = 175,000 Videos

{E_HEART} <b>Need more help?</b> Contact our support team!
    """
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button("🔙 Back to Main Menu", callback_data="back_to_start", style="primary"))
    
    try:
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, help_text, reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "achievements_menu")
def handle_achievements_menu(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    achievements = get_user_achievements(user_id)
    ref_count = get_referral_count(user_id)
    
    all_achievements = {
        'first_referral': {'name': f'{E_STAR} First Referral', 'desc': 'Get your first referral'},
        'referral_master': {'name': f'{E_CROWN} Referral Master', 'desc': 'Reach 10 referrals'},
        'referral_king': {'name': f'{E_DIAMOND} Referral King', 'desc': 'Reach 50 referrals'},
        'referral_legend': {'name': f'{E_FIRE} Referral Legend', 'desc': 'Reach 100 referrals'}
    }
    
    text = f"{E_TROPHY} <b>YOUR ACHIEVEMENTS</b> {E_TROPHY}\n{'═' * 30}\n\n"
    
    for ach_id, ach_info in all_achievements.items():
        if ach_id in achievements:
            text += f"✅ {ach_info['name']} - <b>UNLOCKED</b>\n"
        else:
            text += f"🔒 {ach_info['name']} - <i>{ach_info['desc']}</i>\n"
    
    text += f"\n{E_SPARKLES} <b>Total Referrals:</b> {ref_count}\n"
    text += f"{E_STAR} Keep going to unlock all achievements!"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button("🔙 Back to Main Menu", callback_data="back_to_start", style="primary"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def handle_admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Access denied!")
        return
    
    total_users = get_total_users()
    total_vids = get_total_videos()
    active_today = get_active_users_today()
    
    admin_text = f"""
{E_CROWN} <b>ADMIN CONTROL PANEL</b> {E_CROWN}
{'═' * 30}

📊 <b>Quick Statistics:</b>
• 👥 Total Users: <b>{total_users}</b>
• 📹 Total Videos: <b>{total_vids}</b>
• 📈 Active Today: <b>{active_today}</b>

🛠 <b>Admin Commands:</b>
• /add - Add new videos
• /done - Finish adding videos
• /videos - Video library stats
• /stats - Bot statistics
• /users_count - User count
• /ban [user_id] - Ban user
• /unban [user_id] - Unban user
• /send_v [user_id] [count] - Send videos
• /top_referrers - View top referrers
• /broadcast_all [message] - Broadcast message
• /promo - Generate promo message
• /logs - View admin logs
• /buyers - Top buyers list
• /db_debug - Database debug

{E_FIRE} <b>Bot is running smoothly!</b>
    """
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        styled_button("📊 Quick Stats", callback_data="none", style="primary"),
        styled_button("📹 Video Stats", callback_data="none", style="primary"),
        styled_button("👥 User List", callback_data="none", style="primary"),
        styled_button("🔙 Back", callback_data="back_to_start", style="danger")
    )
    
    try:
        bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, admin_text, reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "offer_menu")
def handle_offer_menu(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        styled_button(f"⭐ 100 Stars ➔ 150 Videos {E_FIRE}", callback_data="buy_150"),
        styled_button(f"⭐ 250 Stars ➔ 400 Videos {E_SPARKLES}", callback_data="buy_400"),
        styled_button(f"⭐ 500 Stars ➔ 800 Videos {E_DIAMOND}", callback_data="buy_800"),
        styled_button(f"⭐ 1000 Stars ➔ 1700 Videos {E_CROWN}", callback_data="buy_1700"),
        styled_button(f"⭐ 5000 Stars ➔ 175,000 Videos {E_ROCKET}", callback_data="buy_175000"),
        styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary")
    )

    offer_text = f"""
{PREMIUM_EMOJI_LINE}
{E_STAR} <b>PREMIUM VIDEO PACKAGES</b> {E_STAR}
{'═' * 30}

{E_FIRE} Choose your perfect package and get instant delivery!

{E_GIFT} <b>Special Bonus:</b> Get extra videos on large purchases!
{E_SPARKLES} All packages include premium quality content
    """
    
    bot.edit_message_text(
        offer_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['offer'])
def handle_offer_command(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        styled_button(f"⭐ 100 Stars ➔ 150 Videos {E_FIRE}", callback_data="buy_150"),
        styled_button(f"⭐ 250 Stars ➔ 400 Videos {E_SPARKLES}", callback_data="buy_400"),
        styled_button(f"⭐ 500 Stars ➔ 800 Videos {E_DIAMOND}", callback_data="buy_800"),
        styled_button(f"⭐ 1000 Stars ➔ 1700 Videos {E_CROWN}", callback_data="buy_1000"),
        styled_button(f"⭐ 5000 Stars ➔ 175,000 Videos {E_ROCKET}", callback_data="buy_175000"),
        styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary")
    )

    bot.send_message(
        message.chat.id,
        f"{PREMIUM_EMOJI_LINE}\n{E_STAR} <b>Premium Video Packages</b> {E_STAR}\n\nChoose your package and get instant delivery!",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_payment_request(call):
    user_id = call.from_user.id
    try:
        count = int(call.data.replace("buy_", ""))
    except ValueError:
        return

    # Map video counts to Star prices
    stars_price = STAR_PACKS.get(count, count)

    try:
        invoice_link = bot_payment.create_invoice_link(
            title=f"Premium Video Pack ({count})",
            description=f"Get {count} exclusive premium videos instantly!",
            payload=f"deliver_{user_id}_{count}",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label=f"{count} Premium Videos", amount=stars_price)]
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            text=f"{E_STAR} Pay {stars_price} Stars", 
            url=invoice_link
        ))
        bot.send_message(
            call.message.chat.id,
            f"{E_FIRE} <b>Premium Video Pack: {count} Videos</b>\n\n"
            f"{E_STAR} Price: <b>{stars_price} Stars</b>\n\n"
            f"{E_ROCKET} Press the button below to complete your purchase:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error creating invoice link: {e}")
        prices = [types.LabeledPrice(label=f"{count} Premium Videos", amount=stars_price)]
        bot.send_invoice(
            call.message.chat.id,
            title=f"Premium Video Pack ({count})",
            description=f"Get {count} exclusive premium videos instantly!",
            invoice_payload=f"deliver_{user_id}_{count}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="premium_videos"
        )

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "referral_menu")
def handle_referral_menu(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)

    global BOT_USERNAME
    if not BOT_USERNAME: 
        BOT_USERNAME = bot.get_me().username
    
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    share_text = f"🔥 Premium Video Bot - Get FREE videos! 🎬\n\n✨ Invite friends & earn up to 1000+ videos!\n⭐ Premium content delivered instantly!\n\n👇 Join now 👇\n{invite_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text={urllib.parse.quote(share_text)}"

    total_earned = sum(reward for inv, reward, _ in REFERRAL_TIERS if inv in claimed_tiers)
    progress_text = build_referral_progress(ref_count, claimed_tiers)

    text = f"""
{PREMIUM_EMOJI_LINE}
{E_CROWN} <b>REFERRAL DASHBOARD</b> {E_CROWN}
{'═' * 30}

{E_WAVE} <b>Total Invites:</b> <code>{ref_count}</code>
{E_GIFT} <b>Videos Earned:</b> <code>{total_earned}</code>

{'═' * 30}
{progress_text}
{'═' * 30}

{E_LINK} <b>Your Invite Link:</b>
<code>{invite_link}</code>

{E_FIRE} <b>Share this link to earn FREE videos!</b>
    """

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(styled_button(f"{E_WAVE} Share Link & Earn", url=share_url, style="success"))

    has_claimable = any(
        ref_count >= inv and inv not in claimed_tiers
        for inv, _, _ in REFERRAL_TIERS
    )
    if has_claimable:
        keyboard.add(styled_button(f"{E_GIFT} Claim Your Rewards!", callback_data="claim_rewards", style="danger"))

    keyboard.add(styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        try: 
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "claim_rewards")
def handle_claim_rewards(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)

    total_videos_to_deliver = 0
    tiers_to_claim = []

    for invites_needed, reward, name in REFERRAL_TIERS:
        if ref_count >= invites_needed and invites_needed not in claimed_tiers:
            total_videos_to_deliver += reward
            tiers_to_claim.append((invites_needed, reward, name))

    if total_videos_to_deliver == 0:
        bot.answer_callback_query(call.id, get_string('no_rewards', lang), show_alert=True)
        return

    unsent = get_unsent_videos(user_id, limit=total_videos_to_deliver)
    if not unsent:
        bot.answer_callback_query(call.id, get_string('no_videos', lang), show_alert=True)
        return

    tiers_claimed_now = []
    for invites_needed, reward, name in tiers_to_claim:
        if claim_tier(user_id, invites_needed):
            tiers_claimed_now.append((name, reward))

    if not tiers_claimed_now:
        bot.answer_callback_query(call.id, "Rewards already claimed!", show_alert=True)
        return

    tier_text = "\n".join([f"✅ {name}: +{reward} videos" for name, reward in tiers_claimed_now])
    bot.answer_callback_query(call.id, get_string('delivering_now', lang, count=len(unsent)))

    bot.send_message(user_id,
        f"{E_PARTY} <b>REWARDS CLAIMED!</b> {E_PARTY}\n"
        f"{'═' * 30}\n\n"
        f"{tier_text}\n\n"
        f"{E_GIFT} Total incoming: <b>{len(unsent)} videos</b>",
        parse_mode='HTML')

    delivery_queue.put((user_id, unsent, notify_delivery_success, notify_delivery_failure, None))

    for admin_id in NOTIFY_IDS:
        try:
            bot.send_message(admin_id,
                f"{E_GIFT} <b>Referral Reward Claimed!</b>\n\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"👥 Invites: {ref_count}\n"
                f"📦 Videos: {len(unsent)}\n"
                f"🏆 Tiers: {', '.join([n for n, _ in tiers_claimed_now])}",
                parse_mode='HTML')
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def handle_leaderboard(call):
    lang = get_user_language(call.from_user.id)
    leaders = get_referral_leaderboard(10)

    if not leaders:
        text = f"{E_TROPHY} <b>LEADERBOARD</b>\n{'═' * 30}\n\nNo leaders yet! Be the first!"
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []
        for i, (uid, uname, count) in enumerate(leaders):
            medal = medals[i] if i < len(medals) else f"#{i+1}"
            display = f"@{uname}" if uname else f"ID:{uid}"
            lines.append(f"{medal} {display} — <b>{count}</b> invites")

        text = f"""
{E_TROPHY} <b>TOP REFERRERS</b> {E_TROPHY}
{'═' * 30}

{chr(10).join(lines)}

{E_FIRE} Invite friends to climb the ranks!
        """

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        try: 
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "none")
def handle_none(call):
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: is_banned(message.from_user.id))
def handle_banned(message):
    bot.send_message(message.chat.id, f"{E_LOCK} You are banned from using this bot.")

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    is_new = False

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone(): 
            is_new = True
            save_user(user_id, username)
            bot.send_message(message.chat.id, 
                f"{E_GLOBE} Please select your language:", 
                reply_markup=language_keyboard())
            # Process referral if exists
            args = message.text.split()
            if len(args) > 1 and args[1].isdigit():
                referrer_id = int(args[1])
                if referrer_id != user_id:
                    if add_referral(referrer_id, user_id):
                        try:
                            bot.send_message(referrer_id, 
                                f"{E_PARTY} <b>New Referral!</b> {E_PARTY}\n\n"
                                f"Someone joined using your link!\n"
                                f"{E_GIFT} Check /referrals for rewards!",
                                parse_mode='HTML')
                        except: pass
            return

    save_user(user_id, username)
    lang = get_user_language(user_id)
    welcome_text = get_string('welcome', lang)
    
    # Add daily motivation
    motivation = get_random_motivation()
    welcome_text += f"\n\n{motivation}"
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=start_keyboard(user_id))

@bot.message_handler(commands=['referrals', 'stats'])
def handle_referral_stats(message):
    user_id = message.from_user.id
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)
    
    global BOT_USERNAME
    if not BOT_USERNAME: BOT_USERNAME = bot.get_me().username
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    progress_text = build_referral_progress(ref_count, claimed_tiers)
    total_earned = sum(reward for inv, reward, _ in REFERRAL_TIERS if inv in claimed_tiers)
    achievements = get_user_achievements(user_id)

    text = f"""
{E_TROPHY} <b>YOUR STATISTICS</b> {E_TROPHY}
{'═' * 30}

{E_WAVE} <b>Total Invites:</b> <code>{ref_count}</code>
{E_GIFT} <b>Videos Earned:</b> <code>{total_earned}</code>
{E_STAR} <b>Achievements:</b> <code>{len(achievements)}</code>

{'═' * 30}
{progress_text}
{'═' * 30}

{E_LINK} <b>Your Invite Link:</b>
<code>{invite_link}</code>
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['motivate'])
def handle_motivate(message):
    user_id = message.from_user.id
    
    # Get random motivation
    motivation = get_random_motivation()
    
    # Create motivational message
    text = f"""
{E_FIRE} <b>DAILY MOTIVATION</b> {E_FIRE}
{'═' * 30}

{motivation}

{'═' * 30}
{E_SPARKLES} <b>Keep pushing forward!</b>
{E_STAR} You're doing great!
    """
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button(f"{E_FIRE} Get Another Quote", callback_data="get_motivation", style="primary"))
    keyboard.add(styled_button("🔙 Main Menu", callback_data="back_to_start", style="primary"))
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_motivation")
def handle_get_motivation(call):
    motivation = get_random_motivation()
    text = f"""
{E_FIRE} <b>MOTIVATION</b> {E_FIRE}
{'═' * 30}

{motivation}

{'═' * 30}
{E_SPARKLES} <b>You can do it!</b>
    """
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button(f"{E_FIRE} Another One!", callback_data="get_motivation", style="primary"))
    keyboard.add(styled_button("🔙 Main Menu", callback_data="back_to_start", style="primary"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                            reply_markup=keyboard, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard, parse_mode='HTML')

# Keep all the remaining functions from the original script...
# [All the original functions preserved: check, logs, buyers, payment handlers, admin commands, etc.]

# Payment handlers
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    payload = message.successful_payment.invoice_payload
    username = message.from_user.username
    
    if payload.startswith("deliver_"):
        parts = payload.split('_')
        count = int(parts[2])
        unsent = get_unsent_videos(user_id, limit=count)
        if unsent:
            bot.send_message(user_id, 
                f"{E_CHECK} {get_string('payment_success', lang, count=len(unsent))}", 
                parse_mode='HTML')

            admin_msg_id = None
            for admin_id in NOTIFY_IDS:
                try:
                    alert = (f"{E_STAR} <b>New Purchase!</b>\n\n"
                            f"👤 User: @{username if username else 'N/A'}\n"
                            f"🆔 ID: <code>{user_id}</code>\n"
                            f"💰 Amount: {message.successful_payment.total_amount} {message.successful_payment.currency}\n"
                            f"📦 Package: {len(unsent)} Videos\n"
                            f"{'═' * 30}\n"
                            f"⏳ Status: <b>Starting delivery...</b>")
                    sent_msg = bot.send_message(admin_id, alert, parse_mode='HTML')
                    admin_msg_id = sent_msg.message_id
                except: pass

            delivery_queue.put((user_id, unsent, notify_delivery_success, notify_delivery_failure, admin_msg_id))

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO payments (user_id, payment_id, amount, currency) VALUES (?, ?, ?, ?)',
                             (user_id, message.successful_payment.telegram_payment_charge_id,
                              message.successful_payment.total_amount, message.successful_payment.currency))
                conn.commit()

            if update_user_milestone(user_id, message.successful_payment.total_amount):
                bonus_vids = get_unsent_videos(user_id, limit=100)
                if bonus_vids:
                    bot.send_message(user_id, 
                        f"{E_PARTY} <b>MILESTONE REACHED!</b> {E_PARTY}\n\n"
                        f"You've reached <b>750 Stars</b> milestone! {E_TROPHY}\n"
                        f"Here are <b>100 BONUS Premium Videos</b>! {E_GIFT}", 
                        parse_mode='HTML')
                    delivery_queue.put((user_id, bonus_vids, notify_delivery_success, notify_delivery_failure, None))
                    for admin_id in NOTIFY_IDS:
                        try: 
                            bot.send_message(admin_id, 
                                f"{E_TROPHY} User {user_id} reached 750 Stars milestone and received 100 bonus videos!")
                        except: pass

# Admin Commands (preserved from original)
@bot.message_handler(commands=['check'])
def handle_check_referral(message):
    user_id = message.from_user.id
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)

    global BOT_USERNAME
    if not BOT_USERNAME: BOT_USERNAME = bot.get_me().username
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    progress_text = build_referral_progress(ref_count, claimed_tiers)
    total_earned = sum(reward for inv, reward, _ in REFERRAL_TIERS if inv in claimed_tiers)

    text = (f"{E_TROPHY} <b>YOUR REFERRAL PROGRESS</b>\n"
            f"{'═' * 30}\n\n"
            f"👥 <b>Total Invites:</b> <code>{ref_count}</code>\n"
            f"🎁 <b>Videos Earned:</b> <code>{total_earned}</code>\n\n"
            f"{progress_text}\n\n"
            f"🔗 <b>Invite Link:</b>\n<code>{invite_link}</code>")
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['logs'])
def handle_view_logs(message):
    if not is_admin(message.from_user.id): return
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.admin_id, u.username, al.action, al.target_id, al.timestamp 
                FROM admin_logs al
                LEFT JOIN users u ON al.admin_id = u.user_id
                ORDER BY al.timestamp DESC 
                LIMIT 20
            ''')
            logs = cursor.fetchall()

        if not logs:
            bot.reply_to(message, "No admin logs found.")
            return

        text = f"📜 <b>Recent Admin Activity</b>\n{'═' * 30}\n\n"
        for aid, uname, action, target, ts in logs:
            admin_display = f"@{uname}" if uname else f"ID:{aid}"
            target_display = f" (Target: {target})" if target else ""
            text += f"👤 {admin_display}\n└ <b>{action}</b>{target_display}\n🕐 <code>{ts}</code>\n\n"

        bot.send_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['buyers'])
def handle_buyers_list(message):
    if not is_admin(message.from_user.id): return
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.username, m.total_spent 
            FROM users u
            JOIN milestones m ON u.user_id = m.user_id
            WHERE m.total_spent > 0
            ORDER BY m.total_spent DESC
            LIMIT 50
        ''')
        buyers = cursor.fetchall()

    if not buyers:
        bot.reply_to(message, "No buyers found yet.")
        return

    text = f"💰 <b>Top Buyers</b>\n{'═' * 30}\n\n"
    for uid, uname, spent in buyers:
        user_display = f"@{uname}" if uname else f"ID:{uid}"
        text += f"👤 {user_display}\n└ <code>{spent}</code> Stars\n\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['db_debug'])
def handle_db_debug(message):
    if not is_admin(message.from_user.id): return
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            total_refs = cursor.execute('SELECT COUNT(*) FROM referrals').fetchone()[0]
            top_5 = cursor.execute('''
                SELECT referrer_id, COUNT(*) as c 
                FROM referrals 
                GROUP BY referrer_id 
                ORDER BY c DESC 
                LIMIT 5
            ''').fetchall()

        text = "🔍 <b>Live DB Debug</b>\n"
        text += f"Total Referrals: {total_refs}\n\n"
        for rid, count in top_5:
            text += f"ID: <code>{rid}</code> - <b>{count}</b> invites\n"

        bot.reply_to(message, text, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['users_count'])
def handle_users_count(message):
    if not is_admin(message.from_user.id): return
    count = get_total_users()
    active = get_active_users_today()
    bot.reply_to(message, 
        f"📊 <b>User Statistics</b>\n\n"
        f"👥 Total registered users: <code>{count}</code>\n"
        f"📈 Active today: <code>{active}</code>", 
        parse_mode='HTML')

@bot.message_handler(commands=['add'])
def handle_add_video(message):
    if not is_admin(message.from_user.id): return
    ADMIN_STATES[message.from_user.id] = 'WAITING_VIDEO'
    bot.send_message(message.chat.id, "📤 Send the videos you want to add. Type /done when finished.")

@bot.message_handler(content_types=['video'])
def handle_video_upload(message):
    if not is_admin(message.from_user.id) or ADMIN_STATES.get(message.from_user.id) != 'WAITING_VIDEO': return
    file_id = message.video.file_id
    file_name = message.video.file_name
    file_size = message.video.file_size
    duration = message.video.duration
    video_id = save_video(file_id, file_name, file_size, duration)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        total_vids = cursor.execute('SELECT COUNT(*) FROM videos').fetchone()[0]

    bot.reply_to(message, f"{E_CHECK} Video added! (Total: {total_vids})")

@bot.message_handler(commands=['done'])
def handle_done(message):
    if not is_admin(message.from_user.id): return
    ADMIN_STATES[message.from_user.id] = None
    bot.send_message(message.chat.id, f"{E_CHECK} Upload session finished.")

@bot.message_handler(commands=['videos'])
def handle_videos_list(message):
    if not is_admin(message.from_user.id): return
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        total_vids = cursor.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
        today_vids = cursor.execute("SELECT COUNT(*) FROM videos WHERE date(added_date) = date('now')").fetchone()[0]
        week_vids = cursor.execute("SELECT COUNT(*) FROM videos WHERE added_date >= datetime('now', '-7 days')").fetchone()[0]

    text = (f"📹 <b>Video Library Stats</b>\n"
            f"{'═' * 30}\n\n"
            f"📊 <b>Total Videos:</b> <code>{total_vids}</code>\n"
            f"📅 <b>Added Today:</b> <code>{today_vids}</code>\n"
            f"🗓️ <b>Added This Week:</b> <code>{week_vids}</code>\n\n"
            f"✨ Your library is growing!")
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def handle_admin_stats(message):
    if not is_admin(message.from_user.id): return
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        total_users = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_vids = cursor.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
        purchases = cursor.execute('SELECT COUNT(*) FROM payments').fetchone()[0]
        total_referrals = cursor.execute('SELECT COUNT(*) FROM referrals').fetchone()[0]
        total_rewards_claimed = cursor.execute('SELECT COUNT(*) FROM referral_rewards').fetchone()[0]
        active_today = cursor.execute("SELECT COUNT(*) FROM users WHERE date(last_seen) = date('now')").fetchone()[0]
    
    bot.send_message(message.chat.id,
        f"📊 <b>Bot Statistics</b>\n{'═' * 30}\n\n"
        f"👥 Users: {total_users}\n"
        f"📈 Active Today: {active_today}\n"
        f"📹 Videos: {total_vids}\n"
        f"🛒 Purchases: {purchases}\n"
        f"👥 Referrals: {total_referrals}\n"
        f"🎁 Rewards Claimed: {total_rewards_claimed}",
        parse_mode='HTML')

@bot.message_handler(commands=['ban'])
def handle_ban_command(message):
    if not is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: /ban <user_id> [reason]")
            return
        target_id = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"
        ban_user(target_id, reason)
        bot.reply_to(message, f"✅ User {target_id} has been banned.\nReason: {reason}")
        log_admin_action(message.from_user.id, "BAN", target_id=target_id, details=reason)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['unban'])
def handle_unban_command(message):
    if not is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: /unban <user_id>")
            return
        target_id = int(args[1])
        unban_user(target_id)
        bot.reply_to(message, f"✅ User {target_id} has been unbanned.")
        log_admin_action(message.from_user.id, "UNBAN", target_id=target_id)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['send_v'])
def handle_send_v(message):
    if not is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "Usage: /send_v <user_id> <count>")
            return
        target_id = int(args[1])
        video_count = int(args[2])
        unsent = get_unsent_videos(target_id, limit=video_count)
        if not unsent:
            bot.reply_to(message, "No new videos available for this user.")
            return

        status_msg = bot.send_message(message.chat.id,
            f"🚀 <b>Starting Manual Delivery...</b>\n"
            f"Target: <code>{target_id}</code>\n"
            f"Count: {len(unsent)}", parse_mode='HTML')

        delivery_queue.put((target_id, unsent, notify_delivery_success, notify_delivery_failure, status_msg.message_id))
        log_admin_action(message.from_user.id, "SEND_V", target_id=target_id, details=f"Count: {video_count}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['top_referrers'])
def handle_top_referrers(message):
    if not is_admin(message.from_user.id): return
    leaders = get_referral_leaderboard(20)

    if not leaders:
        bot.reply_to(message, "No referrals yet.")
        return

    text = f"🏆 <b>Top Referrers (Admin View)</b>\n{'═' * 30}\n\n"
    for i, (uid, uname, count) in enumerate(leaders):
        display = f"@{uname}" if uname else f"ID:{uid}"
        text += f"#{i+1} {display} — <b>{count}</b> invites (ID: <code>{uid}</code>)\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['broadcast_all'])
def handle_broadcast(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /broadcast_all <message>")
        return

    broadcast_text = args[1]
    conn = sqlite3.connect(DATABASE)
    users = [r[0] for r in conn.execute('SELECT user_id FROM users').fetchall()]
    conn.close()

    success, fail = 0, 0
    for uid in users:
        try:
            bot.send_message(uid, broadcast_text, parse_mode='HTML')
            success += 1
            time.sleep(0.05)
        except:
            fail += 1

    bot.reply_to(message, f"📢 Broadcast Complete!\n✅ Success: {success}\n❌ Failed: {fail}")
    log_admin_action(message.from_user.id, "BROADCAST_ALL", details=f"Success: {success}, Failed: {fail}")

@bot.message_handler(commands=['promo'])
def handle_promo(message):
    if not is_admin(message.from_user.id): return

    fire_line = "🔥" * 15
    star_line = "⭐" * 15
    diamond_line = "💎" * 15

    promo_text = (f"{fire_line}\n\n"
        f"🎬 <b>PREMIUM EXCLUSIVE VIDEOS</b> 🎬\n"
        f"{'═' * 30}\n\n"
        f"👑 <b>The #1 Premium Video Bot on Telegram!</b>\n\n"
        f"💎 <b>What You Get:</b>\n"
        f"├ 🎥 High-quality exclusive content\n"
        f"├ ⚡ Instant delivery to your chat\n"
        f"├ 🎁 FREE videos through referrals\n"
        f"├ 🏆 9 reward tiers to unlock\n"
        f"└ ⭐ Starting from 100 Stars!\n\n"
        f"{star_line}\n\n"
        f"👥 <b>INVITE & EARN FREE VIDEOS:</b>\n\n"
        f"🥉 1 invite = 3 free videos\n"
        f"🥈 2 invites = 5 free videos\n"
        f"🥇 5 invites = 12 free videos\n"
        f"💎 10 invites = 25 free videos\n"
        f"👑 25 invites = 62 free videos\n"
        f"💠 50 invites = 125 free videos\n"
        f"🌟 100 invites = 250 free videos\n"
        f"🔥 200 invites = 500 free videos\n"
        f"⚡ 250 invites = 750 free videos\n\n"
        f"<b>Join our channel:</b> https://t.me/+Mx69KEAaOa8zOTBi\n\n"
        f"{diamond_line}\n\n"
        f"🔥 <b>TOTAL: Up to 1960 FREE VIDEOS!</b> 🔥\n\n"
        f"👇 <b>TAP BELOW TO START NOW!</b> 👇")

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 START THE BOT NOW 🚀", url="https://t.me/Llllppppooottt_bot?start=promo"))

    bot.send_message(message.chat.id, promo_text, parse_mode='HTML', reply_markup=keyboard)
    log_admin_action(message.from_user.id, "PROMO_GENERATED")

@bot.message_handler(commands=['dee'])
def handle_dee_command(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text=f"BUY NOW ⭐ 399 Stars",
        callback_data="buy_499_special"
    ))

    offer_text = (f"🔥 <b>EXCLUSIVE LIMITED OFFER!</b> 🔥\n\n"
        f"Unlock <b>499 Premium Videos</b> 🎁\n"
        f"For only <b>399 Stars</b> ⭐\n\n"
        f"⚡ <i>Instant Delivery guaranteed!</i>")
    bot.send_message(message.chat.id, offer_text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_499_special")
def handle_buy_499(call):
    user_id = call.from_user.id
    try:
        invoice_link = bot_payment.create_invoice_link(
            title="Special Offer: 499 Videos",
            description="Get 499 high-quality premium videos instantly!",
            payload=f"deliver_{user_id}_499",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label="499 Videos", amount=399)]
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="⭐ Pay 399 Stars", url=invoice_link))
        bot.send_message(
            call.message.chat.id,
            "🎬 <b>Special Offer: 499 Videos</b>\n\n⭐ Price: <b>399 Stars</b>\n\nPress the button below to complete your purchase:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error creating invoice link: {e}")
        bot.send_invoice(
            call.message.chat.id,
            title="Special Offer: 499 Videos",
            description="Get 499 high-quality premium videos instantly!",
            invoice_payload=f"deliver_{user_id}_499",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label="499 Videos", amount=399)],
            start_parameter="special_offer_499"
        )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    save_user(message.from_user.id, message.from_user.username)

# Payment bot handlers
@bot_payment.pre_checkout_query_handler(func=lambda query: True)
def payment_checkout(pre_checkout_query):
    bot_payment.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot_payment.message_handler(content_types=['successful_payment'])
def payment_got_payment(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        amount = message.successful_payment.total_amount
        currency = message.successful_payment.currency
        charge_id = message.successful_payment.telegram_payment_charge_id
        lang = get_user_language(user_id)

        for admin_id in NOTIFY_IDS:
            try:
                bot.send_message(admin_id,
                    f"💰 <b>New Payment Received!</b>\n\n"
                    f"👤 <b>User:</b> @{escape_html(username) if username else 'N/A'}\n"
                    f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                    f"💵 <b>Amount:</b> <code>{amount}</code> {currency}\n"
                    f"🧾 <b>Charge ID:</b> <code>{charge_id}</code>",
                    parse_mode='HTML')
            except: pass

        payload = message.successful_payment.invoice_payload
        try:
            video_count = int(payload.split("_")[-1])
        except Exception:
            video_count = 7

        unsent = get_unsent_videos(user_id, limit=video_count)
        if unsent:
            bot.send_message(user_id, get_string('payment_success', lang, count=len(unsent)), parse_mode='HTML')
            delivery_queue.put((user_id, unsent, notify_delivery_success, notify_delivery_failure, None))

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO payments (user_id, payment_id, amount, currency) VALUES (?, ?, ?, ?)',
                             (user_id, charge_id, amount, currency))
                conn.commit()
    except Exception as e:
        print(f"Error in payment_got_payment: {e}")

def run_payment_bot():
    while True:
        try:
            bot_payment.delete_webhook(drop_pending_updates=True)
            time.sleep(1)
            bot_payment.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Payment bot polling error: {e}")
            time.sleep(5)

# Initialize and run
init_db()
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

payment_thread = Thread(target=run_payment_bot)
payment_thread.daemon = True
payment_thread.start()

print(f"{E_FIRE} Premium Video Bot v3.0 is starting... {E_FIRE}")

while True:
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        bot.polling(non_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(5)
