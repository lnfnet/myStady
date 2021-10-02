# _*_ coding:utf-8 _*_

"""

__title__ = '网络设备配置文件备份'

__author__ = 'Lucky'

__date__ = '2018/08/23'

"""

from logging import warning

from time import sleep,strftime,localtime

from os import mkdir

import telnetlib

import paramiko

class Telnet_Client:

'''初始化登录参数,以及实例化telnet和ssh类'''

def __init__(self,host_ip,username,password,port):

self.telnet = telnetlib.Telnet()

self.ssh = paramiko.SSHClient()

self.host_ip = host_ip

self.username = username

self.password = password

self.port = port

def login_ssh_host(self):

'''自动添加策略,保存服务器的主机名和公钥信息'''

self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:

self.ssh.connect(self.host_ip,self.port,self.username,self.password,timeout=8)

print("\nssh(%s)连接成功." %self.host_ip)

return True

except:

warning("\n网络(%s)连接失败!" %self.host_ip)

input_string = input("\n请检查网络(%s)是否畅通[ssh]" %self.host_ip)

return False

def login_telnet_host(self):

'''可能有些机器远程连接会连不上,这里做异常捕获'''

try:

self.telnet.open(self.host_ip,self.port,timeout=10)

except:

warning("\n网络(%s)连接失败!" %self.host_ip)

input_string = input("\n请检查网络(%s)是否畅通[telnet]" % self.host_ip + "\n")

return False

else:

'''

这里用read_until方法进行匹配登录字符是否为login,是的话输入用户名,最多等待10秒

这里在强调一下telnet需要传入的内容为bytes,所以需要encode一下

'''

self.telnet.read_until(b'Username: ',timeout=10)

self.telnet.write(self.username.encode('ascii') + b'\n')

# 等待Password出现后输入密码，最多等待10秒

self.telnet.read_until(b'Password: ',timeout=10)

self.telnet.write(self.password.encode('ascii') + b'\n')

# 等待1秒给设备一个缓冲时间

sleep(1)

# read_very_eager()获取上次程序执行的结果

last_command_result = self.telnet.read_very_eager().decode('ascii')

# 判断上次结果是否有登录错误的

if 'Login incorrect' not in last_command_result:

print('\ntelnet(%s)登录成功.' %self.host_ip)

return True

else:

warning('\n登录(%s)失败，用户名或密码错误!' %self.host_ip)

return False

# 执行telnet命令

def execute_some_command(self,

command_telnet_user,

command_telnet_password,

command_telnet_copy_to_ftp,

command_telnet_to_ftp_1,

command_telnet_to_ftp_2,

command_telnet_to_ftp_3):

str_time = strftime("%Y%m%d", localtime())

backup_cfg = self.host_ip + "_" + str_time + ".txt"

# 执行传入的命令,这里也需要将传入的命令进行encode处理

self.telnet.write(command_telnet_user.encode('ascii') + b'\n')

self.telnet.write(command_telnet_password.encode('ascii'))

self.telnet.write(command_telnet_copy_to_ftp.encode('ascii'))

self.telnet.write(command_telnet_to_ftp_1.encode('ascii'))

self.telnet.write(command_telnet_to_ftp_2.encode('ascii'))

try:

self.telnet.write(backup_cfg.encode('ascii') + command_telnet_to_ftp_3.encode('ascii'))

except Exception as e:

print("telnet(%s)备份网络配置文件失败!" %self.host_ip)

else:

print("\ntelnet登录(%s)后网络配置文件备份成功." %self.host_ip)

# 等待1秒给设备一个缓冲时间

sleep(1)

# 获取命令执行结果

# exec_command_result = self.telnet.read_very_eager().decode('ascii')

# print(exec_command_result)

# 执行ssh命令

def execute_ssh_command(self,command):

stdin, stdout, stderr = self.ssh.exec_command(command)

# 等待1秒给设备一个缓冲时间

sleep(1)

result = stdout.readlines()

str_time = strftime("%Y%m%d", localtime())

# mkdir(str_time)

with open(str_time + "\\" + self.host_ip + "_" + str_time + ".txt","w",encoding="utf-8") as result_ssh_obj:

for line in result:

try:

result_ssh_obj.write(line.strip() + "\n")

except Exception as e:

print("备份(%s)设备上的网络配置文件失败,错误代码为:%s" %(self.host_ip,e))

else:

print("\nssh登录(%s)后网络配置文件备份成功." %self.host_ip)

# 退出telnet函数

def logout_telnet(self):

self.telnet.write(b"exit\n")

# 退出ssh函数

def logout_ssh(self):

self.ssh.close()

def main():

str_time = strftime("%Y%m%d", localtime())

mkdir(str_time)

command_telnet_user = "enable\n"

command_telnet_password = "123456\n"

command_telnet_copy_to_ftp = "copy run tftp://192.168.2.2\n"

command_telnet_to_ftp_1 = "\n"

command_telnet_to_ftp_2 = "\n"

command_telnet_to_ftp_3 = "\n"

command_ssh = "show run"

# ssh和telnet调用过程

with open('ssh_host.txt', 'r', encoding='utf-8') as ssh_obj, \

open('telnet_host.txt', 'r', encoding='utf-8') as telnet_obj:

for ssh_ip in ssh_obj:

# 根据类实例化一个ssh对象

ssh_client = Telnet_Client(ssh_ip.strip(), 'admin', '123456', '22')

# 根据函数的返回值进行判断是否继续执行别的函数

if ssh_client.login_ssh_host():

ssh_client.execute_ssh_command(command_ssh)

ssh_client.logout_ssh()

for ip in telnet_obj:

# 根据类实例化一个telnet对象

telnet_client = Telnet_Client(ip.strip(), 'admin', '123456', '23')

# 根据函数的返回值进行判断是否继续执行别的函数

if telnet_client.login_telnet_host():

telnet_client.execute_some_command(command_telnet_user,

command_telnet_password,

command_telnet_copy_to_ftp,

command_telnet_to_ftp_1,

command_telnet_to_ftp_2,

command_telnet_to_ftp_3)

telnet_client.logout_telnet()

if __name__ == '__main__':

main()
