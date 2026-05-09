import telebot
from telebot import types
import sqlite3
import os
import time
import random
from flask import Flask
from threading import Thread

from premium_emojis import get_emoji_tag
from i18n import get_string, PREMIUM_EMOJI_LINE

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
E_CROWN = get_emoji_tag('CROWN', '👑')
E_ROCKET = get_emoji_tag('ROCKET', '🚀')
E_DIAMOND = get_emoji_tag('DIAMOND', '💎')

TOKEN = "8721285488:AAH8XG2wT8Mi3JyUD6jzRWjVnyUWKi6Iysk"
PAYMENT_BOT_TOKEN = "8638636800:AAE8HebDVlk5N28kxiWIgKZdaWSWRdVQHqk"
DATABASE = 'payments.db'
PROVIDER_TOKEN = '187703658:TEST:5d5b04968f5d1a03e9fc853d6895cf8f8f5254fb'
ADMIN_IDS = [7972155518]
NOTIFY_IDS = [7972155518]

# نظام الدعوة المتطور - النجوم تبدأ من 100 فما فوق
REFERRAL_TIERS = [
    (1, 7, "Bronze", 0),        # دعوة واحدة = 7 فيديوهات
    (3, 15, "Silver", 100),     # 3 دعوات + 100 نجمة
    (5, 30, "Gold", 250),       # 5 دعوات + 250 نجمة
    (10, 60, "Platinum", 500),  # 10 دعوات + 500 نجمة
    (20, 120, "Diamond", 1000), # 20 دعوة + 1000 نجمة
    (35, 250, "Legend", 2000),  # 35 دعوة + 2000 نجمة
    (50, 500, "Ultimate", 5000), # 50 دعوة + 5000 نجمة
    (75, 1000, "Supreme", 10000), # 75 دعوة + 10000 نجمة
    (100, 2000, "Godly", 25000),  # 100 دعوة + 25000 نجمة
]

