import requests
import random
import time
import os
import json
from datetime import datetime, timedelta
from telebot import types
import logging
from supabase import create_client, Client

# ==================== تنظیمات لاگینگ ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("🤖 ربات دانلودر اینستاگرام - نسخه VIP v4.0 (رفع مشکل آمار)")
print("=" * 60)

# 🔐 اطلاعات ربات
BOT_TOKEN = "8364910763:AAGtyQFzRWmoXCSHp_XuVem91n2WeZeSPCc"
ADMIN_ID = 6906387548
FAST_CREAT_TOKEN = "6906387548:uTVkrzLDpGglShe@Api_ManagerRoBot"
SUPPORT_USERNAME = "@meAhmad_1386"
CHANNEL_USERNAME = "@ARIANA_MOOD"
CHANNEL_LINK = "https://t.me/ARIANA_MOOD"

# 📊 اطلاعات Supabase
SUPABASE_URL = "https://cykfcctuewglsgwarlds.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5a2ZjY3R1ZXdnbHNnd2FybGRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NDQ1OTIsImV4cCI6MjA4NzUyMDU5Mn0.UPuRUmBIqBSU55ctNrOQQC1DabYNcqGWTvfx1fJijDg"

# ==================== سیستم دیتابیس Supabase ====================
class Database:
    def __init__(self):
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ اتصال به Supabase با موفقیت برقرار شد")
            # بررسی اولیه دیتابیس
            self.check_database()
        except Exception as e:
            logger.error(f"❌ خطا در اتصال به Supabase: {e}")
            raise

    def check_database(self):
        """بررسی وجود کاربران در دیتابیس و لاگ تعداد"""
        try:
            users_resp = self.supabase.table('users').select('*').execute()
            logger.info(f"📊 تعداد کاربران موجود در دیتابیس: {len(users_resp.data)}")
        except Exception as e:
            logger.error(f"❌ خطا در بررسی دیتابیس: {e}")

    # -------------------- کاربران --------------------
    def add_or_update_user(self, user_id, username, first_name, last_name):
        """اضافه کردن کاربر جدید یا به‌روزرسانی کاربر موجود"""
        try:
            response = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            existing = response.data

            if not existing:
                # کاربر جدید
                invite_code = f"INV{user_id}{random.randint(1000, 9999)}"
                is_vip = 1 if user_id == ADMIN_ID else 0

                data = {
                    'user_id': user_id,
                    'username': username or "",
                    'first_name': first_name or "",
                    'last_name': last_name or "",
                    'invite_code': invite_code,
                    'is_vip': is_vip,
                    'join_date': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self.supabase.table('users').insert(data).execute()
                logger.info(f"✅ کاربر جدید اضافه شد: {user_id}")
                return True, "new"
            else:
                # کاربر موجود - به‌روزرسانی اطلاعات
                update_data = {
                    'username': username or "",
                    'first_name': first_name or "",
                    'last_name': last_name or "",
                    'updated_at': datetime.now().isoformat()
                }
                self.supabase.table('users').update(update_data).eq('user_id', user_id).execute()

                user = existing[0]
                if not user.get('invite_code'):
                    invite_code = f"INV{user_id}{random.randint(1000, 9999)}"
                    self.supabase.table('users').update({'invite_code': invite_code}).eq('user_id', user_id).execute()

                logger.info(f"✅ کاربر به‌روز شد: {user_id}")
                return False, "updated"
        except Exception as e:
            logger.error(f"❌ خطا در افزودن/به‌روزرسانی کاربر {user_id}: {e}")
            return False, "error"

    def is_vip(self, user_id):
        """بررسی VIP بودن کاربر"""
        try:
            if user_id == ADMIN_ID:
                return True

            response = self.supabase.table('users').select('is_vip, vip_until').eq('user_id', user_id).execute()
            if response.data:
                user = response.data[0]
                is_vip = user.get('is_vip', 0)
                vip_until = user.get('vip_until')

                if is_vip == 1:
                    if vip_until:
                        try:
                            vip_date = datetime.strptime(vip_until, '%Y-%m-%d').date()
                            today = datetime.now().date()
                            if vip_date < today:
                                self.supabase.table('users').update({'is_vip': 0, 'vip_until': None}).eq('user_id', user_id).execute()
                                return False
                        except:
                            pass
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ خطا در بررسی VIP: {e}")
            return False

    def set_vip(self, user_id, is_vip=True, days=None):
        """تنظیم وضعیت VIP کاربر"""
        try:
            update_data = {}
            if is_vip:
                update_data['is_vip'] = 1
                if days:
                    vip_until = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                    update_data['vip_until'] = vip_until
                else:
                    update_data['vip_until'] = None
            else:
                update_data['is_vip'] = 0
                update_data['vip_until'] = None

            self.supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"❌ خطا در تنظیم VIP: {e}")
            return False

    def get_vip_users(self):
        """دریافت لیست کاربران VIP"""
        try:
            response = self.supabase.table('users').select('user_id, username, first_name, vip_until').eq('is_vip', 1).order('vip_until', desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست VIP: {e}")
            return []

    def get_user_stats(self, user_id):
        """دریافت آمار کاربر"""
        try:
            response = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            if not response.data:
                return None

            user = response.data[0]

            return (
                user.get('user_id'),
                user.get('username'),
                user.get('first_name'),
                user.get('last_name'),
                user.get('join_date'),
                user.get('daily_downloads', 0),
                user.get('last_download_date'),
                user.get('total_downloads', 0),
                user.get('invite_code'),
                user.get('invited_by', 0),
                user.get('invite_count', 0),
                user.get('extra_downloads', 0),
                user.get('is_banned', 0),
                user.get('is_vip', 0),
                user.get('vip_until'),
                user.get('updated_at')
            )
        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار کاربر {user_id}: {e}")
            return None

    def get_today_downloads(self, user_id):
        """تعداد دانلودهای امروز (بدون محدودیت)"""
        return 0

    def can_download(self, user_id):
        """همیشه اجازه دانلود بده"""
        return True

    def increment_download(self, user_id):
        """افزایش آمار کل دانلودها"""
        try:
            current_total = self.supabase.table('users').select('total_downloads').eq('user_id', user_id).execute()
            if current_total.data:
                new_total = current_total.data[0].get('total_downloads', 0) + 1
                self.supabase.table('users').update({'total_downloads': new_total}).eq('user_id', user_id).execute()
                logger.info(f"📈 افزایش دانلود برای کاربر {user_id} به {new_total}")
            return True
        except Exception as e:
            logger.error(f"❌ خطا در افزایش دانلود: {e}")
            return False

    def get_remaining_downloads(self, user_id):
        """همیشه تعداد زیادی باقی‌مانده نشان بده"""
        return 999, 0, 999

    def get_invite_link(self, user_id, bot_username):
        """دریافت لینک دعوت"""
        try:
            response = self.supabase.table('users').select('invite_code').eq('user_id', user_id).execute()
            if response.data and response.data[0].get('invite_code'):
                invite_code = response.data[0]['invite_code']
            else:
                invite_code = f"INV{user_id}{random.randint(1000, 9999)}"
                self.supabase.table('users').update({'invite_code': invite_code}).eq('user_id', user_id).execute()
            return f"https://t.me/{bot_username}?start={invite_code}"
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لینک دعوت: {e}")
            return f"https://t.me/{bot_username}?start=INV{user_id}{random.randint(1000, 9999)}"

    def add_invite_reward(self, inviter_id):
        """افزایش آمار دعوت"""
        try:
            response = self.supabase.table('users').select('invite_count').eq('user_id', inviter_id).execute()
            if response.data:
                current = response.data[0]
                new_count = current.get('invite_count', 0) + 1
                self.supabase.table('users').update({'invite_count': new_count}).eq('user_id', inviter_id).execute()
                logger.info(f"🎁 دعوت جدید برای {inviter_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطا در افزودن پاداش دعوت: {e}")
            return False

    # -------------------- کانال‌های اجباری --------------------
    def add_required_channel(self, channel_username):
        """افزودن کانال اجباری"""
        try:
            clean_username = channel_username.replace('@', '')
            channel_link = f"https://t.me/{clean_username}"
            data = {
                'channel_username': channel_username,
                'channel_link': channel_link,
                'is_active': 1
            }
            self.supabase.table('required_channels').upsert(data, on_conflict='channel_username').execute()
            return True
        except Exception as e:
            logger.error(f"❌ خطا در افزودن کانال: {e}")
            return False

    def remove_required_channel(self, channel_username):
        """حذف کانال اجباری"""
        try:
            self.supabase.table('required_channels').delete().eq('channel_username', channel_username).execute()
            return True
        except Exception as e:
            logger.error(f"❌ خطا در حذف کانال: {e}")
            return False

    def get_required_channels(self):
        """دریافت کانال‌های اجباری"""
        try:
            response = self.supabase.table('required_channels').select('*').eq('is_active', 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کانال‌ها: {e}")
            return []

    # -------------------- ثبت درخواست‌ها --------------------
    def log_request(self, user_id, url, request_type, success=True, response_time=0):
        """ثبت درخواست"""
        try:
            data = {
                'user_id': user_id,
                'url': url,
                'type': request_type,
                'success': 1 if success else 0,
                'response_time': response_time,
                'date': datetime.now().isoformat()
            }
            self.supabase.table('requests').insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"❌ خطا در ثبت درخواست: {e}")
            return False

    # -------------------- آمار و کاربران --------------------
    def get_all_users(self):
        """دریافت تمام کاربران"""
        try:
            response = self.supabase.table('users').select('*').order('join_date', desc=True).execute()
            users = []
            for u in response.data:
                users.append((
                    u.get('user_id'),
                    u.get('username'),
                    u.get('first_name'),
                    u.get('last_name'),
                    u.get('join_date'),
                    u.get('daily_downloads', 0),
                    u.get('last_download_date'),
                    u.get('total_downloads', 0),
                    u.get('invite_code'),
                    u.get('invited_by', 0),
                    u.get('invite_count', 0),
                    u.get('extra_downloads', 0),
                    u.get('is_banned', 0),
                    u.get('is_vip', 0),
                    u.get('vip_until'),
                    u.get('updated_at')
                ))
            return users
        except Exception as e:
            logger.error(f"❌ خطا در دریافت همه کاربران: {e}")
            return []

    def get_total_stats(self):
        """دریافت آمار کلی (رفع مشکل count)"""
        try:
            users_resp = self.supabase.table('users').select('*').execute()
            total_users = len(users_resp.data)
            logger.info(f"📊 آمار - تعداد کاربران: {total_users}")

            requests_resp = self.supabase.table('requests').select('*').execute()
            total_requests = len(requests_resp.data)

            downloads_resp = self.supabase.table('users').select('total_downloads').execute()
            total_downloads = sum(u.get('total_downloads', 0) for u in downloads_resp.data)

            vip_resp = self.supabase.table('users').select('*').eq('is_vip', 1).execute()
            total_vip = len(vip_resp.data)

            logger.info(f"📊 آمار نهایی: {total_users} کاربر, {total_requests} درخواست, {total_downloads} دانلود")
            return total_users, total_requests, total_downloads, total_vip
        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار کلی: {e}")
            return 0, 0, 0, 0

    def reset_user_downloads(self, user_id):
        """ریست دانلودهای کاربر (دیگر کاربردی ندارد)"""
        return True

    def backup_database(self):
        """پشتیبان‌گیری (در Supabase معنی ندارد)"""
        logger.warning("⚠️ پشتیبان‌گیری در Supabase از طریق کد ممکن نیست. لطفاً از داشبورد Supabase استفاده کنید.")
        return None

# ==================== بقیه کد ====================
db = Database()
import telebot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== سیستم عضویت اجباری ====================
def check_subscription(user_id):
    try:
        required_channels = db.get_required_channels()
        if not required_channels:
            return True, []
        not_joined = []
        for channel in required_channels:
            channel_username = channel.get('channel_username')
            channel_link = channel.get('channel_link')
            try:
                clean_username = channel_username.replace('@', '')
                try:
                    chat_member = bot.get_chat_member(f"@{clean_username}", user_id)
                    if chat_member.status in ['member', 'administrator', 'creator']:
                        continue
                    else:
                        not_joined.append({'username': channel_username, 'link': channel_link})
                except Exception as e:
                    if "Chat not found" in str(e) or "bot is not a member" in str(e):
                        logger.warning(f"⚠️ ربات در کانال {channel_username} نیست یا ادمین نیست")
                        not_joined.append({'username': channel_username, 'link': channel_link})
                    else:
                        not_joined.append({'username': channel_username, 'link': channel_link})
            except Exception as e:
                logger.error(f"❌ خطا در بررسی عضویت: {e}")
                not_joined.append({'username': channel_username, 'link': channel_link})
        return len(not_joined) == 0, not_joined
    except Exception as e:
        logger.error(f"❌ خطا در check_subscription: {e}")
        return True, []

# ==================== طراحی منوها ====================
def glass_effect_menu(user_id=None):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["🌐 دانلود از اینستاگرام", "📊 آمار کاربری من", "ℹ️ راهنمای استفاده", "🆘 پشتیبانی", "👥 دعوت دوستان"]
    if user_id == ADMIN_ID:
        buttons.append("👑 پنل مدیریت")
    keyboard.add(buttons[0])
    keyboard.add(buttons[1], buttons[2])
    keyboard.add(buttons[3], buttons[4])
    if user_id == ADMIN_ID:
        keyboard.add(buttons[5])
    return keyboard

def glass_effect_admin_panel():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("📊 آمار کلی", "admin_stats"),
        ("👥 کاربران امروز", "admin_today"),
        ("⭐ مدیریت VIP", "admin_manage_vip"),
        ("📢 ارسال همگانی", "admin_broadcast"),
        ("➕ افزودن کانال", "admin_add_channel"),
        ("➖ حذف کانال", "admin_remove_channel"),
        ("📋 لیست کانال‌ها", "admin_list_channels"),
        ("🔄 ریست کاربر", "admin_reset_user"),
        ("📨 پیام به کاربر", "admin_message_user")
    ]
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.add(
            types.InlineKeyboardButton(row[0][0], callback_data=row[0][1]),
            types.InlineKeyboardButton(row[1][0], callback_data=row[1][1]) if len(row) > 1 else types.InlineKeyboardButton(" ", callback_data="none")
        )
    keyboard.add(types.InlineKeyboardButton("💾 پشتیبان دیتابیس", callback_data="admin_backup"))
    keyboard.add(types.InlineKeyboardButton("🔄 بازخوانی ربات", callback_data="admin_restart"))
    return keyboard

