import os
import json
import logging
import requests
import traceback
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from garminconnect import Garmin

# ==============================================================================
# CONFIGURATION & SETUP
# ==============================================================================

# Setup logging
logging.basicConfig(level=logging.INFO)

# --- CLOUD RUN FILE SYSTEM HACK ---
os.environ['HOME'] = '/tmp'
TOKEN_DIR = '/tmp/garmin_tokens'
PENDING_MFA_FILE = '/tmp/pending_mfa.json'

# --- ENVIRONMENT VARIABLES ---
GARMIN_EMAIL = os.environ.get('GARMIN_EMAIL')
GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Language Selection (Default: 'es')
LANG_CODE = os.environ.get('BOT_LANGUAGE', 'es').lower()

# Fallback Offset (Mexico City / Singapore adjustment if fallback triggered)
FALLBACK_OFFSET = -6

# --- CONSTANTS ---
EF_APP_ID = "e9f83886-2e1d-448e-aa0a-0cdfb9160df9"
EF_FIELD_NUM_GLOBAL = 2  
EF_FIELD_NUM_LAP = 1     

# ==============================================================================
# TRANSLATION DICTIONARY
# ==============================================================================
TRANS = {
    'es': {
        'loading_1': "⏳ 1/3 Conectando...",
        'loading_2': "✅ 2/3 Descargando...",
        'loading_vital': "⏳ Obteniendo signos vitales...",
        'loading_hist': "⏳ Consultando historial...",
        'err_not_found': "❌ No encontré esa actividad.",
        'err_empty': "❌ Error: Actividad vacía.",
        'err_menu': "❌ Error obteniendo menú",
        'err_morning': "❌ Error obteniendo reporte matutino",
        'mfa_prompt': "🔐 **Garmin requiere MFA**\n\nPor favor envía el código de 6 dígitos con el comando:\n`/mfa 123456`",
        'mfa_success': "✅ **MFA verificado correctamente.** Sesión guardada. Ya puedes usar tus comandos.",
        'mfa_no_pending': "⚠️ No hay ninguna solicitud MFA pendiente.",
        'mfa_invalid_format': "⚠️ Formato incorrecto. Uso: `/mfa 123456`",
        'help_msg': "🤖 **Comandos:**\n☀️ `mañana` (Salud)\n📋 `lista` (Historial)\n🔢 `0` (Último entreno)\n🔐 `/mfa 123456` (Para ingresar código Garmin)",
        'menu_title': "📋 **Últimas Actividades:**",
        'menu_footer': "👉 *Envía el número (0, 1...) para ver detalles.*",
        'morning_title': "🌅 **Reporte Matutino**",
        'sleep': "💤 **Sueño**",
        'duration': "⏱️ Duración",
        'body_batt': "🔋 **Body Battery**",
        'bb_max': "Carga máx",
        'bb_now': "Actual",
        'heart': "💓 **Corazón**",
        'rhr': "❤️ RHR (Reposo)",
        'hrv': "📉 VFC (HRV)",
        'readiness': "🚦 **Disposición**",
        'advice_go': "🚀 ¡A VOLAR! Estás a tope.",
        'advice_ok': "✅ Luz verde para entrenar.",
        'advice_warn': "⚠ Baja la carga hoy.",
        'advice_stop': "🛑 Descansa, soldado.",
        'rep_title': "🏃 **REPORTE**",
        'sec_main': "⏱️ **PRINCIPALES**",
        'sec_cardio': "❤️️ **CARDIO & CARGA**",
        'sec_eff': "⚡ **EFICIENCIA**",
        'sec_dyn': "👟 **DINÁMICAS**",
        'sec_splits': "📊 **SPLITS**",
        'lbl_dist': "Dist",
        'lbl_time': "Tiempo",
        'lbl_pace': "Ritmo",
        'lbl_gap': "GAP",
        'lbl_asc': "Asc",
        'lbl_load': "Carga",
        'lbl_zones': "*Zonas:*",
        'lbl_pow': "Potencia",
        'lbl_cal': "Cal",
        'lbl_cad': "Cad",
        'lbl_stride': "Zancada",
        'lbl_gct': "GCT",
        'lbl_osc': "Osc.V",
        'lbl_sens': "Sensación",
        'feel_map': {0: "Muy Débil", 25: "Débil", 50: "Normal", 75: "Fuerte", 100: "Muy Fuerte"}
    },
    'en': {
        'loading_1': "⏳ 1/3 Connecting...",
        'loading_2': "✅ 2/3 Downloading...",
        'loading_vital': "⏳ Fetching vital signs...",
        'loading_hist': "⏳ Fetching history...",
        'err_not_found': "❌ Activity not found.",
        'err_empty': "❌ Error: Empty activity.",
        'err_menu': "❌ Error fetching menu",
        'err_morning': "❌ Error fetching morning report",
        'mfa_prompt': "🔐 **Garmin MFA Required**\n\nPlease reply with your 6-digit code using:\n`/mfa 123456`",
        'mfa_success': "✅ **MFA successfully verified.** Session saved. You can now use all commands.",
        'mfa_no_pending': "⚠️️ No pending MFA request found.",
        'mfa_invalid_format': "⚠️ Incorrect format. Use: `/mfa 123456`",
        'help_msg': "🤖 **Bot Commands:**\n☀️ `morning` (Health)\n📋 `list` (History)\n🔢 `0` (Latest activity)\n🔐 `/mfa 123456` (Enter Garmin MFA code)",
        'menu_title': "📋 **Recent Activities:**",
        'menu_footer': "👉 *Send the number (0, 1...) for details.*",
        'morning_title': "🌅 **Morning Report**",
        'sleep': "💤 **Sleep**",
        'duration': "⏱️ Duration",
        'body_batt': "🔋 **Body Battery**",
        'bb_max': "Max charge",
        'bb_now': "Current",
        'heart': "💓 **Heart**",
        'rhr': "❤️ RHR (Resting)",
        'hrv': "📉 HRV (Status)",
        'readiness': "🚦 **Readiness**",
        'advice_go': "🚀 FULL SEND! You are ready.",
        'advice_ok': "✅ Good to go.",
        'advice_warn': "⚠️️ Take it easy today.",
        'advice_stop': "🛑 Rest day recommended.",
        'rep_title': "🏃 **REPORT**",
        'sec_main': "⏱️ **MAIN STATS**",
        'sec_cardio': "❤️ **CARDIO & LOAD**",
        'sec_eff': "⚡ **EFFICIENCY**",
        'sec_dyn': "👟 **DYNAMICS**",
        'sec_splits': "📊 **SPLITS**",
        'lbl_dist': "Dist",
        'lbl_time': "Time",
        'lbl_pace': "Pace",
        'lbl_gap': "GAP",
        'lbl_asc': "Asc",
        'lbl_load': "Load",
        'lbl_zones': "*Zones:*",
        'lbl_pow': "Power",
        'lbl_cal': "Cal",
        'lbl_cad': "Cad",
        'lbl_stride': "Stride",
        'lbl_gct': "GCT",
        'lbl_osc': "V.Osc",
        'lbl_sens': "Feeling",
        'feel_map': {0: "Very Weak", 25: "Weak", 50: "Normal", 75: "Strong", 100: "Very Strong"}
    }
}