# 10 تصاميم مختلفة للرسائل الترحيبية مع عروض عشوائية
WELCOME_MESSAGES = [
    {
        "title": "🔥 WELCOME TO THE ELITE CLUB! 🔥",
        "emoji_line": "═" * 35,
        "body": (
            f"{E_CROWN} <b>You've entered the <u>Premium Video Paradise</u>!</b> {E_CROWN}\n\n"
            f"⭐ <b>Why settle for less when you can have the BEST?</b> ⭐\n\n"
            f"✨ <b>What makes us SPECIAL:</b>\n"
            f"  • {E_DIAMOND} <b>100,000+</b> Exclusive Premium Videos\n"
            f"  • {E_ROCKET} <b>Instant Delivery</b> to your chat\n"
            f"  • {E_GIFT} <b>FREE Videos</b> via referrals\n"
            f"  • {E_CROWN} <b>9 Reward Tiers</b> to unlock\n"
        ),
        "offer": {
            "name": "🔥 BLAZING DEAL 🔥",
            "videos": 499,
            "stars": 299,
            "emoji": "🔥"
        }
    },
    {
        "title": "💎 ROYAL WELCOME! 👑",
        "emoji_line": "─" * 35,
        "body": (
            f"{E_DIAMOND} <b>Welcome to the <u>KINGDOM of Premium Content</u>!</b> {E_DIAMOND}\n\n"
            f"👑 <b>Only the BEST for our members:</b> 👑\n\n"
            f"  • {E_STAR} <b>Ultra HD</b> Exclusive Videos\n"
            f"  • {E_FIRE} <b>Daily Updates</b> with fresh content\n"
            f"  • {E_HEART} <b>24/7 Support</b> and instant help\n"
            f"  • {E_GIFT} <b>Earn Videos</b> by inviting friends\n"
        ),
        "offer": {
            "name": "⚡ FLASH SALE ⚡",
            "videos": 750,
            "stars": 399,
            "emoji": "⚡"
        }
    },
    {
        "title": "🚀 BLAST OFF TO PREMIUM! 🚀",
        "emoji_line": "━" * 35,
        "body": (
            f"{E_ROCKET} <b>You've launched into <u>Premium Video Space</u>!</b> {E_ROCKET}\n\n"
            f"🌟 <b>Your journey to greatness starts NOW:</b> 🌟\n\n"
            f"  • {E_STAR} <b>Unlimited Access</b> to premium library\n"
            f"  • {E_FIRE} <b>No Ads, No Buffering</b> - Just Quality\n"
            f"  • {E_GIFT} <b>Invite System</b> - Get FREE Premium Videos\n"
            f"  • {E_CROWN} <b>Climb Ranks</b> - Unlock Exclusive Rewards\n"
        ),
        "offer": {
            "name": "🎁 NEW MEMBER BONUS 🎁",
            "videos": 999,
            "stars": 499,
            "emoji": "🎁"
        }
    },
    {
        "title": "✨ YOU'VE ARRIVED! ✨",
        "emoji_line": "⋆" * 35,
        "body": (
            f"{E_SPARKLES} <b>Welcome to the <u>Ultimate Video Hub</u>!</b> {E_SPARKLES}\n\n"
            f"💫 <b>What awaits you inside:</b> 💫\n\n"
            f"  • {E_DIAMOND} <b>Premium Quality</b> - Only the Best\n"
            f"  • {E_ROCKET} <b>Lightning Fast</b> Video Delivery\n"
            f"  • {E_HEART} <b>Community of</b> Thousands of Members\n"
            f"  • {E_GIFT} <b>FREE Videos</b> - Just Share & Earn\n"
        ),
        "offer": {
            "name": "🎉 WELCOME DISCOUNT 🎉",
            "videos": 1499,
            "stars": 699,
            "emoji": "🎉"
        }
    },
    {
        "title": "🏆 CHAMPION'S WELCOME! 🏆",
        "emoji_line": "═" * 35,
        "body": (
            f"{E_CROWN} <b>Only <u>CHAMPIONS</u> get access here!</b> {E_CROWN}\n\n"
            f"🏅 <b>Ready to become a legend?</b> 🏅\n\n"
            f"  • {E_STAR} <b>Exclusive Content</b> You Won't Find Elsewhere\n"
            f"  • {E_FIRE} <b>VIP Treatment</b> and Priority Support\n"
            f"  • {E_GIFT} <b>Referral Rewards</b> Up to 25,000 Stars\n"
            f"  • {E_DIAMOND} <b>Milestone Bonuses</b> - 100+ FREE Videos\n"
        ),
        "offer": {
            "name": "💎 DIAMOND DEAL 💎",
            "videos": 1999,
            "stars": 899,
            "emoji": "💎"
        }
    },
    {
        "title": "🌙 MIDNIGHT PREMIUM CLUB 🌙",
        "emoji_line": "•" * 35,
        "body": (
            f"🌙 <b>Welcome to the <u>Exclusive Night Club</u>!</b> 🌙\n\n"
            f"✨ <b>The best content awaits you in the dark:</b> ✨\n\n"
            f"  • {E_STAR} <b>Midnight Collection</b> of Premium Videos\n"
            f"  • {E_FIRE} <b>Hot Daily Updates</b> - Never Miss Out\n"
            f"  • {E_GIFT} <b>Secret Rewards</b> for Top Referrers\n"
            f"  • {E_CROWN} <b>Become a VIP</b> - Unlock Everything\n"
        ),
        "offer": {
            "name": "🌙 NIGHT OWL SPECIAL 🌙",
            "videos": 2499,
            "stars": 1099,
            "emoji": "🌙"
        }
    },
    {
        "title": "⚡ POWER UP YOUR VIDEO EXPERIENCE ⚡",
        "emoji_line": "▬" * 35,
        "body": (
            f"⚡ <b>You've just <u>POWERED UP</u>!</b> ⚡\n\n"
            f"💪 <b>Get ready for an INSANE experience:</b> 💪\n\n"
            f"  • {E_DIAMOND} <b>Unlimited Power</b> - Watch Any Video, Anytime\n"
            f"  • {E_ROCKET} <b>Lightning Speed</b> - Instant Delivery\n"
            f"  • {E_HEART} <b>Join the Elite</b> - Special Member Perks\n"
            f"  • {E_GIFT} <b>EARN STARS</b> - Invite Friends = Free Stars!\n"
        ),
        "offer": {
            "name": "💪 POWER PACK 💪",
            "videos": 3499,
            "stars": 1499,
            "emoji": "💪"
        }
    },
    {
        "title": "🎬 CINEMA PREMIUM EDITION 🎬",
        "emoji_line": "🎬" * 18,
        "body": (
            f"🎬 <b>Welcome to <u>PREMIUM CINEMA</u>!</b> 🎬\n\n"
            f"🍿 <b>Grab your popcorn and enjoy:</b> 🍿\n\n"
            f"  • {E_STAR} <b>Blockbuster Collection</b> - All Your Favorites\n"
            f"  • {E_FIRE} <b>Weekly Premieres</b> - Fresh Content Every Week\n"
            f"  • {E_GIFT} <b>Movie Night Bonus</b> - Get Extra Videos\n"
            f"  • {E_CROWN} <b>Director's Cut</b> - Exclusive Access\n"
        ),
        "offer": {
            "name": "🍿 CINEMA PASS 🍿",
            "videos": 5000,
            "stars": 1999,
            "emoji": "🎬"
        }
    },
    {
        "title": "💫 LEGENDARY WELCOME 💫",
        "emoji_line": "✧" * 35,
        "body": (
            f"💫 <b>You are now a <u>LEGEND</u>!</b> 💫\n\n"
            f"🏆 <b>Join the ranks of the greatest:</b> 🏆\n\n"
            f"  • {E_DIAMOND} <b>Legendary Content</b> - For True Connoisseurs\n"
            f"  • {E_ROCKET} <b>Priority Queue</b> - Your Videos Come First\n"
            f"  • {E_HEART} <b>Personal Assistant</b> - Dedicated Support\n"
            f"  • {E_GIFT} <b>Legend Rewards</b> - Up to 50,000 Stars!\n"
        ),
        "offer": {
            "name": "✨ LEGENDARY PACK ✨",
            "videos": 10000,
            "stars": 3999,
            "emoji": "✨"
        }
    },
    {
        "title": "🌈 PREMIUM RAINBOW CLUB 🌈",
        "emoji_line": "🌈" * 18,
        "body": (
            f"🌈 <b>Welcome to the <u>Colorful World</u> of Premium!</b> 🌈\n\n"
            f"🎨 <b>A masterpiece of entertainment awaits:</b> 🎨\n\n"
            f"  • {E_STAR} <b>Diverse Collection</b> - Something for Everyone\n"
            f"  • {E_FIRE} <b>Hottest Trends</b> - Stay Updated Always\n"
            f"  • {E_GIFT} <b>Rainbow Rewards</b> - Colorful Bonus Videos\n"
            f"  • {E_CROWN} <b>Royal Treatment</b> - You Deserve the Best\n"
        ),
        "offer": {
            "name": "🌈 RAINBOW DEAL 🌈",
            "videos": 15000,
            "stars": 5999,
            "emoji": "🌈"
        }
    }
]

def is_admin(user_id):
    return user_id in ADMIN_IDS

bot = telebot.TeleBot(TOKEN)
bot_payment = telebot.TeleBot(PAYMENT_BOT_TOKEN)
BOT_USERNAME = None
app = Flask(__name__)