def vip_management_panel():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("➕ افزودن VIP", "admin_add_vip"),
        ("➖ حذف VIP", "admin_remove_vip"),
        ("📋 لیست VIP‌ها", "admin_list_vip"),
        ("⏰ تنظیم مدت VIP", "admin_set_vip_time"),
        ("🔙 بازگشت", "admin_back")
    ]
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.add(
            types.InlineKeyboardButton(row[0][0], callback_data=row[0][1]),
            types.InlineKeyboardButton(row[1][0], callback_data=row[1][1]) if len(row) > 1 else types.InlineKeyboardButton(" ", callback_data="none")
        )
    return keyboard

# ==================== سیستم API دانلود ====================
def download_instagram_content(url):
    start_time = time.time()
    if 'stories' in url or '/story/' in url:
        content_type = 'story'
    elif 'reel' in url or 'reels' in url:
        content_type = 'post2'
    elif '/p/' in url or '/tv/' in url:
        content_type = 'post2'
    else:
        content_type = 'post2'
    api_url = "https://api.fast-creat.ir/instagram"
    params = {'apikey': FAST_CREAT_TOKEN, 'type': content_type, 'url': url}
    try:
        logger.info(f"📡 ارسال درخواست به API برای URL: {url}")
        response = requests.get(api_url, params=params, timeout=45)
        response_time = time.time() - start_time
        logger.info(f"✅ پاسخ API دریافت شد. زمان: {response_time:.2f} ثانیه")
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return {'success': True, 'data': result.get('result', {}), 'response_time': response_time}
            else:
                return {'success': False, 'error': result.get('message', 'خطای ناشناخته'), 'response_time': response_time}
        else:
            return {'success': False, 'error': f"خطای HTTP: {response.status_code}", 'response_time': response_time}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': "زمان اتصال به سرور به پایان رسید", 'response_time': time.time() - start_time}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': "خطا در اتصال به سرور", 'response_time': time.time() - start_time}
    except Exception as e:
        return {'success': False, 'error': f"خطای سیستم: {str(e)}", 'response_time': time.time() - start_time}

