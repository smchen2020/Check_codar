# %%
'''
檢查 CODAR 測站
'''
import os
import datetime
import smtplib
from email.mime.text import MIMEText

# Email 設定
EMAIL_FROM = "shiming.chen@gmail.com"       # <-- 改成你的 Gmail
with open("gmail_app.txt") as f:
    # 從檔案讀取 Gmail 應用程式密碼
    EMAIL_APP_PASSWORD = f.read().strip()

nsending = 4   # 每次寄信的間隔小時數
seasonde_dir = "CodarData/Codar/SeaSonde"

# 建立測站與負責人對應的字典
# 徑向資料站點負責人
site_person = {
    "BABY": ["shiming.chen@gmail.com", "shiming.chen@gmail.com"],
    "CIHO": ["shiming.chen@gmail.com", "shiming.chen@gmail.com"],
    "FALA": ["shiming.chen@gmail.com", "shiming.chen@gmail.com"],
    "HPON": ["shiming.chen@gmail.com", "shiming.chen@gmail.com"],
    "HOWN": ["shiming.chen@gmail.com", "shiming.chen@gmail.com"],
    # "LUYE": ["shiming.chen@gmail.com"],
    # "MABT": ["shiming.chen@gmail.com"],
    # "NAWN": ["shiming.chen@gmail.com"],
    # "PETI": ["shiming.chen@gmail.com"],
    # "SDGO": ["shiming.chen@gmail.com"],
    # "SHIA": ["shiming.chen@gmail.com"],
    # "SUHI": ["shiming.chen@gmail.com"],
    # "OHAL": ["shiming.chen@gmail.com"],
}

# 合成資料負責人
toro_mail = ["shiming.chen@gmail.com"]


# 加上時間標記的 log 輸出
def log(fname, msg):

    with open(f'Log/{fname}', 'a') as f:
        f.write(f"{msg}\n")


# 取得過去幾小時的時間資訊（年、月、日、時）用於組檔名
def get_past_time(t_in):

    return {
        "year": t_in.strftime('%Y'),
        "month": t_in.strftime('%m'),
        "day": t_in.strftime('%d'),
        "hour": t_in.strftime('%H'),
    }


# 組合檔案完整路徑（根據時間與站名）
def generate_filename_radial(time_data, site, path, ideal_or_meas):

    if ideal_or_meas.lower() == 'ideal':
        str1 = f"RDLi_{site.upper()}_"
    else:
        str1 = f"RDLm_{site.upper()}_"

    str2 = f"{time_data['year']}_"
    str3 = f"{time_data['month']}_"
    str4 = f"{time_data['day']}_"
    str5 = f"{time_data['hour']}00"
    filename = str1 + str2 + str3 + str4 + str5 + ".ruv"
    return os.path.join(path, filename)


def generate_filename_totals(time_data, path):

    str1 = f"TOTL_{path[-4:]}_"
    str2 = f"{time_data['year']}_"
    str3 = f"{time_data['month']}_"
    str4 = f"{time_data['day']}_"
    str5 = f"{time_data['hour']}00"
    filename = str1 + str2 + str3 + str4 + str5 + ".tuv"
    return os.path.join(path, filename)


# 檢查檔案大小（若不存在則返回 0）
def get_file_size(filepath):

    try:
        return os.path.getsize(filepath)
    except FileNotFoundError:
        return 0  # 若檔案不存在，返回大小為 0


