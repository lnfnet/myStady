#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
import paramiko
import os, sys
import json
import time
import telnetlib
 
 
def sshconfig(ip, port, username, password, cmd, PS1, isNeedEnableMode, enablePassword):
    # 实例化SSHClient
    client = paramiko.SSHClient()
    # 自动添加策略，保存服务器的主机名和密钥信息
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接SSH服务端，以用户名和密码进行认证
    client.connect(hostname=ip, username=username, password=password, look_for_keys=False)
    chan = client.invoke_shell()
    chan.settimeout(9000)
 
    # 获取登陆后的消息
    welcomeinfo = ''
    while True:
        line = chan.recv(4096)
        welcomeinfo += line
        if (PS1 is not None) & (len(PS1) > 0):
            isFindPS1 = False;
            for i in range(len(PS1)):
                if PS1[i] in line:
                    isFindPS1 = True
            if isFindPS1 == True:
                break;
    print welcomeinfo
 
    if isNeedEnableMode == "1":
        chan.send('enable' + '\n')
        chan.send(enablePassword + '\n')
        # 获取特权后的消息
        enableInfo = ''
        while True:
            line = chan.recv(4096)
            enableInfo += line
            if (PS1 is not None) & (len(PS1) > 0):
                isFindPS1 = False;
                for i in range(len(PS1)):
                    if PS1[i] in line:
                        isFindPS1 = True
                if isFindPS1 == True:
                    break;
        print enableInfo
 
    chan.send(cmd + '\n')
    result = ''
    # more交互处理
    more = '-- More --'
    more2 = '--More--'
    more3 = '<--- More --->'
    more4 = '-- More --'
    #  循环获取数据
    while True:
        line = chan.recv(4096)
        result += line
        if (more in line) | (more2 in line) | (more3 in line) | (more4 in line):
            chan.send(" ")
            continue;
        if (PS1 is not None) & (len(PS1) > 0):
            isFindPS1 = False;
            for i in range(len(PS1)):
                if PS1[i] in line:
                    isFindPS1 = True
            if isFindPS1 == True:
                break;
 
    print result
    return result
 
def telnetconfig(ip, port, username, password, cmd, PS1, isNeedEnableMode, enablePassword):
    # 连接Telnet服务器
    tn = telnetlib.Telnet(ip, port=23, timeout=10)
    tn.set_debuglevel(2)
    # 处理登录
    # 输入登录用户名
    tn.read_until('Username:')
    tn.write(username.encode('ascii') + '\n')
 
    # 输入登录密码
    tn.read_until('Password:')
    tn.write(password.encode('ascii') + '\n')
 
    time.sleep(2)
 
    # 获取登陆后的消息
    welcomeinfo = ""
    while True:
        line = tn.read_very_eager().encode("ascii")
        welcomeinfo += line
        if (PS1 is not None) & (len(PS1) > 0):
            isFindPS1 = False;
            for i in range(len(PS1)):
                if PS1[i] in line:
                    isFindPS1 = True
            if isFindPS1 == True:
                break;
    print welcomeinfo
 
    #处理特权密码
    if isNeedEnableMode == "1":
        tn.write('enable'.encode('ascii') + '\n')
        tn.write(enablePassword.encode('ascii') + '\n')
        time.sleep(2)
        # 获取特权后的消息
        enableInfo = ''
        while True:
            line = tn.read_very_eager().encode("ascii")
            enableInfo += line
            if (PS1 is not None) & (len(PS1) > 0):
                isFindPS1 = False;
                for i in range(len(PS1)):
                    if PS1[i] in line:
                        isFindPS1 = True
                if isFindPS1 == True:
                    break;
        print enableInfo
 
    tn.write(cmd.encode('ascii') + '\n')
    time.sleep(2)
    result = ''
    # more交互处理
    more = '-- More --'
    more2 = '--More--'
    more3 = '<--- More --->'
    more4 = '-- More --'
    #  循环获取数据
    while True:
        line = tn.read_very_eager().encode("ascii")
        result += line
        if (more in line) | (more2 in line) | (more3 in line) | (more4 in line):
            tn.write(" ".encode('ascii') )
            time.sleep(2)
            continue;
        if (PS1 is not None) & (len(PS1) > 0):
            isFindPS1 = False;
            for i in range(len(PS1)):
                if PS1[i] in line:
                    isFindPS1 = True
            if isFindPS1 == True:
                break;
 
    print result
    return result
 
    tn.close()  # tn.write('exit\n')
    return "aaa"
 
def main():
    file = open("SwitchConfig.json", "rb")
    fileJson = json.load(file)
    switch = fileJson["switch"]
    # print switch
    for i in range(len(switch)):
        print switch[i]
        if switch[i]["protocol"] == "ssh":
            result = sshconfig(switch[i]["ip"], switch[i]["port"], switch[i]["username"], switch[i]["password"],
                               switch[i]["cmd"], switch[i]["PS1"], switch[i]["isNeedEnableMode"],
                               switch[i]["enablePassword"])
            fileName = switch[i]["fileName"]
            fileObject = open(fileName, 'w')
            fileObject.write(result)
            fileObject.close()
        if switch[i]["protocol"] == "telnet":
            result = telnetconfig(switch[i]["ip"], switch[i]["port"], switch[i]["username"], switch[i]["password"],
                               switch[i]["cmd"], switch[i]["PS1"], switch[i]["isNeedEnableMode"],
                               switch[i]["enablePassword"])
            fileName = switch[i]["fileName"]
            fileObject = open(fileName, 'w')
            fileObject.write(result)
 
    sys.exit(0)
 
 
if __name__ == '__main__':
    main()