T = TRANS.get(LANG_CODE, TRANS['es'])

# ==============================================================================
# GARMIN AUTH & MFA UTILITIES
# ==============================================================================

def get_garmin_client(chat_id=None, mfa_code=None):
    """
    Initializes Garmin client using stored tokens if available.
    If full auth is required and MFA triggers, prompts user or uses provided mfa_code.
    """
    garmin = Garmin()

    # 1. Try restoring existing session tokens first
    if os.path.exists(TOKEN_DIR):
        try:
            garmin.login(TOKEN_DIR)
            return garmin
        except Exception as e:
            logging.warning(f"Failed to restore saved token session: {e}")

    # 2. If token login fails or doesn't exist, log in with email/password
    garmin = Garmin(
        email=GARMIN_EMAIL,
        password=GARMIN_PASSWORD,
        prompt_mfa=lambda: mfa_code if mfa_code else _trigger_mfa_flow(chat_id)
    )
    garmin.login()

    # 3. Save successful session tokens for future requests
    os.makedirs(TOKEN_DIR, exist_ok=True)
    garmin.garth.dump(TOKEN_DIR)

    # Clear pending MFA state file if login succeeded
    if os.path.exists(PENDING_MFA_FILE):
        try:
            os.remove(PENDING_MFA_FILE)
        except Exception:
            pass

    return garmin