# 使用 Gmail SMTP 發送 Email
def send_email_via_gmail(subject, message, recipient):

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ",".join(recipient)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipient, msg.as_string())
        print(f"✅ Email sent to {recipient} via Gmail.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def get_file_size_radial(t, site, ideal_or_meas):

    path_radial = f"{seasonde_dir}/Data/RadialSites/Site_{site}_{ideal_or_meas.lower()}/"
    filepath = generate_filename_radial(t, site, path_radial, ideal_or_meas)
    file_size = get_file_size(filepath)

    return file_size, filepath


def get_file_size_totals(t, tor4_or_toro):

    path_totals = f"{seasonde_dir}/Data/Totals/Totals_{tor4_or_toro.upper()}"
    filepath = generate_filename_totals(t, path_totals)
    file_size = get_file_size(filepath)

    return file_size, filepath


def check_radial(t_radar, t_now, min_file_size=1000):

    # 設定目前時間
    t_now_str = t_now.strftime("[%Y-%m-%d %H:%M:%S UTC+8]")
    t_radar_log = f"{t_radar['year']}_{t_radar['month']}_{t_radar['day']}_{t_radar['hour']}00"

    fname = t_now.strftime("%Y-%m-%d.log")
    log(fname, f"Radial 檢查時間: {t_now_str}")

    # 檢索所有站點
    for site in list(site_person.keys()):

        warning = {'meas': False, 'ideal': False}
        filepath = {}

        for ideal_or_meas in ['meas', 'ideal']:

            # 檢查 radial ideal 資料檔案大小
            file_size, filepath[ideal_or_meas] = get_file_size_radial(t_radar, site, ideal_or_meas)

            # 如果檔案大小小於最小值，則記錄異常並發送警告郵件
            if file_size < min_file_size:
                warning[ideal_or_meas] = True
                
        if warning['meas'] and warning['ideal']:

            log_msg = f"*{site}* 異常 {t_radar_log}"
            log(fname, log_msg)

            # 檢查是否已經寄出警告信，如果已寄出就不再寄，
            # 除非寄出後經過設定的次數後仍然異常，則再寄一次
            site_str = f"{site}"
            to_send = check_sending(site_str, t_radar)

            if to_send:
                # 寄出警告信
                subject = f"{site} Radial 異常警示"
                message = f"{site} {t_radar_log} 檔案異常，請盡速確認系統狀況。\n\n"
                
                if warning['meas']:
                    message += f"{filepath['meas']}\n"
                if warning['ideal']:
                    message += f"{filepath['ideal']}\n"
                
                send_email_via_gmail(subject, message, site_person[site])

        else:
            
            log_msg = f" {site}  正常 {t_radar_log}"
            if warning['meas'] == False:
                log_msg += " meas"
            if warning['ideal'] == False:
                log_msg += " ideal"
            
            log(fname, log_msg)
            remove_sending(f"{site}")


def check_totals(t_radar, t_now, min_file_size=1000):

    # 在 log 中記錄檢查時間
    t_now_str = t_now.strftime("[%Y-%m-%d %H:%M:%S UTC+8]")
    fname = t_now.strftime("%Y-%m-%d.log")
    log(fname, f"Totals 檢查時間: {t_now_str}")

    t_log_str = f"{t_radar['year']}_{t_radar['month']}_{t_radar['day']}_{t_radar['hour']}00"

    for dd in ['TORO', 'TOR4']:

        # 檢查 radial ideal 資料檔案大小
        file_size, filepath = get_file_size_totals(t_radar, dd)

        # 如果檔案大小小於最小值，則記錄異常並發送警告郵件
        if file_size < min_file_size:

            log_msg = f"*{dd}* 異常 {t_log_str}"
            log(fname, log_msg)

            # 檢查是否已經寄出警告信，如果已寄出就不再寄，
            # 除非寄出後經過設定的次數後仍然異常，則再寄一次
            to_send = check_sending(dd, t_radar)

            if to_send:
                # 寄出警告信
                subject = f"Totals {dd} 異常警示"
                message = f"{t_log_str} {dd} 檔案異常，請盡速確認系統狀況。"
                message += f"\n\n檔案: {filepath}\n"
                send_email_via_gmail(subject, message, toro_mail)

        else:

            log_msg = f" {dd}  正常 {t_log_str}"
            log(fname, log_msg)
            remove_sending(dd)


def check_sending(site_str, t_radar):

    # 檢查是否已經寄出警告信
    fname = f"sending_{site_str}.txt"
    if os.path.exists(fname):

        content = []
        with open(fname, 'r') as f:
            for line in f:
                content.append(line.strip())

        count = int(content[0])

        # 如果已經寄過警告信，但 count 大於設定數值後仍然異常，則再寄一次警告信
        # 同時更新警告信計數為 0
        if count >= nsending:
            to_send = True
            count = 0
        else:
            to_send = False

        # 更新警告信計數並把資料有問題的時間加入原本檔案
        with open(fname, 'w') as f:
            f.write(f"{count + 1}\n")
            for line in content[1:]:
                f.write(line + "\n")
            f.write(f"{t_radar['year']}-{t_radar['month']}-{t_radar['day']} {t_radar['hour']}:00:00\n")

    else:

        # 尚未寄信
        to_send = True
        with open(fname, 'w') as f:
            f.write("1\n")
            f.write(f"{t_radar['year']}-{t_radar['month']}-{t_radar['day']} {t_radar['hour']}:00:00\n")

    return to_send


def remove_sending(site_str):

    fname = f"sending_{site_str}.txt"
    if os.path.exists(fname):
        os.remove(fname)

#----------------------------------------------------------

# 主程式
# 檢查目前時間減去 2 小時的檔案是否正常

# 為了檢視 log 的便利性，在 log 內的時間標記會使用 UTC+8 時區
# 但雷達系統的時間是 UTC 時區，所以要注意時間的轉換
t_now_p8 = datetime.datetime.strptime("2025-06-30T20", "%Y-%m-%dT%H")   #  測試使用，之後要修改為目前時間
#t_now_p8 = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# 設定檢查時間為 2 小時前。注意：這裡的時間是 UTC 時區
delta_t_check = datetime.timedelta(hours=-2)
t_check_utc = get_past_time(t_now_p8 + delta_t_check - datetime.timedelta(hours=8))

check_radial(t_check_utc, t_now_p8)
check_totals(t_check_utc, t_now_p8)
