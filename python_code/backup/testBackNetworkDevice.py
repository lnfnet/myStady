#!/usr/bin/env python
# -*- coding: utf-8 -*-
from netmiko import ConnectHandler
import time
import os

def Cisco(ip):
   #SSH登录名和密码
    cisco = {
       'device_type': 'cisco_ios',
       'ip': ip,
       'username': 'admin',
       'password': 'cisco',
       'port': 22,
       'secret': 'cisco', 
       'verbose': False, 
    }
   
   #添加设备地址。
    Address = [
   '192.168.88.111',
   '192.168.88.112'
    ]
   #添加设备名，要和上面的IP地址相对应。
    Name = [
   'OAN3K01',
   'PRON3K02'
    ]
   ID=Address.index(ip)
  
   
    print ('---------------正在连接网络设备：%s---------------\n' % Name[ID])
    net_connect = ConnectHandler(**cisco)
   net_connect.enable()
   #设置下发的命令。
    commands = [
       'show running-config',
   
    ]
    timestr = time.strftime('%Y_%m_%d', time.localtime())
    for cmd in commands:
      #E:\config要事先建立，要不然会报错。
       filename = 'E:\config\%s_%s.txt' % (Name[ID], timestr)
       save = open(filename, 'w')
       print ('正在下发配置命令：' + cmd)
       try:
           result = net_connect.send_command(cmd)
           save.write(result)
           print ('备份完成！\n')
       except ValueError:
           print('备份失败！')
           break
   net_connect.disconnect()


if __name__ == '__main__':
    #设备地址。
    ips = [
       '192.168.88.111',
      '192.168.88.112'
     
    ]
    for ip in ips:
      Cisco(ip)
   