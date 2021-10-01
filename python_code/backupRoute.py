#! /usr/bin/env python3

from netmiko import ConnectHandler #导入库

import os

import time

def cisco_ios (ip,username,password,secret): #定义cisco_ios函数

    cisco = {
        "device_type":"cisco_ios", #设备类型为“cisco_ios”

        "ip":ip, #传入ip参数

        "username":username, #传入登陆用户名

        "password":password, #传入登陆密码

        "secret":secret #传入sceret密码

    }
command = ["show run"] #执行show run 命令。此列表可以加入多条命令

connect = ConnectHandler(**cisco) #对不同品牌设备的预定义的内容。这个地方建议看一下源码，我这一句话解释不太清楚。

full_config = ""

for cmd in command:

    config = connect.send_command(cmd)

    full_config += config

return full_config

connect.disconnect()

now = time.strftime("%Y-%m-%d", time.localtime()) #定义时间格式，备份文件名用到

if __name__ == "__main__":

host = ["10.163.4.39","10.163.0.126","10.163.1.253","10.163.1.254","10.163.1.133","10.163.1.134","10.163.1.135","10.163.1.129","10.163.1.130","10.163.1.131","10.16

3.1.132"] #需要备份的ip地址放入列表中

for ip in host: #循环列表，保存配置

conf = cisco_ios(ip, "admin", "admin123", "admin123")

with open(f"/root/backup/beijing/{ip}/cfg_bak_{ip}_{now}.txt", mode="a") as f1:

f1.write(conf) #保存到文件中

time.sleep(30) #每个IP之间等待30秒，给系统点反应时间