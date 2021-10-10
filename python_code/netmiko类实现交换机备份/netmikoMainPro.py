#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

from netmiko import ConnectHandler
from ftp_client import main     #导入ftp上传模块
import os
import time
import re

def Cisco(ip):
	#cisco swith_config export function
	cisco_881 = {
	'device_type': 'cisco_ios',
	'ip': ip,
	'username': 'cisco',
	'password': 'cisco',
	'port': '22',
	'secret': 'cisco',
	'verbose': False,
	}
'''思科设备的username cisco privilege 15 password cisco,privilege 15权限为
最大可以执行的命令越多
'''
print(u'正在连接Devices：{0}\n'.format(ip))
net_connect = ConnectHandler(**cisco_881)
net_connect.enable()

timestr = time.strftime('%Y-%m-%d', time.localtime(time.time()))

for cmds in open('commands', 'r'):
	cmd = cmds.replace('\n',' ')
	filename = (u'{0}_{1}_{2}.txt'.format(ip,cmd.replace(' ','_').replace('/','-'), timestr))
	save = open('/root/python_code/config_scrtpt/config/' + filename, 'w')
	print (u'正在执行命令：\n' + cmds)
	result = net_connect.send_command(cmds)
	time.sleep(1)
	save.write(result)
	print(u'命令执行完毕，结果保存于当前目录{0}中!\n'.format(filename))
	save.close()
	net_connect.disconnect()

if __name__ == '__main__':
	for ips in open('ips','r'):
		ip = ips.replace('\n','')
		try:
			Cisco(ip)
		except Exception as e:
			print ('连接超时! ',e)
			pass
		time.sleep(1)
	print (u'=====上传文件至目标服务器=====')
	main()   #ftp上传主程序
	print (u'\n文件上传成功!')