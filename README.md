# Requirements:

Dnsdist (v2 and above only) - Docker - Python3 - Nginx (Optional)

# Notes:

1- Replace The v2ray outbound in config.json file with your v2ray outbound configuration. <br>
2- Install App Requirements in app directory. <br>
3- Path for sni dashboard is http://IP_ADDR:5000/sni-admin if you dont use NGINX. <br>
4- Stop the systemd-resolved.service <br>
5- Must enter an ip address or range in the whitelisted IPs in CIDR notation! 0.0.0.0/0 For everyone<br> 
6- the script only works for UBUNTU 24.04 LTS to install packages. and will disable nginx dnsdist & systemd-resolved. <br> 



# Environment Variables:

- Replace SNI_HOST_IP   in .env file inside root dir.
- Replace SNI_HOST_IP   in app directory .env file.
- Replace USE_NGINX     in app directory .env file if you use nginx as reverse proxy -> 1 else 0
- Replace PASSWORD      in app directory .env file for your sni-admin dashboard.

# Setup

```bash
git clone https://github.com/AmHoTa/sni-proxy-v2ray /root/sni-proxy
cd /root/sni-proxy
nohup python3 app/app.py > /dev/null &
docker network create --subnet 192.168.25.0/24 --gateway 192.168.25.254 sninet
docker compose build
docker compose up
```


Big Thanks to ShervinAMD for his work.