# ==================== دستورات اصلی ====================
@bot.message_handler(commands=['start', 'restart'])
def start_command(message):
    try:
        user = message.from_user
        logger.info(f"👤 کاربر: {user.id} - {user.first_name}")
        
        db.add_or_update_user(user.id, user.username, user.first_name, user.last_name)
        
        if len(message.text.split()) > 1:
            invite_code = message.text.split()[1]
            if invite_code.startswith("INV"):
                response = db.supabase.table('users').select('user_id').eq('invite_code', invite_code).execute()
                if response.data:
                    inviter_id = response.data[0]['user_id']
                    if inviter_id != user.id:
                        if db.add_invite_reward(inviter_id):
                            try:
                                bot.send_message(inviter_id, 
                                    f"🎉 <b>دوست شما با لینک دعوت شما وارد شد!</b>\n\n"
                                    f"👤 کاربر: {user.first_name}\n"
                                    f"🆔 آیدی: {user.id}\n"
                                    f"🎁 <b>یک دعوت به آمار شما اضافه شد!</b>")
                            except:
                                pass
        
        is_subscribed, not_joined = check_subscription(user.id)
        
        if not is_subscribed:
            keyboard = types.InlineKeyboardMarkup()
            for channel_info in not_joined:
                keyboard.add(types.InlineKeyboardButton(
                    f"👉 عضویت در {channel_info['username']}", 
                    url=channel_info['link']
                ))
            keyboard.add(types.InlineKeyboardButton(
                "✅ بررسی مجدد عضویت", 
                callback_data=f"check_sub_{user.id}"
            ))
            
            channels_list = "\n".join([f"• {chan['username']}" for chan in not_joined])
            welcome_text = f"""
👋 <b>سلام {user.first_name} عزیز!</b>

🔒 برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:

{channels_list}

⚠️ <b>توجه:</b> پس از عضویت، دکمه «بررسی مجدد عضویت» را بزنید.
            """
            bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='HTML')
            return
        
        user_stats = db.get_user_stats(user.id)
        remaining, current, total = db.get_remaining_downloads(user.id)  # اصلاح شده: user.id بجای user_id
        
        welcome_text = f"""
✨ <b>سلام {user.first_name} عزیز!</b>

🎉 به ربات دانلودر حرفه‌ای اینستاگرام خوش آمدید!

<b>🚀 ویژگی‌های ربات:</b>
✅ دانلود پست، ریلس، استوری
✅ کیفیت اصلی بدون افت
✅ **بدون هیچ محدودیتی در دانلود!**

<b>💡 نحوه استفاده:</b>
۱. لینک پست اینستاگرام را کپی کنید
۲. برای ربات ارسال کنید
۳. فایل را دانلود کنید

🔗 <b>کانال ما:</b> {CHANNEL_USERNAME}

<b>شروع کنید! یک لینک اینستاگرام ارسال کنید. 👇</b>
        """
        bot.send_message(message.chat.id, welcome_text, reply_markup=glass_effect_menu(user.id), parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ خطا در start_command: {e}")
        bot.reply_to(message, "⚠️ خطا در پردازش دستور. لطفاً مجدد تلاش کنید.")

# ==================== توابع سیستم پشتیبانی ====================
def support_category_selection(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("💼 اسپانسر شدن", "support_cat_sponsor"),
        ("📢 تبلیغات در ربات", "support_cat_ads"),
        ("🐞 خطا یا مشکل", "support_cat_bug"),
        ("📝 سایر موارد", "support_cat_other"),
        ("❌ انصراف", "support_cat_cancel")
    ]
    for btn in buttons:
        keyboard.add(types.InlineKeyboardButton(btn[0], callback_data=btn[1]))
    bot.send_message(message.chat.id, "🆘 <b>پشتیبانی ربات</b>\n\nلطفاً موضوع درخواست خود را انتخاب کنید:\n👇👇👇", reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('support_cat_'))
def support_category_callback(call):
    try:
        user_id = call.from_user.id
        category = call.data.replace('support_cat_', '')
        if category == 'cancel':
            bot.edit_message_text("❌ درخواست پشتیبانی لغو شد.", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            bot.answer_callback_query(call.id, "لغو شد")
            return
        category_names = {'sponsor': '💼 اسپانسر شدن', 'ads': '📢 تبلیغات در ربات', 'bug': '🐞 خطا یا مشکل', 'other': '📝 سایر موارد'}
        cat_name = category_names.get(category, 'سایر موارد')
        msg = bot.edit_message_text(
            f"🆘 <b>ارسال پیام به پشتیبانی</b>\n\n"
            f"📋 <b>موضوع:</b> {cat_name}\n\n"
            f"📝 لطفاً متن درخواست خود را ارسال کنید:\n"
            f"(متن، عکس، ویدیو، فایل و ...)\n\n"
            f"✏️ برای لغو دستور /cancel را ارسال کنید.",
            call.message.chat.id, call.message.message_id, parse_mode='HTML'
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: process_support_message(m, category, cat_name))
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"❌ خطا در support_category_callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطا", show_alert=True)

def process_support_message(message, category, category_name):
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ ارسال درخواست پشتیبانی لغو شد.", reply_markup=glass_effect_menu(message.from_user.id), parse_mode='HTML')
        return
    try:
        user = message.from_user
        admin_text = f"""
📨 <b>پیام پشتیبانی جدید</b>

👤 <b>کاربر:</b> {user.first_name} {user.last_name or ''}
🆔 <b>آیدی:</b> <code>{user.id}</code>
📎 <b>یوزرنیم:</b> @{user.username or 'ندارد'}
📋 <b>موضوع:</b> {category_name}
🕒 <b>زمان:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>📝 محتوای پیام:</b>
        """
        if message.content_type == 'text':
            bot.send_message(ADMIN_ID, admin_text + f"\n{message.text}", parse_mode='HTML')
        elif message.content_type == 'photo':
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text + (f"\n{message.caption}" if message.caption else ""), parse_mode='HTML')
        elif message.content_type == 'video':
            bot.send_video(ADMIN_ID, message.video.file_id, caption=admin_text + (f"\n{message.caption}" if message.caption else ""), parse_mode='HTML')
        elif message.content_type == 'document':
            bot.send_document(ADMIN_ID, message.document.file_id, caption=admin_text + (f"\n{message.caption}" if message.caption else ""), parse_mode='HTML')
        elif message.content_type == 'audio':
            bot.send_audio(ADMIN_ID, message.audio.file_id, caption=admin_text + (f"\n{message.caption}" if message.caption else ""), parse_mode='HTML')
        elif message.content_type == 'voice':
            bot.send_voice(ADMIN_ID, message.voice.file_id, caption=admin_text, parse_mode='HTML')
        elif message.content_type == 'sticker':
            bot.send_sticker(ADMIN_ID, message.sticker.file_id)
            bot.send_message(ADMIN_ID, admin_text + "\n[استیکر]", parse_mode='HTML')
        elif message.content_type == 'animation':
            bot.send_animation(ADMIN_ID, message.animation.file_id, caption=admin_text + (f"\n{message.caption}" if message.caption else ""), parse_mode='HTML')
        else:
            bot.send_message(ADMIN_ID, admin_text + "\n[محتوای قابل نمایش نیست]", parse_mode='HTML')
        
        bot.send_message(
            message.chat.id,
            f"✅ <b>پیام شما با موفقیت ارسال شد!</b>\n\n"
            f"📋 <b>موضوع:</b> {category_name}\n"
            f"🆔 <b>کد پیگیری:</b> {user.id}-{datetime.now().strftime('%H%M%S')}\n\n"
            f"📌 در اسرع وقت پاسخ شما از طریق همین ربات ارسال خواهد شد.",
            reply_markup=glass_effect_menu(user.id), parse_mode='HTML'
        )
        logger.info(f"📨 پیام پشتیبانی از {user.id} با موضوع {category_name} به ادمین ارسال شد")
    except Exception as e:
        logger.error(f"❌ خطا در process_support_message: {e}")
        bot.send_message(message.chat.id, "❌ <b>خطا در ارسال پیام!</b>\nلطفاً دوباره تلاش کنید یا با پشتیبانی مستقیم تماس بگیرید.", reply_markup=glass_effect_menu(message.from_user.id), parse_mode='HTML')