def _trigger_mfa_flow(chat_id):
    """Called when Garmin requires an MFA code during fresh login."""
    if chat_id:
        with open(PENDING_MFA_FILE, 'w') as f:
            json.dump({'chat_id': chat_id, 'timestamp': datetime.now().timestamp()}, f)
        send_telegram(chat_id, T['mfa_prompt'])

    raise Exception("MFA_REQUIRED")

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_dynamic_today(garmin_client):
    try:
        settings = garmin_client.get_user_settings()
        user_tz_name = settings.get('userData', {}).get('timeZone')
        if user_tz_name:
            user_tz = ZoneInfo(user_tz_name)
            local_now = datetime.now(user_tz)
            logging.info(f"📍 Detected Timezone: {user_tz_name} | Date: {local_now.date()}")
            return local_now.date().isoformat()
    except Exception as e:
        logging.warning(f"⚠️ Timezone detection failed, using fallback. Error: {e}")

    utc_now = datetime.now(timezone.utc)
    local_now = utc_now + timedelta(hours=FALLBACK_OFFSET)
    return local_now.date().isoformat()

def format_time(seconds):
    if not seconds: return "00:00"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02}:{s:02}"
    return f"{m:02}:{s:02}"

def format_duration_hm(seconds):
    if not seconds: return "-"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"

def format_pace(mps):
    if not mps or mps <= 0: return "-"
    seconds_per_km = 1000 / mps
    m, s = divmod(seconds_per_km, 60)
    return f"{int(m):02}:{int(s):02}"

def safe_round(val, decimals=0):
    try:
        if val is None or val == "N/A": return "-"
        f = float(val)
        if decimals == 0: return int(round(f))
        return round(f, decimals)
    except Exception:
        return val

def get_ciq_by_id(data, target_app_id, target_field_num):
    ciq_list = data.get('connectIQMeasurements') or data.get('connectIQMeasurement', [])
    if not ciq_list: return None
    for item in ciq_list:
        app_id = str(item.get('appID', ''))
        field_num = item.get('developerFieldNumber')
        try:
            if app_id == target_app_id and int(field_num) == int(target_field_num):
                return float(item.get('value'))
        except Exception:
            continue
    return None

def send_telegram(chat_id, text, use_markdown=True):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    if use_markdown:
        payload['parse_mode'] = 'Markdown'
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        if not response_data.get('ok'):
            error_desc = response_data.get('description', 'Unknown error')
            logging.error(f"⚠️ Telegram Error: {error_desc}")
            if use_markdown and ("parse" in error_desc.lower() or "markdown" in error_desc.lower()):
                send_telegram(chat_id, text, use_markdown=False)
    except Exception as e:
        logging.error(f"Connection Error: {e}")

# ==============================================================================
# MORNING REPORT LOGIC
# ==============================================================================

