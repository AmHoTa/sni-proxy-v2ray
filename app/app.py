from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import re
from pathlib import Path
import subprocess
import os
from dotenv import load_dotenv, dotenv_values

# =====================================================================
# Configuration
# =====================================================================

load_dotenv()
print(dotenv_values())


SNI_HOST_IP = dotenv_values()['SNI_HOST_IP']
USE_NGINX = dotenv_values()['USE_NGINX']
PASSWORD = dotenv_values()['PASSWORD']
DNSDIST_CONFIG_PATH = "/etc/dnsdist/dnsdist.conf"
DNSMASQ_CONFIG_PATH = "/root/sni-proxy/dnsmasq.conf"
SECRET_LOGIN_PATH = "/dns-admin/"
DNSDIST_WEB_IP = "127.0.0.1" if int(USE_NGINX) else "0.0.0.0"
FLASK_IP = "127.0.0.1" if int(USE_NGINX) else "0.0.0.0"
print(bool(USE_NGINX))

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_A_SECURE_RANDOM_KEY"

# Hidden login URL (change to anything you want)

subnets = []
domains = []

# =====================================================================
# Authentication Helpers
# =====================================================================

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(SECRET_LOGIN_PATH)
        return f(*args, **kwargs)
    return wrapper


@app.route(SECRET_LOGIN_PATH, methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        if request.form.get("password") == PASSWORD:
            session["authenticated"] = True
            return redirect(url_for('index'))
        else:
            error = "Invalid password."

    return f"""
    <html>
      <body style="font-family: Arial; padding: 20px;">
        <h2>Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Password"
                   style="padding: 8px; width: 220px;"/>
            <button type="submit" style="padding: 8px 20px;">Login</button>
        </form>
        <p style="color:red;">{error if error else ""}</p>
      </body>
    </html>
    """


@app.route('/logout')
def logout():
    session.clear()
    return redirect(SECRET_LOGIN_PATH)

# =====================================================================
# Application Routes (Protected)
# =====================================================================

@app.route('/', methods=['GET'])
@login_required
def index():

    global subnets, domains

    if not Path(DNSDIST_CONFIG_PATH).exists():
        raise FileNotFoundError(f"{DNSDIST_CONFIG_PATH} File Does Not Exist!")

    with open(DNSDIST_CONFIG_PATH, "r") as dnsdist_config:
        lines = dnsdist_config.readlines()

        proxy_str = ""
        flag_proxy = False

        for line in lines:
            if "subnets" in line:
                flag_proxy = True
            if flag_proxy and re.match(r'[a-z]', line) is None:
                proxy_str += line
            if "}" in line:
                flag_proxy = False

        subnets = re.findall(r'"([^"]*)"', proxy_str)

    with open(DNSMASQ_CONFIG_PATH, "r") as dnsmasq_config:
        domains = []
        lines = dnsmasq_config.readlines()
        for line in lines:
            domain = re.findall(r'address=/([^/]+)/\{SNI_HOST_IP\}', line)
            if domain:
                domains += domain

    command = subprocess.run("docker ps", shell=True, text=True, capture_output=True)

    return render_template(
        'index.html',
        left_text="\n".join(subnets),
        right_text="\n".join(domains),
        health_status=command.stdout
    )


@app.route('/submit_left', methods=['POST'])
@login_required
def submit_left():
    global domains, subnets

    submitted_text = request.form.get('left_textarea', '')
    subnets = [line.strip() for line in submitted_text.strip().split('\n') if line.strip()]

    conf = "local subnets = {\n"
    for subnet in subnets:
        conf += '"' + subnet + '",\n'
    conf += "}\n"


    default = f"""
setLocal('0.0.0.0:53')
setACL('0.0.0.0/0')

webserver('{DNSDIST_WEB_IP}:5353')
setWebserverConfig({{password="{PASSWORD}", apiKey="{PASSWORD}", acl="0.0.0.0/0"}})

newServer({{address = '{SNI_HOST_IP}:530', pool='sniproxy'}})
addAction(NetmaskGroupRule(subnets), PoolAction("sniproxy"))

"""
    conf += default

    with open(DNSDIST_CONFIG_PATH + "-temp", "w") as temp:
        temp.writelines(conf)

    command = subprocess.run(
        f"dnsdist --check-config -C {DNSDIST_CONFIG_PATH}-temp",
        shell=True, text=True, capture_output=True
    )

    if re.match(f"Configuration {DNSDIST_CONFIG_PATH}-temp OK!", command.stdout):
        os.remove(f"{DNSDIST_CONFIG_PATH}-temp")

    with open(DNSDIST_CONFIG_PATH, "w") as config:
        config.writelines(conf)

    subprocess.run("systemctl restart dnsdist", shell=True, text=True)

    domains = []
    subnets = []

    return redirect(url_for('index'))


@app.route('/submit_right', methods=['POST'])
@login_required
def submit_right():
    global domains, subnets

    submitted_text = request.form.get('right_textarea', '')
    domains = [line.strip() for line in submitted_text.strip().split('\n') if line.strip()]

    conf = """
bind-dynamic
bogus-priv
domain-needed
log-queries
log-facility=-
local-ttl=60
server={DNS_PROXY_IP}
"""
    
    for domain in domains:
        conf += f"address=/{domain}/{{SNI_HOST_IP}}\n"

    with open(DNSMASQ_CONFIG_PATH, "w") as config:
        config.writelines(conf)

    subprocess.run("docker restart sni", text=True, shell=True)

    domains = []
    subnets = []

    return redirect(url_for('index'))


# =====================================================================
# Start Application
# =====================================================================

if __name__ == '__main__':
    app.run(debug=True, host=f"{FLASK_IP}")

