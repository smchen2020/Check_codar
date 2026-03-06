# %%
'''
寄送 log 內容
'''
import datetime
from email.mime.multipart import MIMEMultipart
import smtplib
from email.mime.text import MIMEText

# Email 設定
EMAIL_FROM = "shiming.chen@gmail.com"       # <-- 改成你的 Gmail
with open("gmail_app.txt") as f:
    # 從檔案讀取 Gmail 應用程式密碼
    EMAIL_APP_PASSWORD = f.read().strip()

#recipient = ["chiayan.cheng@gmail.com", "shaohua@niar.org.tw"]
recipient = ["chiayan.cheng@gmail.com", "shaohua@niar.org.tw", "shiming.chen@gmail.com"]
#recipient = ["shiming.chen@gmail.com"]


# 使用 Gmail SMTP 發送 Email
def send_email_via_gmail(subject, message, recipient):

    # msg = MIMEText(message)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ",".join(recipient)
    msg.attach(MIMEText(message, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


#----------------------------------------------------------

t_now_p8 = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
check_date = t_now_p8 - datetime.timedelta(hours=24)
day = check_date.day
month = check_date.month
year = check_date.year

log_name = f"{year}-{month:02}-{day:02}.log"
with open(f"Log/{log_name}", "r") as f:
    log_content = f.readlines()

# 將 log 內容的時間順序反轉
# 分段：每遇到 "檢查時間" 開頭的行就開始新區塊
blocks = []
current_block = []

for line in log_content:

    if "Radial 檢查時間" in line and current_block:
        blocks.append(current_block)
        current_block = []

    current_block.append(line)

if current_block:
    blocks.append(current_block)

# 反轉區塊順序（由新至舊）
blocks = blocks[::-1]

# 合併回單一 list
log_content_new = []
for block in blocks:
    log_content_new.extend(block)

# 將 log 內容用 HTML 格式包裝
rows = [line.strip().split(maxsplit=4) for line in log_content_new]

html = "<html><body><table>"

for row in rows:

    row[0] = row[0].strip("*")

    if "異常" in row[1]:
        row[1] = f'<span style="color:red;font-weight:bold;">{row[1]}</span>'

    if "檢查時間" in row[1]:
        html += f'<tr><th colspan="5">{" ".join(row)}</th></tr>\n'
    else:
        html += f'<tr><td>{"</td><td>".join(row)}</td></tr>\n'

html += "</table></body></html>"

send_email_via_gmail(f"Log Report - {log_name}", html, recipient)

print(f'OK to send log  {t_now_p8}')