def get_morning_report(chat_id=None):
    try:
        garmin = get_garmin_client(chat_id=chat_id)
        today = get_dynamic_today(garmin)
        
        # 1. SLEEP
        sleep_score, sleep_qual, sleep_secs = "-", "-", 0
        sleep_range = ""
        try:
            sleep_data = garmin.get_sleep_data(today)
            daily_sleep = sleep_data.get('dailySleepDTO', {})
            sleep_score = daily_sleep.get('sleepScores', {}).get('overall', {}).get('value', '-')
            sleep_qual = daily_sleep.get('sleepScores', {}).get('overall', {}).get('qualifierKey', '').replace('_', ' ').title()
            sleep_secs = daily_sleep.get('sleepTimeSeconds', 0)
            
            start_ts = daily_sleep.get('sleepStartTimestampLocal')
            end_ts = daily_sleep.get('sleepEndTimestampLocal')
            if start_ts and end_ts:
                start_dt = datetime.fromtimestamp(start_ts / 1000)
                end_dt = datetime.fromtimestamp(end_ts / 1000)
                sleep_range = f"({start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')})"
        except Exception:
            pass
        
        # 2. BODY BATTERY
        bb_charged, bb_now = "-", "-"
        try:
            bb_data = garmin.get_body_battery(today)
            if bb_data:
                values = bb_data[0].get('bodyBatteryValuesArray', [])
                if values:
                    vals = [x[1] for x in values if x[1] is not None]
                    if vals:
                        bb_charged = max(vals)
                        bb_now = vals[-1]
        except Exception:
            pass

        # 3. RHR
        rhr = "-"
        user_sum_data = None
        try:
            user_sum_data = garmin.get_user_summary(today)
            if user_sum_data and 'restingHeartRate' in user_sum_data:
                rhr = user_sum_data['restingHeartRate']
        except Exception:
            pass

        # 4. TRAINING READINESS
        readiness = "-"
        try:
            r_data = garmin.get_training_readiness(today)
            if r_data:
                if isinstance(r_data, list) and len(r_data) > 0:
                    readiness = r_data[0].get('score', '-')
                elif isinstance(r_data, dict):
                    if 'score' in r_data:
                        readiness = r_data['score']
                    elif 'trainingReadinessDynamicDTO' in r_data:
                        readiness = r_data['trainingReadinessDynamicDTO'].get('score')
        except Exception:
            pass

        if readiness == "-" and user_sum_data:
            try:
                if 'trainingReadinessDynamicDTO' in user_sum_data:
                    readiness = user_sum_data['trainingReadinessDynamicDTO'].get('score')
                elif 'trainingReadiness' in user_sum_data:
                    readiness = user_sum_data['trainingReadiness']
            except Exception:
                pass
            
        if readiness is None: readiness = "-"

        # 5. HRV (LAST NIGHT + AVERAGE)
        hrv_status, hrv_avg, hrv_last = "-", "-", "-"
        try:
            hrv_data = garmin.get_hrv_data(today)
            if hrv_data and 'hrvSummary' in hrv_data:
                summary = hrv_data['hrvSummary']
                hrv_status = summary.get('status', '-').title()
                hrv_avg = summary.get('weeklyAvg', '-')
                hrv_last = summary.get('lastNightAvg', '-')
        except Exception:
            pass

        # READINESS ADVICE
        advice = T['advice_ok']
        if isinstance(readiness, (int, float)):
            if readiness >= 80: advice = T['advice_go']
            elif readiness >= 50: advice = T['advice_ok']
            elif readiness >= 25: advice = T['advice_warn']
            else: advice = T['advice_stop']

        report = (
            f"{T['morning_title']} ({today})\n\n"
            f"{T['sleep']}\n"
            f"• Puntuación: *{sleep_score}* ({sleep_qual})\n"
            f"• {T['duration']}: *{format_duration_hm(sleep_secs)}* {sleep_range}\n\n"
            f"{T['body_batt']}\n"
            f"• {T['bb_max']}: *{bb_charged}* | {T['bb_now']}: *{bb_now}*\n\n"
            f"{T['heart']}\n"
            f"• {T['rhr']}: *{rhr} bpm*\n"
            f"• {T['hrv']}: *{hrv_last} ms* (Estado: {hrv_status} | Promed: {hrv_avg}ms)\n\n"
            f"{T['readiness']}\n"
            f"• Puntuación: *{readiness}/100*\n"
            f"👉 _{advice}_"
        )
        return report

    except Exception as e:
        if "MFA_REQUIRED" in str(e):
            return None
        logging.error(f"Error in morning report: {e}\n{traceback.format_exc()}")
        return T['err_morning']

