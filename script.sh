# Install Dnsdist

echo \
"deb [signed-by=/etc/apt/keyrings/dnsdist-20-pub.asc] http://repo.powerdns.com/ubuntu noble-dnsdist-20 main" > /etc/apt/sources.list.d/pdns.list

echo \
"Package: dnsdist* 
Pin: origin repo.powerdns.com 
Pin-Priority: 600" > /etc/apt/preferences.d/dnsdist-20

install -d /etc/apt/keyrings; curl https://repo.powerdns.com/FD380FBB-pub.asc | sudo tee /etc/apt/keyrings/dnsdist-20-pub.asc

apt update
apt install dnsdist -y

# Install Python

apt install python3 python3-flask python3-dotenv


# Install Docker
apt update
apt install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc


tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt update
apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# Install Nginx

apt install curl gnupg2 ca-certificates lsb-release ubuntu-keyring

curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
    | tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
https://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
    | tee /etc/apt/sources.list.d/nginx.list	

apt update
apt install nginx 



systemctl disable --now systemd-resolved dnsdist nginx