# ==================== پردازش پیام‌ها ====================
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    try:
        user_id = message.from_user.id
        text = message.text.strip()
        
        is_subscribed, not_joined = check_subscription(user_id)
        if not is_subscribed:
            keyboard = types.InlineKeyboardMarkup()
            for channel_info in not_joined:
                keyboard.add(types.InlineKeyboardButton(f"عضویت در {channel_info['username']}", url=channel_info['link']))
            keyboard.add(types.InlineKeyboardButton("✅ بررسی مجدد", callback_data=f"check_sub_{user_id}"))
            bot.reply_to(message, f"⚠️ <b>لطفاً ابتدا در کانال‌های زیر عضو شوید:</b>\n\n" + "\n".join([f"• {chan['username']}" for chan in not_joined]), reply_markup=keyboard, parse_mode='HTML')
            return
        
        if text == "🌐 دانلود از اینستاگرام":
            bot.reply_to(message,
                f"📥 <b>سیستم دانلود فعال</b>\n\n"
                f"🎉 شما می‌توانید بدون محدودیت دانلود کنید!\n\n"
                f"🔗 <b>لطفاً لینک اینستاگرام را ارسال کنید:</b>\n\n"
                f"مثال: https://www.instagram.com/p/...\n"
                f"یا https://www.instagram.com/reel/...",
                parse_mode='HTML'
            )
        
        elif text == "📊 آمار کاربری من":
            user = message.from_user
            db.add_or_update_user(user.id, user.username, user.first_name, user.last_name)
            user_stats = db.get_user_stats(user.id)
            if user_stats:
                join_date = user_stats[4]
                if isinstance(join_date, str):
                    join_date = join_date[:10]
                else:
                    join_date = 'جدید'
                remaining, current, total = db.get_remaining_downloads(user.id)
                is_vip = db.is_vip(user.id)
                stats_text = f"""
📊 <b>آمار کاربری شما</b>

<b>👤 اطلاعات شخصی:</b>
├ نام: {user_stats[2] or 'ندارد'}
├ یوزرنیم: @{user_stats[1] or 'ندارد'}
├ آیدی: <code>{user_stats[0]}</code>
└ عضویت: {join_date}
"""
                if is_vip:
                    vip_until = user_stats[14]
                    if vip_until:
                        stats_text += f"⭐ <b>وضعیت: کاربر ویژه (تا {vip_until})</b>\n"
                    else:
                        stats_text += "⭐ <b>وضعیت: کاربر ویژه (دائمی)</b>\n"
                stats_text += f"""
<b>📥 آمار دانلود:</b>
├ کل دانلودها: {user_stats[7] or 0}
├ دعوت‌ها: {user_stats[10] or 0}
└ وضعیت: نامحدود

🔗 <b>کانال ما:</b> {CHANNEL_USERNAME}
                """
                bot.reply_to(message, stats_text, parse_mode='HTML')
            else:
                stats_text = f"""
📊 <b>آمار کاربری شما</b>

<b>👤 اطلاعات شخصی:</b>
├ نام: {user.first_name}
├ یوزرنیم: @{user.username or 'ندارد'}
├ آیدی: <code>{user.id}</code>
└ عضویت: امروز

<b>📥 آمار دانلود:</b>
├ کل دانلودها: 0
├ دعوت‌ها: 0
└ وضعیت: نامحدود

🔗 <b>کانال ما:</b> {CHANNEL_USERNAME}
                """
                bot.reply_to(message, stats_text, parse_mode='HTML')
        
        elif text == "👑 پنل مدیریت":
            if user_id == ADMIN_ID:
                total_users, total_requests, total_downloads, total_vip = db.get_total_stats()
                admin_text = f"""
👑 <b>پنل مدیریت ربات</b>

📊 <b>آمار کلی:</b>
├ کاربران: {total_users} نفر
├ درخواست‌ها: {total_requests} بار
└ دانلودها: {total_downloads} فایل
⭐ کاربران ویژه: {total_vip} نفر

🕒 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>لطفاً گزینه مورد نظر را انتخاب کنید:</b>
                """
                bot.send_message(message.chat.id, admin_text, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
            else:
                bot.reply_to(message, "⛔ <b>دسترسی محدود!</b>", parse_mode='HTML')
        
        elif text == "ℹ️ راهنمای استفاده":
            help_text = f"""
📚 <b>راهنمای کامل ربات</b>

<b>🎯 نحوه استفاده:</b>
۱. لینک پست/ریلس/استوری اینستاگرام را کپی کنید
۲. در ربات ارسال کنید (پیست کنید)
۳. منتظر دانلود باشید

<b>🚀 ویژگی‌ها:</b>
• بدون هیچ محدودیتی در تعداد دانلود
• کیفیت اصلی
• پشتیبانی از پست، ریلس، استوری

<b>🎁 سیستم دعوت:</b>
هر دوستی که با لینک شما بیاید، یک دعوت به آمار شما اضافه می‌شود.

<b>⭐ کاربر ویژه:</b>
فقط برای نمایش – همه کاربران عملاً ویژه هستند.

<b>🆘 پشتیبانی:</b> {SUPPORT_USERNAME}
<b>📢 کانال:</b> {CHANNEL_USERNAME}
            """
            bot.reply_to(message, help_text, parse_mode='HTML')
        
        elif text == "🆘 پشتیبانی":
            support_category_selection(message)
        
        elif text == "👥 دعوت دوستان":
            user = message.from_user
            db.add_or_update_user(user.id, user.username, user.first_name, user.last_name)
            invite_link = db.get_invite_link(user.id, bot.get_me().username)
            user_stats = db.get_user_stats(user.id)
            invite_count = user_stats[10] if user_stats and user_stats[10] else 0
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "📱 اشتراک‌گذاری لینک", 
                url=f"https://t.me/share/url?url={invite_link}&text=🎉 ربات دانلودر اینستاگرام! بدون تبلیغات و کاملاً رایگان!"
            ))
            bot.reply_to(
                message,
                f"📣 <b>سیستم دعوت دوستان</b>\n\n"
                f"🎁 <b>با دعوت دوستان، آمار دعوت‌های شما افزایش می‌یابد!</b>\n\n"
                f"🔗 <b>لینک اختصاصی شما:</b>\n"
                f"<code>{invite_link}</code>\n\n"
                f"📊 <b>دعوت‌های شما:</b> {invite_count} نفر\n\n"
                f"💡 <b>روش استفاده:</b>\n"
                f"۱. این لینک را برای دوستان بفرستید\n"
                f"۲. دوستان روی لینک کلیک کنند\n"
                f"۳. دعوت شما ثبت می‌شود\n\n"
                f"🔗 <b>کانال ما:</b> {CHANNEL_USERNAME}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        elif 'instagram.com' in text:
            if not ('https://www.instagram.com/' in text or 'http://www.instagram.com/' in text):
                bot.reply_to(message, "⚠️ <b>لینک نامعتبر!</b>\n\nلطفاً لینک معتبر اینستاگرام ارسال کنید.\nمثال: https://www.instagram.com/p/...", parse_mode='HTML')
                return
            
            processing_msg = bot.reply_to(message, "⏳ <b>در حال پردازش لینک...</b>\n\nلطفاً چند ثانیه صبر کنید.", parse_mode='HTML')
            result = download_instagram_content(text)
            
            if result.get('success'):
                data = result.get('data', {})
                db.increment_download(user_id)
                db.log_request(user_id, text, 'download', True, result.get('response_time', 0))
                try:
                    bot.delete_message(message.chat.id, processing_msg.message_id)
                except:
                    pass
                
                files_sent = 0
                files = data.get('files', [])
                if not files:
                    bot.reply_to(message, "❌ <b>فایلی برای دانلود یافت نشد!</b>\n\nلطفاً لینک دیگری ارسال کنید.", parse_mode='HTML')
                    return
                
                for file in files:
                    try:
                        if file.get('type') == 'video':
                            bot.send_video(chat_id=message.chat.id, video=file.get('url'),
                                caption=f"✅ <b>دانلود موفق!</b>\n\n🎬 <b>نوع:</b> ویدیو\n📊 <b>کیفیت:</b> {file.get('quality', 'HD')}\n👤 <b>سازنده:</b> {data.get('author', 'اینستاگرام')}\n\n✨ <b>ممنون از دانلودت!</b>\n🔗 {CHANNEL_USERNAME}",
                                parse_mode='HTML')
                            files_sent += 1
                            time.sleep(1)
                        elif file.get('type') == 'image':
                            bot.send_photo(chat_id=message.chat.id, photo=file.get('url'),
                                caption=f"✅ <b>دانلود موفق!</b>\n\n📸 <b>نوع:</b> عکس\n👤 <b>سازنده:</b> {data.get('author', 'اینستاگرام')}\n\n✨ <b>ممنون از دانلودت!</b>\n🔗 {CHANNEL_USERNAME}",
                                parse_mode='HTML')
                            files_sent += 1
                            time.sleep(1)
                    except Exception as e:
                        logger.error(f"❌ خطا در ارسال فایل: {e}")
                        continue
                
                if files_sent > 0:
                    success_text = f"""
✨ <b>عملیات دانلود با موفقیت انجام شد!</b>

✅ <b>{files_sent} فایل ارسال شد.</b>

🔗 {CHANNEL_USERNAME}
                    """
                    bot.send_message(message.chat.id, success_text, parse_mode='HTML')
                else:
                    bot.reply_to(message, "❌ <b>خطا در ارسال فایل‌ها!</b>\n\nلطفاً مجدد تلاش کنید یا با پشتیبانی تماس بگیرید.", parse_mode='HTML')
            else:
                db.log_request(user_id, text, 'download', False, result.get('response_time', 0))
                error_msg = result.get('error', 'خطای ناشناخته')
                bot.edit_message_text(
                    f"❌ <b>خطا در دانلود!</b>\n\n📛 <b>علت خطا:</b> {error_msg}\n\n🔍 <b>راه‌حل‌ها:</b>\n• لینک را بررسی کنید\n• از لینک اصلی استفاده کنید\n• پست خصوصی قابل دانلود نیست\n• چند دقیقه دیگر تلاش کنید\n\n🆘 <b>پشتیبانی:</b> {SUPPORT_USERNAME}",
                    message.chat.id, processing_msg.message_id, parse_mode='HTML'
                )
        else:
            bot.reply_to(message, f"🤖 <b>سلام!</b>\n\nلطفاً یکی از گزینه‌های منو را انتخاب کنید.\n\n🔗 <b>کانال ما:</b> {CHANNEL_USERNAME}", reply_markup=glass_effect_menu(user_id), parse_mode='HTML')
    except Exception as e:
        logger.error(f"❌ خطا در handle_messages: {e}")
        bot.reply_to(message, "⚠️ <b>خطا در پردازش پیام!</b>\n\nلطفاً مجدد تلاش کنید.", parse_mode='HTML')

# ==================== مدیریت Callback ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        if call.data.startswith('check_sub_'):
            user_id = int(call.data.split('_')[2])
            if call.from_user.id != user_id:
                bot.answer_callback_query(call.id, "این دکمه برای شما نیست!", show_alert=True)
                return
            is_subscribed, not_joined = check_subscription(user_id)
            if is_subscribed:
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                bot.send_message(user_id, "✅ <b>عالی! عضویت شما تایید شد.</b>\n\n🎉 حالا می‌توانید از ربات استفاده کنید!\n\n🔽 <b>لطفاً از منوی زیر گزینه مورد نظر را انتخاب کنید:</b>", reply_markup=glass_effect_menu(user_id), parse_mode='HTML')
                bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
            else:
                keyboard = types.InlineKeyboardMarkup()
                for channel_info in not_joined:
                    keyboard.add(types.InlineKeyboardButton(f"عضویت در {channel_info['username']}", url=channel_info['link']))
                keyboard.add(types.InlineKeyboardButton("✅ بررسی مجدد", callback_data=f"check_sub_{user_id}"))
                try:
                    bot.edit_message_text(
                        f"⚠️ <b>هنوز در کانال‌های زیر عضو نیستید:</b>\n\n" +
                        "\n".join([f"• {chan['username']}" for chan in not_joined]) +
                        f"\n\n📌 پس از عضویت روی «بررسی مجدد» کلیک کنید.",
                        call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML'
                    )
                except:
                    pass
                bot.answer_callback_query(call.id, f"هنوز در {len(not_joined)} کانال عضو نیستید!", show_alert=True)
        
        elif call.from_user.id == ADMIN_ID:
            if call.data == "admin_stats":
                total_users, total_requests, total_downloads, total_vip = db.get_total_stats()
                stats_text = f"""
📊 <b>آمار کلی ربات</b>

👥 <b>کاربران کل:</b> {total_users} نفر
📥 <b>درخواست‌ها:</b> {total_requests} بار
⬇️ <b>دانلودها:</b> {total_downloads} فایل
⭐ <b>کاربران ویژه:</b> {total_vip} نفر
💾 <b>حافظه دیتابیس:</b> (در Supabase قابل نمایش نیست)

🕒 <b>زمان:</b> {datetime.now().strftime('%H:%M:%S')}
                """
                bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
            elif call.data == "admin_today":
                users = db.get_all_users()
                today = datetime.now().date()
                today_users = []
                for user in users:
                    if user[4]:
                        try:
                            join_date = datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S').date() if isinstance(user[4], str) else user[4]
                            if join_date == today:
                                today_users.append(user)
                        except:
                            continue
                if today_users:
                    text = "👥 <b>کاربران امروز</b>\n\n"
                    for i, user in enumerate(today_users[:20], 1):
                        vip_status = "⭐" if db.is_vip(user[0]) else ""
                        text += f"{i}. {user[2] or 'بدون نام'} (@{user[1] or 'ندارد'}) {vip_status}\n"
                    if len(today_users) > 20:
                        text += f"\n📈 <b>تعداد کل:</b> {len(today_users)} کاربر"
                else:
                    text = "📭 <b>امروز کاربر جدیدی نیامده است</b>"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
            elif call.data == "admin_manage_vip":
                vip_users = db.get_vip_users()
                vip_count = len(vip_users)
                vip_text = f"""
⭐ <b>مدیریت کاربران ویژه</b>

👥 <b>تعداد VIP‌ها:</b> {vip_count} نفر

<b>🔧 گزینه‌های مدیریت:</b>
• افزودن کاربر به VIP
• حذف کاربر از VIP
• تنظیم مدت VIP
• مشاهده لیست VIP‌ها

<b>⚠️ توجه:</b> کاربران ویژه فقط برای نمایش هستند (همه عملاً ویژه‌اند).
                """
                bot.edit_message_text(vip_text, call.message.chat.id, call.message.message_id, reply_markup=vip_management_panel(), parse_mode='HTML')
            elif call.data == "admin_add_vip":
                msg = bot.send_message(call.message.chat.id, "➕ <b>افزودن کاربر به VIP</b>\n\n👤 <b>آیدی کاربر را ارسال کنید:</b>\nمثال: 123456789\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_add_vip)
            elif call.data == "admin_remove_vip":
                vip_users = db.get_vip_users()
                if vip_users:
                    keyboard = types.InlineKeyboardMarkup()
                    for user in vip_users[:20]:
                        user_id = user['user_id']
                        username = user.get('username', '')
                        first_name = user.get('first_name', '')
                        display_name = first_name or username or f"User {user_id}"
                        keyboard.add(types.InlineKeyboardButton(f"❌ {display_name} ({user_id})", callback_data=f"del_vip_{user_id}"))
                    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
                    bot.edit_message_text("❌ <b>حذف کاربر از VIP</b>\n\nبرای حذف روی نام کاربر کلیک کنید:", call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
                else:
                    bot.answer_callback_query(call.id, "کاربر VIPی وجود ندارد!", show_alert=True)
            elif call.data.startswith("del_vip_"):
                user_id = int(call.data.replace("del_vip_", ""))
                if db.set_vip(user_id, False):
                    try:
                        bot.send_message(user_id, "⚠️ <b>وضعیت VIP شما تغییر کرد!</b>\n\n❌ وضعیت کاربر ویژه شما توسط مدیریت غیرفعال شد.\n(توجه: این تغییر تأثیری در دانلود ندارد و همه کاربران نامحدود هستند.)")
                    except:
                        pass
                    bot.answer_callback_query(call.id, "✅ کاربر از VIP حذف شد!")
                    bot.edit_message_text(f"✅ <b>کاربر {user_id} از لیست VIP‌ها حذف شد!</b>", call.message.chat.id, call.message.message_id, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
                else:
                    bot.answer_callback_query(call.id, "❌ خطا در حذف VIP!", show_alert=True)
            elif call.data == "admin_list_vip":
                vip_users = db.get_vip_users()
                if vip_users:
                    text = "⭐ <b>لیست کاربران ویژه</b>\n\n"
                    for i, user in enumerate(vip_users, 1):
                        user_id = user['user_id']
                        username = user.get('username', '')
                        first_name = user.get('first_name', '')
                        vip_until = user.get('vip_until')
                        display_name = first_name or username or f"User {user_id}"
                        vip_status = f"تا {vip_until}" if vip_until else "دائمی"
                        text += f"{i}. {display_name}\n   ├ آیدی: {user_id}\n   └ وضعیت: {vip_status}\n\n"
                    text += f"📊 <b>تعداد کل:</b> {len(vip_users)} کاربر"
                else:
                    text = "📭 <b>کاربر VIPی وجود ندارد</b>"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
            elif call.data == "admin_set_vip_time":
                msg = bot.send_message(call.message.chat.id, "⏰ <b>تنظیم مدت VIP</b>\n\n📝 <b>دستور:</b> آیدی_کاربر تعداد_روز\nمثال: 123456789 30\n\nبرای VIP دائمی از 0 استفاده کنید:\nمثال: 123456789 0\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_set_vip_time)
            elif call.data == "admin_broadcast":
                msg = bot.send_message(call.message.chat.id, "📢 <b>ارسال پیام همگانی</b>\n\nهر نوع محتوایی را ارسال کنید:\n📝 متن، 📸 عکس، 🎬 ویدیو، 📁 فایل، 🎵 موزیک، 📌 استیکر، 🔗 لینک\n\n⚠️ <b>توجه:</b> این پیام بدون اضافه کردن متن اضافی ارسال می‌شود.\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_broadcast)
            elif call.data == "admin_add_channel":
                msg = bot.send_message(call.message.chat.id, "➕ <b>افزودن کانال اجباری</b>\n\n🔗 <b>یوزرنیم کانال را ارسال کنید:</b>\nمثال: @ARIANA_MOOD\n\n⚠️ <i>ربات باید در کانال ادمین باشد!</i>\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_add_channel)
            elif call.data == "admin_remove_channel":
                channels = db.get_required_channels()
                if channels:
                    keyboard = types.InlineKeyboardMarkup()
                    for channel in channels:
                        keyboard.add(types.InlineKeyboardButton(f"حذف {channel['channel_username']}", callback_data=f"del_chan_{channel['channel_username']}"))
                    keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
                    bot.edit_message_text("📋 <b>کانال‌های اجباری</b>\n\nبرای حذف روی نام کانال کلیک کنید:", call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
                else:
                    bot.answer_callback_query(call.id, "کانالی وجود ندارد!", show_alert=True)
            elif call.data.startswith("del_chan_"):
                channel_username = call.data.replace("del_chan_", "")
                if db.remove_required_channel(channel_username):
                    bot.answer_callback_query(call.id, "✅ حذف شد!")
                    bot.edit_message_text(f"✅ <b>کانال {channel_username} با موفقیت حذف شد!</b>", call.message.chat.id, call.message.message_id, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
                else:
                    bot.answer_callback_query(call.id, "❌ خطا در حذف!", show_alert=True)
            elif call.data == "admin_list_channels":
                channels = db.get_required_channels()
                if channels:
                    text = "📋 <b>کانال‌های اجباری</b>\n\n"
                    for chan in channels:
                        text += f"• {chan['channel_username']}\n  └ {chan['channel_link']}\n"
                else:
                    text = "📭 <b>کانالی وجود ندارد</b>"
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='HTML')
            elif call.data == "admin_back":
                bot.edit_message_text("👑 <b>پنل مدیریت</b>\n\nلطفاً گزینه مورد نظر را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
            elif call.data == "admin_reset_user":
                msg = bot.send_message(call.message.chat.id, "🔄 <b>ریست دانلود کاربر</b>\n\n👤 <b>آیدی کاربر را ارسال کنید:</b>\nمثال: 123456789\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_reset_user)
            elif call.data == "admin_message_user":
                msg = bot.send_message(call.message.chat.id, "📨 <b>پیام به کاربر</b>\n\n👤 <b>آیدی کاربر را ارسال کنید:</b>\nمثال: 123456789\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
                bot.register_next_step_handler(msg, process_message_user_step1)
            elif call.data == "admin_backup":
                db.backup_database()
                bot.send_message(call.message.chat.id, "⚠️ <b>پشتیبان‌گیری در Supabase از طریق کد ممکن نیست.</b>\n\nلطفاً از داشبورد Supabase برای پشتیبان‌گیری استفاده کنید.", parse_mode='HTML')
                bot.answer_callback_query(call.id, "❌ امکان پشتیبان‌گیری وجود ندارد", show_alert=True)
            elif call.data == "admin_restart":
                bot.answer_callback_query(call.id, "🔄 ربات در حال بازخوانی...")
                bot.send_message(ADMIN_ID, f"🔄 <b>ربات با موفقیت بازخوانی شد!</b>\n\n🕒 زمان: {datetime.now().strftime('%H:%M:%S')}", parse_mode='HTML')
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"❌ خطا در handle_callbacks: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)
        except:
            pass

# ==================== توابع مدیریت VIP ====================
def process_add_vip(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ افزودن VIP لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        user_id = int(message.text)
        response = db.supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if not response.data:
            db.add_or_update_user(user_id, "", "", "")
        if db.set_vip(user_id, True):
            try:
                bot.send_message(user_id, "🎉 <b>تبریک! شما کاربر ویژه شدید!</b>\n\n⭐ <b>امتیازات کاربر ویژه:</b>\n• نشان ویژه در پروفایل شما\n• (توجه: همه کاربران عملاً ویژه هستند و محدودیتی ندارند)\n\n✨ از ربات لذت ببرید!")
            except:
                pass
            bot.send_message(message.chat.id, f"✅ <b>کاربر {user_id} با موفقیت VIP شد!</b>\n\n⭐ کاربر اکنون نشان ویژه دارد.", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "❌ <b>خطا در VIP کردن کاربر!</b>", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, "❌ <b>آیدی نامعتبر!</b>\nلطفاً عدد معتبر وارد کنید.", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

def process_set_vip_time(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ تنظیم مدت VIP لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        user_id = int(parts[0])
        days = int(parts[1])
        response = db.supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if not response.data:
            db.add_or_update_user(user_id, "", "", "")
        if days == 0:
            if db.set_vip(user_id, True, None):
                try:
                    bot.send_message(user_id, "🎉 <b>تبریک! شما کاربر ویژه دائمی شدید!</b>\n\n⭐ <b>امتیازات:</b>\n• نشان ویژه دائمی\n\n✨ از ربات لذت ببرید!")
                except:
                    pass
                bot.send_message(message.chat.id, f"✅ <b>کاربر {user_id} VIP دائمی شد!</b>", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
        elif days > 0:
            if db.set_vip(user_id, True, days):
                expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                try:
                    bot.send_message(user_id, f"🎉 <b>تبریک! شما کاربر ویژه شدید!</b>\n\n⭐ <b>امتیازات:</b>\n• نشان ویژه\n• اعتبار تا: {expiry_date}\n\n✨ از ربات لذت ببرید!")
                except:
                    pass
                bot.send_message(message.chat.id, f"✅ <b>کاربر {user_id} VIP شد!</b>\n\n📅 مدت: {days} روز\n⏰ انقضا: {expiry_date}", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "❌ <b>تعداد روز نامعتبر!</b>\nبرای VIP دائمی از 0 استفاده کنید.", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, "❌ <b>فرمت نامعتبر!</b>\nفرمت صحیح: آیدی_کاربر تعداد_روز\nمثال: 123456789 30", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

# ==================== توابع مدیریت ====================
def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ ارسال همگانی لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    users = db.get_all_users()
    if not users:
        bot.send_message(message.chat.id, "❌ هیچ کاربری وجود ندارد!", reply_markup=glass_effect_admin_panel())
        return
    processing_msg = bot.send_message(message.chat.id, f"⏳ در حال ارسال به {len(users)} کاربر...")
    success = 0
    failed = 0
    for user in users:
        try:
            if message.content_type == 'text':
                bot.send_message(user[0], message.text, parse_mode='HTML', disable_web_page_preview=True)
            elif message.content_type == 'photo':
                bot.send_photo(user[0], message.photo[-1].file_id, caption=message.caption or '', parse_mode='HTML')
            elif message.content_type == 'video':
                bot.send_video(user[0], message.video.file_id, caption=message.caption or '', parse_mode='HTML')
            elif message.content_type == 'document':
                bot.send_document(user[0], message.document.file_id, caption=message.caption or '', parse_mode='HTML')
            elif message.content_type == 'audio':
                bot.send_audio(user[0], message.audio.file_id, caption=message.caption or '', parse_mode='HTML')
            elif message.content_type == 'voice':
                bot.send_voice(user[0], message.voice.file_id)
            elif message.content_type == 'sticker':
                bot.send_sticker(user[0], message.sticker.file_id)
            elif message.content_type == 'animation':
                bot.send_animation(user[0], message.animation.file_id, caption=message.caption or '', parse_mode='HTML')
            success += 1
            time.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.error(f"❌ خطا در ارسال به کاربر {user[0]}: {e}")
    try:
        bot.delete_message(message.chat.id, processing_msg.message_id)
    except:
        pass
    report_text = f"""
✅ <b>گزارش ارسال همگانی</b>

👥 <b>کاربران کل:</b> {len(users)}
✅ <b>موفق:</b> {success}
❌ <b>ناموفق:</b> {failed}
📊 <b>درصد موفقیت:</b> {(success/len(users)*100):.1f}%

🕒 <b>زمان:</b> {datetime.now().strftime('%H:%M:%S')}
    """
    bot.send_message(message.chat.id, report_text, reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

def process_add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ افزودن کانال لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        channel_username = message.text.strip()
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        db.add_required_channel(channel_username)
        bot.send_message(message.chat.id, f"✅ <b>کانال {channel_username} با موفقیت اضافه شد!</b>\n\n🔗 لینک: https://t.me/{channel_username.replace('@', '')}\n\n👤 از این پس کاربران جدید باید در این کانال عضو شوند.", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>خطا در افزودن کانال!</b>\n\n{str(e)}", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

def process_reset_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ ریست کاربر لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        user_id = int(message.text)
        bot.send_message(message.chat.id, f"✅ <b>عملیات ریست برای کاربر {user_id} انجام شد (بدون تأثیر).</b>", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, "❌ <b>آیدی نامعتبر!</b>\nلطفاً عدد معتبر وارد کنید.", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

def process_message_user_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ ارسال پیام لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, "📝 <b>پیام خود را وارد کنید:</b>\n\nهر نوع محتوایی را می‌توانید ارسال کنید.\n\n✏️ <i>برای لغو دستور /cancel را ارسال کنید.</i>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: process_message_user_step2(m, user_id))
    except:
        bot.send_message(message.chat.id, "❌ <b>آیدی نامعتبر!</b>", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

def process_message_user_step2(message, user_id):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text and message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "❌ ارسال پیام لغو شد.", reply_markup=glass_effect_admin_panel())
        return
    try:
        if message.content_type == 'text':
            bot.send_message(user_id, message.text, parse_mode='HTML')
        elif message.content_type == 'photo':
            bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or '', parse_mode='HTML')
        elif message.content_type == 'video':
            bot.send_video(user_id, message.video.file_id, caption=message.caption or '', parse_mode='HTML')
        elif message.content_type == 'document':
            bot.send_document(user_id, message.document.file_id, caption=message.caption or '', parse_mode='HTML')
        bot.send_message(message.chat.id, f"✅ <b>پیام با موفقیت به کاربر {user_id} ارسال شد!</b>", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>خطا در ارسال پیام!</b>\n\n{str(e)}", reply_markup=glass_effect_admin_panel(), parse_mode='HTML')

# ==================== راه‌اندازی ربات ====================
def start_bot():
    print("\n" + "=" * 60)
    print("🚀 در حال راه‌اندازی ربات با Supabase (رفع مشکل آمار)...")
    print("=" * 60)
    try:
        db.supabase.table('users').select('count', count='exact').limit(1).execute()
        print("✅ اتصال به Supabase برقرار است")
        try:
            db.add_required_channel(CHANNEL_USERNAME)
            print(f"✅ کانال اصلی {CHANNEL_USERNAME} اضافه شد")
        except:
            print(f"⚠️ کانال اصلی از قبل وجود دارد")
        bot_info = bot.get_me()
        print(f"✅ ربات: @{bot_info.username}")
        print(f"🆔 آیدی ربات: {bot_info.id}")
        print(f"👑 ادمین: {ADMIN_ID}")
        print(f"📢 کانال: {CHANNEL_USERNAME}")
        total_users, total_requests, total_downloads, total_vip = db.get_total_stats()
        print(f"📊 آمار: {total_users} کاربر، {total_requests} درخواست، {total_downloads} دانلود، {total_vip} VIP")
        print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("\n📱 ربات آنلاین و آماده است!")
        print("⭐ ویژگی: حذف محدودیت دانلود برای همه کاربران")
        print("💡 دستورات:")
        print("   /start - شروع ربات")
        print("=" * 60)
        try:
            bot.send_message(ADMIN_ID, f"✅ <b>ربات با حذف محدودیت راه‌اندازی شد!</b>\n\n🤖 ربات: @{bot_info.username}\n👥 کاربران: {total_users}\n📥 درخواست‌ها: {total_requests}\n⬇️ دانلودها: {total_downloads}\n⭐ VIP‌ها: {total_vip}\n🕒 زمان: {datetime.now().strftime('%H:%M:%S')}\n\n👑 برای دسترسی به پنل مدیریت، دکمه «👑 پنل مدیریت» را از منو انتخاب کنید.", parse_mode='HTML', reply_markup=glass_effect_menu(ADMIN_ID))
        except Exception as e:
            print(f"⚠️ خطا در اطلاع به ادمین: {e}")
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی: {e}")
        print("🔄 تلاش مجدد در 15 ثانیه...")
        time.sleep(15)
        start_bot()

if __name__ == "__main__":
    print("🤖 شروع برنامه...")
    start_bot()
