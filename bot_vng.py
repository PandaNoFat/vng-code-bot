import requests
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- ĐỌC TỪ BIẾN MÔI TRƯỜNG (Không hardcode nữa) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COOKIE_STRING = os.getenv("COOKIE_STRING")

ACCOUNTS_INFO = {
    "ID1": "EJ7Z-CDRL-LMYC",
    "ID2": "3LCD-HS9L-LMYC",
    "ID3": "WM7A-V4RL-LMGG",
    "ID4": "VM7C-AVZL-LMYY"
}

VNG_API_URL = "https://vgrapi-sea.vnggames.com/coordinator/api/v1/code/redeem"

VNG_HEADERS = {
    "Cookie": COOKIE_STRING,
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0",
    "x-client-region": "VN"   # 👈 Đã sửa đúng tên header
}

async def call_redeem_api(role_id, code):
    payload = {"serverId": "2", "gameCode": "C15", "roleId": role_id, "roleName": role_id, "code": code}
    try:
        response = requests.post(VNG_API_URL, json=payload, headers=VNG_HEADERS, timeout=10)
        text_content = response.text
        
        # Bắt lỗi 403 (WAF chặn)
        if response.status_code == 403:
            return "error", f"⛔ VNG đã chặn IP (Status 403). Token WAF hết hạn hoặc IP thay đổi.\nNội dung: {text_content[:100]}..."

        if response.status_code == 200:
            try:
                res_json = response.json()
                return "success", res_json.get('message', 'Thành công!')
            except:
                return "error", f"Server trả về 200 nhưng nội dung không phải JSON: {text_content[:100]}..."
                
        elif response.status_code in [401, 400]:
            # Lỗi do Cookie hết hạn hoặc sai (khi chạy cùng IP mới có giá trị)
            return "expired", f"⚠️ Cookie không hợp lệ (Status {response.status_code})."
        else:
            return "error", f"Server lỗi ({response.status_code}): {text_content[:100]}..."
    except Exception as e:
        return "error", f"Lỗi kết nối: {str(e)}"

async def handle_nhapcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = update.message.text.split(" ", 1)
        if len(args) < 2:
            await update.message.reply_text("⚠️ Cú pháp: `/nhapcode MÃ1,MÃ2`")
            return
        codes = [c.strip() for c in args[1].strip().split(',') if c.strip()]
        if not codes:
            await update.message.reply_text("⚠️ Bạn chưa gửi mã code nào!")
            return
            
        await update.message.reply_text(f"🔄 Đang xử lý {len(codes)} code cho {len(ACCOUNTS_INFO)} ID...")

        report_list = []
        for acc_name, role_id in ACCOUNTS_INFO.items():
            report_list.append(f"\n👤 **{acc_name}** (`{role_id}`):")
            for code in codes:
                status, result = await call_redeem_api(role_id, code)
                if status == "success":
                    report_list.append(f"  - Code `{code}`: ✅ {result}")
                elif status == "expired":
                    report_list.append(f"  - Code `{code}`: ⚠️ {result}")
                else:
                    report_list.append(f"  - Code `{code}`: ❌ {result}")
                await asyncio.sleep(2)
            await asyncio.sleep(5)

        await update.message.reply_text("📢 Kết quả nhập Giftcode VNG\n" + "\n".join(report_list), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"💥 Bot gặp lỗi: {str(e)}")

if __name__ == "__main__":
    # Kiểm tra xem có biến môi trường chưa để tránh bot chạy khi chưa cấu hình
    if not TELEGRAM_BOT_TOKEN or not COOKIE_STRING:
        print("🚨 Lỗi: Thiếu TELEGRAM_BOT_TOKEN hoặc COOKIE_STRING trong Railway Variables!")
    else:
        print("✅ Bot VNG chạy 24/7 trên Railway. Gõ /nhapcode để dùng.")
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("nhapcode", handle_nhapcode))
        app.run_polling()
