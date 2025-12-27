import os
import requests
import json
import schedule
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import webbrowser

app = Flask(__name__)

# Global configuration storage
config = {
    'api_key': '',
    'whatsapp_group_link': '',
    'is_running': False,
    'driver': None
}

class GroqAPI:
    """Python wrapper for Groq API (FREE & FAST)"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def simple_chat(self, user_message, system_message=None):
        """Simple chat helper"""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return None


def generate_hunger_message(time_slot):
    """Generate WhatsApp message using Groq API"""
    
    if not config['api_key']:
        return "⚠️ API Key not configured"
    
    system_prompt = """You are an AI message generator for an Indian Daily Hunger-Time WhatsApp Notification System.
Your task is to generate ONE short WhatsApp-friendly message for the given hunger time.

STRICT RULES:
1. Output MUST have EXACTLY 3 lines.
2. Each line MUST be separated by a single line break.
3. Do NOT add greetings, explanations, headers, or extra spacing.
4. Language must be simple, casual, and relatable to Indian users.
5. Tone should be funny, light, and friendly.

REQUIRED STRUCTURE:
Line 1: Funny hunger-related line (Indian context)
Line 2: Simple, practical health tip
Line 3: Soft chocolate mention (gentle, non-pushy)

Return ONLY the 3-line WhatsApp message. Nothing else."""
    
    groq = GroqAPI(config['api_key'])
    
    message = groq.simple_chat(
        user_message=f"Generate message for: {time_slot}",
        system_message=system_prompt
    )
    
    return message


def init_whatsapp_driver():
    """Initialize WhatsApp Web with Selenium"""
    try:
        print("🔧 Setting up ChromeDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--user-data-dir=./whatsapp_session")  # Save session
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add these to prevent crashes
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Automatically download and use correct ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        print("🌐 Opening Chrome browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("📱 Loading WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        print("✅ WhatsApp Web opened. Please scan QR code if needed.")
        print("⏳ Waiting for WhatsApp to load...")
        
        # Wait for WhatsApp to load (search box appears)
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
        )
        
        print("✅ WhatsApp Web loaded successfully!")
        return driver
        
    except Exception as e:
        print(f"❌ Error initializing WhatsApp: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Chrome browser is installed")
        print("   2. Close all Chrome windows and try again")
        print("   3. Run: pip install --upgrade webdriver-manager")
        return None


def send_to_whatsapp_group(message):
    """Send message to WhatsApp group using Selenium"""
    
    if not config['whatsapp_group_link']:
        print("⚠️ WhatsApp group link not configured")
        return False
    
    try:
        # Initialize driver if not exists
        if not config['driver']:
            config['driver'] = init_whatsapp_driver()
            if not config['driver']:
                return False
        
        driver = config['driver']
        
        print(f"📱 Opening WhatsApp group link...")
        
        # Open the group invite link
        driver.get(config['whatsapp_group_link'])
        time.sleep(3)
        
        # Click "Join Group" if needed (for first time)
        try:
            join_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Join group")]'))
            )
            join_button.click()
            time.sleep(2)
        except:
            pass  # Already in group
        
        # Find message input box
        message_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        
        # Type message
        message_box.click()
        time.sleep(1)
        
        # Split message by lines and send with Shift+Enter
        lines = message.split('\n')
        for i, line in enumerate(lines):
            message_box.send_keys(line)
            if i < len(lines) - 1:
                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        
        time.sleep(1)
        
        # Send message (Enter key)
        message_box.send_keys(Keys.ENTER)
        
        print("✅ Message sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending to WhatsApp: {e}")
        return False


def job_11_30():
    """Job for 11:30 AM"""
    message = generate_hunger_message("11:30 AM – Pre-Lunch Hunger")
    if message:
        send_to_whatsapp_group(message)


def job_16_30():
    """Job for 4:30 PM"""
    message = generate_hunger_message("4:30 PM – Evening Snack Time")
    if message:
        send_to_whatsapp_group(message)


def job_21_30():
    """Job for 9:30 PM"""
    message = generate_hunger_message("9:30 PM – Late Night Cravings")
    if message:
        send_to_whatsapp_group(message)


def run_scheduler():
    """Run the scheduler in background"""
    while config['is_running']:
        schedule.run_pending()
        time.sleep(30)


# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Group Scheduler - Groq AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 650px;
            width: 100%;
            padding: 40px;
        }
        h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .free-badge {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .form-group { margin-bottom: 25px; }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        input[type="text"], input[type="password"], textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 20px;
            margin-left: 10px;
        }
        .status-running { background: #d4edda; color: #155724; }
        .status-stopped { background: #f8d7da; color: #721c24; }
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #5a6268; }
        .btn-info { background: #17a2b8; color: white; }
        .btn-info:hover { background: #138496; }
        .schedule-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
        }
        .schedule-info h3 { color: #333; margin-bottom: 15px; font-size: 18px; }
        .schedule-item {
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .schedule-item:last-child { border-bottom: none; }
        .time { font-weight: 600; color: #667eea; }
        .alert {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        .info-box {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .info-box h4 { margin-bottom: 10px; }
        .info-box ul { margin-left: 20px; }
        .info-box li { margin: 5px 0; }
        .setup-steps {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .setup-steps h4 { margin-bottom: 15px; font-size: 18px; }
        .setup-steps ol { margin-left: 20px; }
        .setup-steps li { margin: 10px 0; line-height: 1.6; }
        .setup-steps a { color: #fff; text-decoration: underline; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <span class="free-badge">✨ 100% FREE - GROUP SUPPORT! ✨</span>
        
        <h1>🍫 WhatsApp Group Scheduler</h1>
        <p class="subtitle">Send automated messages to WhatsApp groups with Groq AI</p>
        
        {% if status_message %}
        <div class="alert alert-success">{{ status_message }}</div>
        {% endif %}
        
        <div class="setup-steps">
            <h4>📋 How to Get Group Invite Link:</h4>
            <ol>
                <li>Open your WhatsApp group</li>
                <li>Tap group name at top</li>
                <li>Tap "Invite via link"</li>
                <li>Tap "Copy link"</li>
                <li>Paste below! ⬇️</li>
            </ol>
        </div>
        
        <span class="status-badge {% if is_running %}status-running{% else %}status-stopped{% endif %}">
            {% if is_running %}🟢 Running{% else %}🔴 Stopped{% endif %}
        </span>
        
        <form method="POST" action="/save-config">
            <div class="form-group">
                <label for="api_key">🔑 Groq API Key (FREE)</label>
                <input type="password" id="api_key" name="api_key" 
                       placeholder="gsk_..." 
                       value="{{ api_key }}" required>
                <small style="color: #666;">Get FREE key: <a href="https://console.groq.com/keys" target="_blank">console.groq.com/keys</a></small>
            </div>
            
            <div class="form-group">
                <label for="whatsapp_group_link">📱 WhatsApp Group Invite Link</label>
                <textarea id="whatsapp_group_link" name="whatsapp_group_link" 
                       rows="3"
                       placeholder="https://chat.whatsapp.com/xxxxxxxxxx" 
                       required>{{ whatsapp_group_link }}</textarea>
                <small style="color: #666;">Paste the complete group invite link</small>
            </div>
            
            <button type="submit" class="btn btn-primary">💾 Save Configuration</button>
        </form>
        
        <div class="button-group">
            <form method="POST" action="/init-whatsapp" style="display: inline;">
                <button type="submit" class="btn btn-info">🌐 Initialize WhatsApp</button>
            </form>
            
            {% if not is_running %}
            <form method="POST" action="/start" style="display: inline;">
                <button type="submit" class="btn btn-success">▶️ Start Scheduler</button>
            </form>
            {% else %}
            <form method="POST" action="/stop" style="display: inline;">
                <button type="submit" class="btn btn-danger">⏸️ Stop Scheduler</button>
            </form>
            {% endif %}
            
            <form method="POST" action="/test" style="display: inline;">
                <button type="submit" class="btn btn-secondary">🧪 Send Test</button>
            </form>
        </div>
        
        <div class="schedule-info">
            <h3>📅 Daily Schedule</h3>
            <div class="schedule-item">
                <span class="time">11:30 AM</span> - Pre-Lunch Hunger
            </div>
            <div class="schedule-item">
                <span class="time">4:30 PM</span> - Evening Snack
            </div>
            <div class="schedule-item">
                <span class="time">9:30 PM</span> - Late Night
            </div>
        </div>
        
        <div class="info-box">
            <h4>⚠️ Important Setup Steps:</h4>
            <ul>
                <li><strong>Click "Initialize WhatsApp" first</strong> - Scan QR if needed</li>
                <li><strong>Keep Chrome open</strong> - Don't close the browser</li>
                <li><strong>Stay logged in</strong> - Session will be saved</li>
                <li><strong>Test first</strong> - Click "Send Test" before starting</li>
            </ul>
        </div>
        
        <div class="alert alert-info" style="margin-top: 20px;">
            <strong>💡 Tip:</strong> Click "Initialize WhatsApp" once. After that, you only need to click "Start Scheduler". The browser will stay open automatically!
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        api_key=config['api_key'],
        whatsapp_group_link=config['whatsapp_group_link'],
        is_running=config['is_running'],
        status_message=request.args.get('message')
    )


@app.route('/save-config', methods=['POST'])
def save_config():
    config['api_key'] = request.form.get('api_key', '')
    config['whatsapp_group_link'] = request.form.get('whatsapp_group_link', '').strip()
    return redirect(url_for('index', message='✅ Configuration saved!'))


@app.route('/init-whatsapp', methods=['POST'])
def initialize_whatsapp():
    if config['driver']:
        return redirect(url_for('index', message='⚠️ WhatsApp already initialized!'))
    
    config['driver'] = init_whatsapp_driver()
    
    if config['driver']:
        return redirect(url_for('index', message='✅ WhatsApp initialized! Scan QR if needed, then click "Send Test".'))
    else:
        return redirect(url_for('index', message='❌ Failed to initialize WhatsApp. Install ChromeDriver.'))


@app.route('/start', methods=['POST'])
def start_scheduler():
    if not config['api_key'] or not config['whatsapp_group_link']:
        return redirect(url_for('index', message='⚠️ Please configure both API key and group link!'))
    
    if not config['driver']:
        return redirect(url_for('index', message='⚠️ Please click "Initialize WhatsApp" first!'))
    
    config['is_running'] = True
    
    schedule.clear()
    schedule.every().day.at("11:30").do(job_11_30)
    schedule.every().day.at("16:30").do(job_16_30)
    schedule.every().day.at("21:30").do(job_21_30)
    
    thread = Thread(target=run_scheduler, daemon=True)
    thread.start()
    
    return redirect(url_for('index', message='✅ Scheduler started! Messages will be sent automatically.'))


@app.route('/stop', methods=['POST'])
def stop_scheduler():
    config['is_running'] = False
    schedule.clear()
    return redirect(url_for('index', message='⏸️ Scheduler stopped.'))


@app.route('/test', methods=['POST'])
def test_message():
    if not config['api_key']:
        return redirect(url_for('index', message='⚠️ Configure API key first!'))
    
    if not config['whatsapp_group_link']:
        return redirect(url_for('index', message='⚠️ Configure group link first!'))
    
    if not config['driver']:
        return redirect(url_for('index', message='⚠️ Click "Initialize WhatsApp" first!'))
    
    message = generate_hunger_message("4:30 PM – Evening Snack Time")
    if message:
        success = send_to_whatsapp_group(message)
        if success:
            return redirect(url_for('index', message='✅ Test message sent to group!'))
        else:
            return redirect(url_for('index', message='❌ Failed to send. Check if you are in the group.'))
    else:
        return redirect(url_for('index', message='❌ Failed to generate message. Check API key.'))


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 WhatsApp GROUP Scheduler - Groq AI (FREE)")
    print("=" * 70)
    print("✨ NEW: Now supports WhatsApp Group Invite Links!")
    print()
    print("📱 Setup:")
    print("   1. Install: pip install selenium requests flask schedule")
    print("   2. Install ChromeDriver: https://chromedriver.chromium.org/")
    print("   3. Get group invite link from WhatsApp")
    print("   4. Open: http://localhost:5000")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Click 'Initialize WhatsApp' and scan QR code")
    print("   - Keep Chrome browser open")
    print("   - Test before starting scheduler")
    print("=" * 70)
    print()
    app.run(debug=True, port=5000, use_reloader=False)