# ==============================================================================
# MENU & RECENT ACTIVITIES LOGIC
# ==============================================================================

def get_activities_menu(chat_id=None):
    try:
        garmin = get_garmin_client(chat_id=chat_id)
        activities = garmin.get_activities(0, 5)
        if not activities:
            return T['err_not_found']

        lines = [T['menu_title'], ""]
        for idx, act in enumerate(activities):
            name = act.get('activityName', 'Actividad')
            dist = safe_round(act.get('distance', 0) / 1000, 2)
            date_str = act.get('startTimeLocal', '')[:10]
            lines.append(f"*{idx}* - {date_str} | *{name}* ({dist} km)")

        lines.append("")
        lines.append(T['menu_footer'])
        return "\n".join(lines)
    except Exception as e:
        if "MFA_REQUIRED" in str(e):
            return None
        logging.error(f"Error in activities menu: {e}")
        return T['err_menu']

# ==============================================================================
# MAIN TELEGRAM WEBHOOK ENTRYPOINT
# ==============================================================================

def telegram_webhook(request):
    """Entry point for Google Cloud Run / Functions Framework."""
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        if not chat_id or not text:
            return "OK", 200

        # ----------------------------------------------------------------------
        # COMMAND 1: /mfa 123456
        # ----------------------------------------------------------------------
        if text.lower().startswith("/mfa"):
            parts = text.split()
            if len(parts) == 2 and parts[1].isdigit():
                mfa_code = parts[1]
                send_telegram(chat_id, "⏳ Verificando código MFA con Garmin...")
                try:
                    get_garmin_client(chat_id=chat_id, mfa_code=mfa_code)
                    send_telegram(chat_id, T['mfa_success'])
                except Exception as e:
                    send_telegram(chat_id, f"❌ Error verificando MFA: {str(e)}")
            else:
                send_telegram(chat_id, T['mfa_invalid_format'])
            return "OK", 200

        # ----------------------------------------------------------------------
        # COMMAND 2: MORNING REPORT ('morning' / 'mañana')
        # ----------------------------------------------------------------------
        if text.lower() in ['morning', 'mañana', 'manana']:
            send_telegram(chat_id, T['loading_vital'])
            report = get_morning_report(chat_id=chat_id)
            if report:
                send_telegram(chat_id, report)
            return "OK", 200

        # ----------------------------------------------------------------------
        # COMMAND 3: ACTIVITIES LIST ('list' / 'lista')
        # ----------------------------------------------------------------------
        if text.lower() in ['list', 'lista']:
            send_telegram(chat_id, T['loading_hist'])
            menu = get_activities_menu(chat_id=chat_id)
            if menu:
                send_telegram(chat_id, menu)
            return "OK", 200

        # ----------------------------------------------------------------------
        # DEFAULT / HELP COMMAND
        # ----------------------------------------------------------------------
        if text == "/start" or text.lower() == "help":
            send_telegram(chat_id, T['help_msg'])
            return "OK", 200

        # Handle numeric input (0, 1, 2...) for activity selection
        if text.isdigit():
            send_telegram(chat_id, T['loading_1'])
            # Here you can hook in your full individual activity report function
            send_telegram(chat_id, f"Fetching details for activity index {text}...")
            return "OK", 200

        send_telegram(chat_id, T['help_msg'])
        return "OK", 200

    except Exception as e:
        logging.error(f"Error in webhook handler: {e}\n{traceback.format_exc()}")
        return "OK", 200