def setup_bot_commands():
    commands = [
        types.BotCommand("start", "Start Bot"),
        types.BotCommand("offer", "Special Offers")
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
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, language TEXT DEFAULT 'en', last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS payments (user_id INTEGER, payment_id TEXT, amount INTEGER, currency TEXT, PRIMARY KEY (user_id, payment_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT NOT NULL, file_name TEXT, file_size INTEGER, duration INTEGER, added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sent_videos (user_id INTEGER, video_id INTEGER, PRIMARY KEY (user_id, video_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (referrer_id INTEGER, referred_id INTEGER, PRIMARY KEY (referred_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS share_rewards (user_id INTEGER PRIMARY KEY, rewarded BOOLEAN DEFAULT FALSE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS gift_claims (user_id INTEGER PRIMARY KEY, last_claim_time TIMESTAMP NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_subscriptions (user_id INTEGER PRIMARY KEY, days_remaining INTEGER, last_sent_date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS processed_deep_links (link_id TEXT PRIMARY KEY, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS milestones (user_id INTEGER PRIMARY KEY, total_spent INTEGER DEFAULT 0, rewarded BOOLEAN DEFAULT FALSE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT, target_id INTEGER, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS referral_rewards (user_id INTEGER, tier_invites INTEGER, stars_rewarded INTEGER DEFAULT 0, claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, tier_invites))''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_sent_videos_user ON sent_videos(user_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_videos_file_id ON videos(file_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)''')
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN language TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN stars_balance INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE referral_rewards ADD COLUMN stars_rewarded INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        conn.commit()

def is_banned(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

def ban_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
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
                cursor.execute('INSERT INTO users (user_id, username, last_seen, stars_balance) VALUES (?, ?, CURRENT_TIMESTAMP, 0)', (user_id, username))
            else:
                cursor.execute('UPDATE users SET username = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?', (username, user_id))
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
                    f"✨ <b>Welcome them to the club!</b>",
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
        
        # إضافة مكافأة النجوم للمدعو
        cursor.execute('UPDATE users SET stars_balance = stars_balance + 50 WHERE user_id = ?', (referred_id,))
        conn.commit()
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

def claim_tier(user_id, tier_invites, stars_reward):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO referral_rewards (user_id, tier_invites, stars_rewarded) VALUES (?, ?, ?)', (user_id, tier_invites, stars_reward))
            conn.commit()
            # إضافة النجوم للرصيد
            if stars_reward > 0:
                cursor.execute('UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?', (stars_reward, user_id))
                conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def get_next_tier(ref_count, claimed_tiers):
    for invites_needed, reward, name, stars_reward in REFERRAL_TIERS:
        if invites_needed not in claimed_tiers:
            return (invites_needed, reward, name, stars_reward)
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
            cursor.execute('INSERT INTO videos (file_id, file_name, file_size, duration) VALUES (?, ?, ?, ?)', (file_id, file_name, file_size, duration))
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
            conn.commit()
    except Exception as e:
        print(f"DB error save_sent_video: {e}")

def get_user_stars_balance(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT stars_balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

def update_user_stars(user_id, amount):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()

import queue
import threading
from concurrent.futures import ThreadPoolExecutor

delivery_queue = queue.Queue()
delivery_pool = ThreadPoolExecutor(max_workers=10)

def process_delivery(task):
    try:
        if len(task) == 5:
            user_id, video_list, success_callback, failure_callback, admin_msg_id = task
        else:
            user_id, video_list, success_callback, failure_callback = task
            admin_msg_id = None

        total_vids = len(video_list)
        CAPTION = ""
        success_count = 0

        for idx, (v_id, f_id) in enumerate(video_list):
            try:
                time.sleep(0.3)
                bot.send_video(user_id, f_id, caption=CAPTION)
                save_sent_video(user_id, v_id)
                success_count += 1

                if admin_msg_id and (success_count % 5 == 0 or success_count == total_vids):
                    for admin_id in NOTIFY_IDS:
                        try:
                            bot.edit_message_text(
                                f"🚀 <b>Delivery Progress</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"User ID: <code>{user_id}</code>\n"
                                f"Progress: <b>{success_count}/{total_vids}</b> videos\n"
                                f"Status: <b>Sending...</b>",
                                admin_id, admin_msg_id, parse_mode='HTML'
                            )
                        except: pass
            except Exception as e:
                print(f"Worker error: {e}")
                if "blocked" in str(e).lower(): break

        if admin_msg_id:
            for admin_id in NOTIFY_IDS:
                try:
                    bot.edit_message_text(
                        f"✅ <b>Delivery Complete</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"User ID: <code>{user_id}</code>\n"
                        f"Total: <b>{success_count}/{total_vids}</b> videos sent.",
                        admin_id, admin_msg_id, parse_mode='HTML'
                    )
                except: pass

        if success_count > 0:
            if success_callback: success_callback(user_id, success_count)
        else:
            if failure_callback: failure_callback(user_id)
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

        bot.send_message(user_id, get_string('delivery_success', lang, count=count), parse_mode='HTML', reply_markup=keyboard)
    except: pass

def notify_delivery_failure(user_id):
    lang = get_user_language(user_id)
    try: bot.send_message(user_id, get_string('delivery_failed', lang, user_id=user_id), parse_mode='HTML')
    except: pass

def get_total_users():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
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
    for invites_needed, reward, name, stars_reward in REFERRAL_TIERS:
        stars_text = f" + {stars_reward} ⭐" if stars_reward > 0 else ""
        if invites_needed in claimed_tiers:
            lines.append(f"✅ <b>{name}</b> ┊ {invites_needed} invites ┊ {reward} videos{stars_text} ┊ <b>CLAIMED</b>")
        elif ref_count >= invites_needed:
            lines.append(f"🎁 <b>{name}</b> ┊ {invites_needed} invites ┊ {reward} videos{stars_text} ┊ <b>READY!</b>")
        else:
            lines.append(f"🔒 <b>{name}</b> ┊ {invites_needed} invites ┊ {reward} videos{stars_text} ┊ {ref_count}/{invites_needed}")
    return "\n".join(lines)

def start_keyboard(user_id=None):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    lang = get_user_language(user_id) if user_id else 'en'
    from premium_emojis import PREMIUM_EMOJIS
    star_emoji_id = PREMIUM_EMOJIS.get('STAR_GOLD')
    fire_emoji_id = PREMIUM_EMOJIS.get('FIRE')
    gift_emoji_id = PREMIUM_EMOJIS.get('GIFT')
    wave_emoji_id = PREMINUM_EMOJIS.get('WAVE')
    heart_emoji_id = PREMIUM_EMOJIS.get('HEART_RED')
    crown_emoji_id = PREMIUM_EMOJIS.get('CROWN')

    # الصف الأول: Join Group
    keyboard.add(types.InlineKeyboardButton(text="🌟 Join Group 🚀", url="https://t.me/+ARG5VlNBj4NhYWE0"))

    # الصف الثاني: Mega Pack (5000 نجم - 175,000 فيديو)
    keyboard.add(styled_button(text="💎 MEGA PACK: 175,000 Videos + 5000 Stars 💎", callback_data="buy_175000", style="success", emoji_id=star_emoji_id))

    # الصف الثالث: VIP Packs
    keyboard.add(
        styled_button(text="👑 1000 Stars → 1600 Videos 👑", callback_data="buy_1600", style="primary", emoji_id=crown_emoji_id),
        styled_button(text="✨ 500 Stars → 750 Videos ✨", callback_data="buy_750", style="primary", emoji_id=star_emoji_id)
    )

    # الصف الرابع: Standard Packs
    keyboard.add(
        styled_button(text="⭐ 250 Stars → 350 Videos ⭐", callback_data="buy_350", style="primary", emoji_id=star_emoji_id),
        styled_button(text="🔥 100 Stars → 120 Videos 🔥", callback_data="buy_120", style="primary", emoji_id=star_emoji_id)
    )

    if user_id:
        ref_count = get_referral_count(user_id)
        claimed_tiers = get_claimed_tiers(user_id)
        stars_balance = get_user_stars_balance(user_id)
        next_tier = get_next_tier(ref_count, claimed_tiers)

        global BOT_USERNAME
        if not BOT_USERNAME:
            try:
                me = bot.get_me()
                BOT_USERNAME = me.username
            except:
                BOT_USERNAME = "bot"

        invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        share_text = f"🎬 EXCLUSIVE PREMIUM VIDEO BOT! 🎬\n\nGet 100,000+ premium videos instantly!\nInvite friends & earn FREE videos + STARS!\nContent delivered in seconds!\n\nJoin now: {invite_link}"
        import urllib.parse
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text={urllib.parse.quote(share_text)}"

        has_claimable = any(ref_count >= inv and inv not in claimed_tiers for inv, _, _, _ in REFERRAL_TIERS)

        # الصف الخامس: Claim Rewards
        if has_claimable:
            keyboard.add(styled_button(text=f"🎁 CLAIM REWARDS ({ref_count} invites) 🎁", callback_data="claim_rewards", style="danger", emoji_id=gift_emoji_id))

        # الصف السادس: Invite Friends
        if next_tier:
            invites_needed, reward, name, stars_reward = next_tier
            keyboard.add(styled_button(text=f"🤝 INVITE FRIENDS ({ref_count}/{invites_needed}) 🤝", url=share_url, style="success", emoji_id=wave_emoji_id))
        else:
            keyboard.add(styled_button(text=f"🏆 ALL TIERS COMPLETED! ({ref_count}) 🏆", url=share_url, style="success", emoji_id=crown_emoji_id))

        # الصف السابع: Referral Menu + Stars Balance
        keyboard.add(
            styled_button(text=f"📊 REFERRAL DASHBOARD ({ref_count}) 📊", callback_data="referral_menu", style="primary", emoji_id=heart_emoji_id),
            styled_button(text=f"⭐ STARS: {stars_balance} ⭐", callback_data="none", style="primary", emoji_id=star_emoji_id)
        )

    # الصف الثامن: Offers & Leaderboard
    keyboard.add(
        styled_button(text="🔥 SPECIAL OFFERS 🔥", callback_data="offer_menu", style="success", emoji_id=fire_emoji_id),
        styled_button(text=get_string('leaderboard', lang), callback_data="leaderboard", style="primary", emoji_id=star_emoji_id)
    )

    # الصف التاسع: Language & My Videos
    keyboard.add(
        types.InlineKeyboardButton("🌐 Language", callback_data="change_lang"),
        styled_button(text="🎬 MY VIDEOS 🎬", callback_data="my_videos", style="primary", emoji_id=star_emoji_id)
    )

    if user_id and is_admin(user_id):
        total_users = get_total_users()
        keyboard.add(styled_button(text=f"🔧 ADMIN PANEL ({total_users}) 🔧", callback_data="admin_panel", style="primary"))

    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def handle_back_to_start(call):
    lang = get_user_language(call.from_user.id)
    welcome_text = get_string('welcome', lang)
    try:
        bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=start_keyboard(call.from_user.id),
            parse_mode='HTML'
        )
    except:
        try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=start_keyboard(call.from_user.id))
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

@bot.callback_query_handler(func=lambda call: call.data == "offer_menu")
def handle_offer_menu(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)

    from premium_emojis import PREMIUM_EMOJIS
    star_id = PREMIUM_EMOJIS.get('STAR_GOLD')
    fire_id = PREMIUM_EMOJIS.get('FIRE')
    crown_id = PREMIUM_EMOJIS.get('CROWN')

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        styled_button("💎 5000 Stars → 175,000 Videos + 2000 Bonus 💎", callback_data="buy_175000", emoji_id=star_id),
        styled_button("👑 1000 Stars → 1600 Videos + 100 Bonus 👑", callback_data="buy_1600", emoji_id=crown_id),
        styled_button("⭐ 500 Stars → 750 Videos + 50 Bonus ⭐", callback_data="buy_750", emoji_id=star_id),
        styled_button("🔥 250 Stars → 350 Videos + 25 Bonus 🔥", callback_data="buy_350", emoji_id=fire_id),
        styled_button("✨ 100 Stars → 120 Videos + 10 Bonus ✨", callback_data="buy_120", emoji_id=star_id),
        styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary")
    )

    bot.edit_message_text(
        f"{PREMIUM_EMOJI_LINE}\n✨ <b>🔥 HOT OFFERS 🔥</b> ✨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>💎 Choose your package and get INSTANT delivery!</b>\n\n"
        f"<i>⭐ All packages include BONUS videos!</i>",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['offer'])
def handle_offer_command(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)

    from premium_emojis import PREMIUM_EMOJIS
    star_id = PREMIUM_EMOJIS.get('STAR_GOLD')
    fire_id = PREMIUM_EMOJIS.get('FIRE')
    crown_id = PREMIUM_EMOJIS.get('CROWN')

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        styled_button("💎 5000 Stars → 175,000 Videos + 2000 Bonus 💎", callback_data="buy_175000", emoji_id=star_id),
        styled_button("👑 1000 Stars → 1600 Videos + 100 Bonus 👑", callback_data="buy_1600", emoji_id=crown_id),
        styled_button("⭐ 500 Stars → 750 Videos + 50 Bonus ⭐", callback_data="buy_750", emoji_id=star_id),
        styled_button("🔥 250 Stars → 350 Videos + 25 Bonus 🔥", callback_data="buy_350", emoji_id=fire_id),
        styled_button("✨ 100 Stars → 120 Videos + 10 Bonus ✨", callback_data="buy_120", emoji_id=star_id),
        styled_button(get_string('back_to_start', lang), callback_data="back_to_start", style="primary")
    )

    bot.send_message(
        message.chat.id,
        f"{PREMIUM_EMOJI_LINE}\n✨ <b>🔥 HOT OFFERS 🔥</b> ✨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>💎 Choose your package and get INSTANT delivery!</b>\n\n"
        f"<i>⭐ All packages include BONUS videos!</i>",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data == "my_videos")
def handle_my_videos(call):
    user_id = call.from_user.id
    # إرسال فيديوهات عشوائية للمستخدم
    videos = get_unsent_videos(user_id, limit=5)
    if videos:
        bot.answer_callback_query(call.id, "🎬 Sending you 5 random videos!")
        delivery_queue.put((user_id, videos, notify_delivery_success, notify_delivery_failure, None))
    else:
        bot.answer_callback_query(call.id, "❌ No videos available right now!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def handle_admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Admin only!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        styled_button("📊 Stats", callback_data="admin_stats"),
        styled_button("🎬 Videos DB", callback_data="admin_videos"),
        styled_button("👥 Users", callback_data="admin_users"),
        styled_button("💰 Buyers", callback_data="admin_buyers"),
        styled_button("📜 Logs", callback_data="admin_logs"),
        styled_button("🏆 Top Referrers", callback_data="admin_top_ref"),
        styled_button("📢 Broadcast", callback_data="admin_broadcast"),
        styled_button("🚫 Ban/Unban", callback_data="admin_ban"),
        styled_button("📤 Send Videos", callback_data="admin_send_v"),
        styled_button("🎁 Welcome Msg", callback_data="admin_welcome"),
        styled_button("⬅️ Back", callback_data="back_to_start")
    )
    
    bot.edit_message_text(
        f"🔧 <b>ADMIN CONTROL PANEL</b> 🔧\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Welcome, Admin!</b>\n\nSelect an option below:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_welcome")
def handle_admin_welcome(call):
    if not is_admin(call.from_user.id):
        return
    
    bot.answer_callback_query(call.id, "📤 Send /welcome command to broadcast welcome message!")
    bot.send_message(call.message.chat.id, 
        "🎯 <b>Welcome Message Tool</b>\n\n"
        "Use: <code>/welcome</code>\n\n"
        "This will send a RANDOM beautifully designed welcome message\n"
        "with special offers to ALL users!\n\n"
        f"<i>There are {len(WELCOME_MESSAGES)} different designs!</i>",
        parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_payment_request(call):
    user_id = call.from_user.id
    try:
        count = int(call.data.replace("buy_", ""))
    except ValueError:
        return

    # باقات الأسعار بالنجوم (تبدأ من 100)
    stars_map = {
        120: 100,
        350: 250,
        750: 500,
        1600: 1000,
        175000: 5000
    }

    stars_price = stars_map.get(count, count)

    try:
        invoice_link = bot_payment.create_invoice_link(
            title=f"🔥 PREMIUM PACK: {count} Videos 🔥",
            description=f"⚡ INSTANT Delivery! Get {count} exclusive premium videos!\n⭐ BONUS videos included!",
            payload=f"deliver_{user_id}_{count}",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label=f"🎬 {count} Premium Videos", amount=stars_price)]
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text=f"⭐ PAY {stars_price} STARS", url=invoice_link))
        keyboard.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="offer_menu"))
        bot.send_message(
            call.message.chat.id,
            f"🎬 <b>PREMIUM PACK: {count} Videos</b>\n\n"
            f"⭐ <b>Price:</b> {stars_price} Stars\n"
            f"⚡ <b>Delivery:</b> Instant\n"
            f"🎁 <b>Bonus:</b> FREE extra videos included!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<i>Press the button below to complete your purchase:</i>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error creating invoice link: {e}")
        prices = [types.LabeledPrice(label=f"{count} Videos", amount=stars_price)]
        bot.send_invoice(
            call.message.chat.id,
            title=f"🔥 PREMIUM PACK: {count} Videos 🔥",
            description=f"⚡ INSTANT Delivery! Get {count} exclusive premium videos!",
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
    stars_balance = get_user_stars_balance(user_id)

    global BOT_USERNAME
    if not BOT_USERNAME: 
        try:
            BOT_USERNAME = bot.get_me().username
        except:
            BOT_USERNAME = "bot"
            
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    share_text = f"🎬 EXCLUSIVE PREMIUM VIDEO BOT! 🎬\n\nGet 100,000+ premium videos instantly!\nInvite friends & earn FREE videos + STARS!\nJoin now: {invite_link}"
    import urllib.parse
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text={urllib.parse.quote(share_text)}"

    total_videos_earned = sum(reward for inv, reward, _, _ in REFERRAL_TIERS if inv in claimed_tiers)
    total_stars_earned = sum(stars for inv, _, _, stars in REFERRAL_TIERS if inv in claimed_tiers)
    progress_text = build_referral_progress(ref_count, claimed_tiers)

    text = (
        f"{PREMIUM_EMOJI_LINE}\n"
        f"🏆 <b>REFERRAL DASHBOARD</b> 🏆\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Total Invites:</b> <code>{ref_count}</code>\n"
        f"🎬 <b>Videos Earned:</b> <code>{total_videos_earned}</code>\n"
        f"⭐ <b>Stars Earned:</b> <code>{total_stars_earned}</code>\n"
        f"💎 <b>Your Balance:</b> <code>{stars_balance}</code> Stars\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{progress_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>Your Invite Link:</b>\n<code>{invite_link}</code>\n\n"
        f"💡 <i>Share this link with friends to earn rewards!</i>"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(styled_button("📤 SHARE INVITE LINK", url=share_url, style="success"))

    has_claimable = any(
        ref_count >= inv and inv not in claimed_tiers
        for inv, _, _, _ in REFERRAL_TIERS
    )
    if has_claimable:
        keyboard.add(styled_button("🎁 CLAIM REWARDS", callback_data="claim_rewards", style="danger"))

    keyboard.add(styled_button("⬅️ BACK TO START", callback_data="back_to_start", style="primary"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
    except:
        try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "claim_rewards")
def handle_claim_rewards(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)

    total_videos_to_deliver = 0
    total_stars_to_add = 0
    tiers_to_claim = []

    for invites_needed, reward, name, stars_reward in REFERRAL_TIERS:
        if ref_count >= invites_needed and invites_needed not in claimed_tiers:
            total_videos_to_deliver += reward
            total_stars_to_add += stars_reward
            tiers_to_claim.append((invites_needed, reward, name, stars_reward))

    if total_videos_to_deliver == 0 and total_stars_to_add == 0:
        bot.answer_callback_query(call.id, get_string('no_rewards', lang), show_alert=True)
        return

    # إضافة النجوم أولاً
    if total_stars_to_add > 0:
        update_user_stars(user_id, total_stars_to_add)

    unsent = get_unsent_videos(user_id, limit=total_videos_to_deliver) if total_videos_to_deliver > 0 else []

    tiers_claimed_now = []
    for invites_needed, reward, name, stars_reward in tiers_to_claim:
        if claim_tier(user_id, invites_needed, stars_reward):
            tiers_claimed_now.append((name, reward, stars_reward))

    if not tiers_claimed_now:
        bot.answer_callback_query(call.id, "Rewards already claimed!", show_alert=True)
        return

    tier_text = "\n".join([f"✅ {name}: +{reward} videos + {stars_reward} ⭐" for name, reward, stars_reward in tiers_claimed_now])
    bot.answer_callback_query(call.id, f"✨ Claimed! Check your rewards!", show_alert=True)

    response_text = (
        f"🎁 <b>REWARDS CLAIMED SUCCESSFULLY!</b> 🎁\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{tier_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if total_videos_to_deliver > 0:
        response_text += f"🎬 <b>Total Videos:</b> {len(unsent)} videos will be delivered!\n"
    if total_stars_to_add > 0:
        response_text += f"⭐ <b>Stars Added:</b> +{total_stars_to_add} Stars to your balance!\n"
    
    bot.send_message(user_id, response_text, parse_mode='HTML')

    if unsent:
        delivery_queue.put((user_id, unsent, notify_delivery_success, notify_delivery_failure, None))

    for admin_id in NOTIFY_IDS:
        try:
            bot.send_message(admin_id,
                f"🎁 <b>Referral Reward Claimed!</b>\n\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"👥 Invites: {ref_count}\n"
                f"🎬 Videos: {len(unsent)}\n"
                f"⭐ Stars: +{total_stars_to_add}\n"
                f"🏆 Tiers: {', '.join([n for n, _, _ in tiers_claimed_now])}",
                parse_mode='HTML')
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard")
def handle_leaderboard(call):
    lang = get_user_language(call.from_user.id)
    leaders = get_referral_leaderboard(10)

    if not leaders:
        text = (
            f"🏆 <b>LEADERBOARD</b> 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 No leaders yet!\n\n"
            f"💡 <i>Be the first to invite friends!</i>"
        )
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []
        for i, (uid, uname, count) in enumerate(leaders):
            medal = medals[i] if i < len(medals) else f"#{i+1}"
            display = f"@{uname}" if uname else f"User {uid}"
            stars_balance = get_user_stars_balance(uid)
            lines.append(f"{medal} {display} — <b>{count}</b> invites | ⭐ {stars_balance}")

        text = (
            f"🏆 <b>TOP REFERRERS LEADERBOARD</b> 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            + "\n".join(lines) +
            f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Keep inviting to climb the ranks!</i>"
        )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(styled_button("⬅️ BACK TO START", callback_data="back_to_start", style="primary"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
    except:
        try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "none")
def handle_none(call):
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: is_banned(message.from_user.id))
def handle_banned(message):
    bot.send_message(message.chat.id, "🚫 You are banned from using this bot.")

# ======================== أمر /welcome للأدمن ========================
@bot.message_handler(commands=['welcome'])
def handle_welcome_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ This command is for admins only!")
        return
    
    # اختيار تصميم عشوائي من الـ 10 تصاميم
    selected = random.choice(WELCOME_MESSAGES)
    
    # بناء الرسالة
    welcome_text = (
        f"{selected['emoji_line']}\n"
        f"{selected['title']}\n"
        f"{selected['emoji_line']}\n\n"
        f"{selected['body']}\n\n"
        f"{selected['emoji_line']}\n\n"
        f"🎁 <b>SPECIAL WELCOME OFFER:</b> 🎁\n"
        f"{selected['offer']['emoji']} <b>{selected['offer']['name']}</b> {selected['offer']['emoji']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>{selected['offer']['videos']:,} Premium Videos</b>\n"
        f"⭐ <b>Only {selected['offer']['stars']:,} Stars!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ <b>LIMITED TIME OFFER!</b> ⚡\n"
        f"✨ <i>Click the button below to claim your welcome bonus!</i>"
    )
    
    # زر العرض
    offer_keyboard = types.InlineKeyboardMarkup()
    offer_keyboard.add(
        types.InlineKeyboardButton(
            text=f"{selected['offer']['emoji']} CLAIM NOW - {selected['offer']['stars']} ⭐ {selected['offer']['emoji']}",
            callback_data=f"buy_{selected['offer']['videos']}"
        )
    )
    
    # إرسال لكل المستخدمين
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
    
    success_count = 0
    fail_count = 0
    
    bot.send_message(message.chat.id, f"📢 <b>Sending welcome message to all users...</b>\n\nSelected design: {selected['title']}\nTotal users: {len(users)}", parse_mode='HTML')
    
    for (user_id,) in users:
        try:
            bot.send_message(user_id, welcome_text, parse_mode='HTML', reply_markup=offer_keyboard)
            success_count += 1
            time.sleep(0.05)
        except Exception as e:
            fail_count += 1
    
    bot.send_message(message.chat.id, 
        f"✅ <b>Welcome Broadcast Complete!</b>\n\n"
        f"📤 Success: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"🎨 Design: {selected['title']}",
        parse_mode='HTML'
    )
    
    log_admin_action(message.from_user.id, "WELCOME_BROADCAST", details=f"Design: {selected['title']}, Success: {success_count}, Failed: {fail_count}")

# باقي الكود الأصلي كما هو (الأوامر الأخرى)

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
            bot.send_message(message.chat.id, "🌐 Please select your language:", reply_markup=language_keyboard())
            args = message.text.split()
            if len(args) > 1 and args[1].isdigit():
                referrer_id = int(args[1])
                if referrer_id != user_id:
                    add_referral(referrer_id, user_id)
            return

    save_user(user_id, username)
    lang = get_user_language(user_id)
    welcome_text = get_string('welcome', lang)
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML', reply_markup=start_keyboard(user_id))

@bot.message_handler(commands=['check'])
def handle_check_referral(message):
    user_id = message.from_user.id
    ref_count = get_referral_count(user_id)
    claimed_tiers = get_claimed_tiers(user_id)
    stars_balance = get_user_stars_balance(user_id)

    global BOT_USERNAME
    if not BOT_USERNAME: 
        try:
            BOT_USERNAME = bot.get_me().username
        except:
            BOT_USERNAME = "bot"
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    progress_text = build_referral_progress(ref_count, claimed_tiers)
    total_videos_earned = sum(reward for inv, reward, _, _ in REFERRAL_TIERS if inv in claimed_tiers)
    total_stars_earned = sum(stars for inv, _, _, stars in REFERRAL_TIERS if inv in claimed_tiers)

    text = (
        f"🏆 <b>YOUR REFERRAL PROGRESS</b> 🏆\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Total Invites:</b> <code>{ref_count}</code>\n"
        f"🎬 <b>Videos Earned:</b> <code>{total_videos_earned}</code>\n"
        f"⭐ <b>Stars Earned:</b> <code>{total_stars_earned}</code>\n"
        f"💎 <b>Your Balance:</b> <code>{stars_balance}</code> Stars\n\n"
        f"{progress_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Invite Link:</b>\n<code>{invite_link}</code>"
    )
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

        text = "📜 <b>Recent Admin Activity</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
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

    text = "💰 <b>Top Buyers</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for uid, uname, spent in buyers:
        user_display = f"@{uname}" if uname else f"ID:{uid}"
        text += f"👤 {user_display}\n└ ⭐ <code>{spent}</code> Stars\n\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')

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
        
        # إضافة مكافأة إضافية حسب حجم الباقة
        bonus = 0
        if count >= 175000:
            bonus = 2000
        elif count >= 1600:
            bonus = 100
        elif count >= 750:
            bonus = 50
        elif count >= 350:
            bonus = 25
        elif count >= 120:
            bonus = 10
            
        total_count = count + bonus
        
        unsent = get_unsent_videos(user_id, limit=total_count)
        if unsent:
            bonus_text = f"\n🎁 <b>BONUS:</b> +{bonus} FREE videos!" if bonus > 0 else ""
            bot.send_message(user_id, 
                f"✅ <b>PAYMENT SUCCESSFUL!</b> ✅\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎬 <b>Package:</b> {count} Videos\n"
                f"{bonus_text}\n"
                f"📦 <b>Total:</b> {len(unsent)} videos\n"
                f"⚡ <b>Status:</b> Delivering now...\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", 
                parse_mode='HTML')

            admin_msg_id = None
            for admin_id in NOTIFY_IDS:
                try:
                    alert = (f"⭐ <b>NEW PURCHASE!</b> ⭐\n\n"
                            f"👤 User: @{username if username else 'N/A'}\n"
                            f"🆔 ID: <code>{user_id}</code>\n"
                            f"💰 Amount: {message.successful_payment.total_amount} ⭐\n"
                            f"🎬 Package: {count} Videos (+{bonus} bonus)\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"⏳ Status: <b>Delivering...</b>")
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
                        f"🎉 <b>MILESTONE UNLOCKED!</b> 🎉\n\n"
                        f"✨ You've reached <b>750 Stars</b> spent! ✨\n"
                        f"🎁 Here are <b>100 BONUS Premium Videos</b> just for you!\n"
                        f"❤️ Thank you for being a loyal member!",
                        parse_mode='HTML')
                    delivery_queue.put((user_id, bonus_vids, notify_delivery_success, notify_delivery_failure, None))

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

        text = "🔍 <b>Live DB Debug</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📊 Total Referrals: {total_refs}\n\n"
        for rid, count in top_5:
            text += f"🆔 ID: <code>{rid}</code> - <b>{count}</b> invites\n"

        bot.reply_to(message, text, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['users_count'])
def handle_users_count(message):
    if not is_admin(message.from_user.id): return
    count = get_total_users()
    bot.reply_to(message, f"👥 <b>User Count</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👤 Total registered users: <code>{count}</code>", parse_mode='HTML')

@bot.message_handler(commands=['add'])
def handle_add_video(message):
    if not is_admin(message.from_user.id): return
    ADMIN_STATES[message.from_user.id] = 'WAITING_VIDEO'
    bot.send_message(message.chat.id, "📤 Send the videos you want to add to the library.\nType /done when finished.")

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

    bot.reply_to(message, f"✅ Video added! (Total: {total_vids})")

@bot.message_handler(commands=['done'])
def handle_done(message):
    if not is_admin(message.from_user.id): return
    ADMIN_STATES[message.from_user.id] = None
    bot.send_message(message.chat.id, "✅ Upload session finished.")

@bot.message_handler(commands=['videos'])
def handle_videos_list(message):
    if not is_admin(message.from_user.id): return
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        total_vids = cursor.execute('SELECT COUNT(*) FROM videos').fetchone()[0]
        today_vids = cursor.execute("SELECT COUNT(*) FROM videos WHERE date(added_date) = date('now')").fetchone()[0]
        week_vids = cursor.execute("SELECT COUNT(*) FROM videos WHERE added_date >= datetime('now', '-7 days')").fetchone()[0]

    text = (
        f"🎬 <b>Video Library Stats</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Total Videos:</b> <code>{total_vids}</code>\n"
        f"📅 <b>Added Today:</b> <code>{today_vids}</code>\n"
        f"🗓️ <b>Added This Week:</b> <code>{week_vids}</code>\n\n"
        f"✨ Your library is growing!"
    )
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
    bot.send_message(message.chat.id,
        f"📊 <b>Bot Stats</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Users: {total_users}\n"
        f"🎬 Videos: {total_vids}\n"
        f"💰 Purchases: {purchases}\n"
        f"👥 Total Referrals: {total_referrals}\n"
        f"🎁 Rewards Claimed: {total_rewards_claimed}",
        parse_mode='HTML')

@bot.message_handler(commands=['ban'])
def handle_ban_command(message):
    if not is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Usage: /ban <user_id>")
            return
        target_id = int(args[1])
        ban_user(target_id)
        bot.reply_to(message, f"✅ User {target_id} has been banned.")
        log_admin_action(message.from_user.id, "BAN", target_id=target_id)
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

    text = "🏆 <b>Top Referrers (Admin View)</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (uid, uname, count) in enumerate(leaders):
        display = f"@{uname}" if uname else f"ID:{uid}"
        stars = get_user_stars_balance(uid)
        text += f"#{i+1} {display} — <b>{count}</b> invites | ⭐ {stars} (ID: <code>{uid}</code>)\n"

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

    promo_text = (
        f"🔥" * 10 + "\n\n"
        f"🎬 <b>PREMIUM EXCLUSIVE VIDEOS</b> 🎬\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 <b>The #1 Premium Video Bot on Telegram!</b>\n\n"
        f"💎 <b>What You Get:</b>\n"
        f"├ 🎥 High-quality exclusive content\n"
        f"├ ⚡ Instant delivery to your chat\n"
        f"├ 🎁 FREE videos through referrals\n"
        f"└ 🏆 9 reward tiers to unlock\n\n"
        f"⭐" * 10 + "\n\n"
        f"👥 <b>INVITE & EARN:</b>\n\n"
        f"🥉 1 invite = 7 videos\n"
        f"🥈 3 invites = 15 videos + 100⭐\n"
        f"🥇 5 invites = 30 videos + 250⭐\n"
        f"💎 10 invites = 60 videos + 500⭐\n"
        f"👑 20 invites = 120 videos + 1000⭐\n"
        f"🏆 35 invites = 250 videos + 2000⭐\n"
        f"🌟 50 invites = 500 videos + 5000⭐\n"
        f"⚡ 75 invites = 1000 videos + 10000⭐\n"
        f"🔥 100 invites = 2000 videos + 25000⭐\n\n"
        f"💎" * 10 + "\n\n"
        f"🔥 <b>TOTAL: Up to 2,000 FREE VIDEOS + 43,850 STARS!</b> 🔥\n\n"
        f"👇 <b>TAP BELOW TO START NOW!</b> 👇"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 START THE BOT NOW 🚀", url="https://t.me/Llllppppooottt_bot?start=promo"))

    bot.send_message(message.chat.id, promo_text, parse_mode='HTML', reply_markup=keyboard)
    log_admin_action(message.from_user.id, "PROMO_GENERATED")

@bot.message_handler(commands=['share'])
def handle_share_broadcast(message):
    if not is_admin(message.from_user.id):
        return

    lang = 'en'
    global BOT_USERNAME
    if not BOT_USERNAME: 
        try:
            BOT_USERNAME = bot.get_me().username
        except:
            BOT_USERNAME = "bot"
    
    invite_link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"
    
    share_text = f"🔥 <b>STAY MOTIVATED!</b> 🔥\n\n" \
                 f"✨ <b>Success is a journey, not a destination!</b>\n" \
                 f"🚀 <b>Push yourself because no one else is going to do it for you!</b>\n\n" \
                 f"🎁 <b>Share this bot with your friends and earn FREE premium videos + STARS!</b>\n\n" \
                 f"👇 <b>Invite & Earn Now</b> 👇"
                 
    import urllib.parse
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_link)}&text={urllib.parse.quote('Check out this amazing bot! 🎬 Get FREE videos and STARS!')}"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📤 SHARE & EARN VIDEOS", url=share_url))
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        
    count = 0
    for (u_id,) in users:
        try:
            bot.send_message(u_id, share_text, parse_mode='HTML', reply_markup=keyboard)
            count += 1
            time.sleep(0.05)
        except:
            continue
            
    bot.reply_to(message, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(commands=['dee'])
def handle_dee_command(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text=f"⭐ BUY NOW ⭐",
        callback_data="buy_499_special"
    ))

    offer_text = (
        f"🔥 <b>EXCLUSIVE LIMITED OFFER!</b> 🔥\n\n"
        f"🎁 Unlock <b>499 Premium Videos</b>\n"
        f"⭐ For only <b>299 Stars</b>\n\n"
        f"⚡ <i>Instant Delivery guaranteed!</i>"
    )
    bot.send_message(message.chat.id, offer_text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_499_special")
def handle_buy_499(call):
    user_id = call.from_user.id
    try:
        invoice_link = bot_payment.create_invoice_link(
            title="🎁 SPECIAL OFFER: 499 Videos",
            description="Get 499 high-quality premium videos instantly! ⚡",
            payload=f"deliver_{user_id}_499",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label="🎬 499 Premium Videos", amount=299)]
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="⭐ PAY 299 STARS", url=invoice_link))
        keyboard.add(types.InlineKeyboardButton(text="⬅️ Back", callback_data="offer_menu"))
        bot.send_message(
            call.message.chat.id,
            "🎬 <b>SPECIAL OFFER: 499 Videos</b>\n\n"
            f"⭐ Price: <b>299 Stars</b>\n"
            f"⚡ Delivery: Instant\n\n"
            f"Press the button below to complete your purchase:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error creating invoice link: {e}")
        bot.send_invoice(
            call.message.chat.id,
            title="🎁 SPECIAL OFFER: 499 Videos",
            description="Get 499 high-quality premium videos instantly!",
            invoice_payload=f"deliver_{user_id}_499",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label="499 Videos", amount=299)],
            start_parameter="special_offer_499"
        )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    save_user(message.from_user.id, message.from_user.username)

# ── Payment bot handlers ──────────────────────────────────────────────────────

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

init_db()
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

payment_thread = Thread(target=run_payment_bot)
payment_thread.daemon = True
payment_thread.start()

print("Bot is starting...")
while True:
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
        bot.polling(non_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(5)
