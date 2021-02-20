
# easy-mornings-server

## setup pi

1) flash sd card

2) write wpa_supplicant.conf
3) write ssh

4) power up
5) ssh pi@raspberrypi.local

6) change password

## install

```
apt install pigpio
sudo pigpiod
sudo echo "sudo pigpiod" >> /etc/rc.local

apt install python3-pip
apt install git

pip3 install git+https://github.com/samtherussell/easy-mornings-server.git

wget https://raw.githubusercontent.com/samtherussell/easy-mornings-server/main/easy-mornings-server.service
sudo cp easy-mornings-server.service /etc/systemd/system/
sudo systemctl enable easy-mornings-server.service
sudo systemctl start easy-mornings-server
```