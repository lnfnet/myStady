import telnetlib
import time
import re
import getpass

username = input('请输入你的账号：')
passwd = getpass.getpass('请输入你的账号密码：')
commands = ['term len 0',
            'show run',
            'show mac add','show cdp nei']
timestr1 = time.strftime('%Y-%m-%d %X', time.localtime())
timestr = time.strftime('%Y-%m-%d', time.localtime())


def main(host):
    tn = telnetlib.Telnet(host, port=23, timeout=3)
    time.sleep(2)
    #tn.set_debuglevel(2)
    tn.read_until(b"Username:", timeout=3)
    tn.write(username.encode('ascii') + b'\n')

    tn.read_until(b"Password:")
    tn.write(passwd.encode('ascii') + b'\n')
    print('己成功登录%s [%s]' % (host, timestr1))
    time.sleep(0.5)
    tn.read_until(b"#")

    hostname_command = 'show run | in hostname'
    tn.write(hostname_command.encode('ascii') + b'\n')
    time.sleep(1)
    cmd_text = tn.read_very_eager().decode('ascii')
    match = re.split(' ', cmd_text)
    match1 = match[-1].replace('\n', ' ').replace('\r', '').replace('#', '')
    hostlist = re.split(' ', match1)
    hostname = hostlist[1]
    print(hostname)
    command_result = tn.read_very_eager().decode('ascii')
    filepath = 'D:\\SWbackup\\log\\'
    filename = ('%s %s %s' % (host, hostname, timestr))
    print(filename)
    save = open(filepath + filename + '.txt', 'a', newline='')  # 以写的方式来打开文件
    print(command_result, file=save)
    tn.close()


def do_work(host_list, all_num):
    num = 0
    for host in host_list:
        try:
            main(host)
            num += 1
            print("\r备份进度为：%.2f %%" % (num * 100 / all_num), end="")
            print('')
            print("-" * 50)
        except:
            f2 = open(r'D:\SWbackup\error.txt', 'a+')
            print('Can not connect to Device')
            print('%s is error' % host, file=f2)
            print('*' * 20 + '%s' % timestr1 + '*' * 20, file=f2)
            num += 1
            print("\r备份进度为：%.2f %%" % (num * 100 / all_num), end="")
            print('')
            print("-" * 50)
            f2.close()


host_list = []
f1 = open(r'D:\SWbackup\sw_telnet.txt', 'r')  # 获取文件中的每行IP
for line in f1.readlines():
    line = line.replace('\n', '')
    host_list.append(line)
f1.close
print(host_list)

all_num = len(host_list)

do_work(host_list, all_num)