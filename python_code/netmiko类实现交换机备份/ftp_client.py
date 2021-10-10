#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

from ftplib import FTP
import re
import os

def ftpconnect(host, username, password):
	ftp = FTP()
    
	ftp.connect(host, 21)
	ftp.login(username, password)
	return ftp

def uploadfile(ftp, localpath, remotepath):
	bufsize = 1024
	fp = open(localpath, 'rb')
	ftp.storbinary('STOR ' + remotepath, fp, bufsize)
	ftp.set_debuglevel(0)
	fp.close()
	
def filename():
        #获取指定路径下的所有文件将文件名存放到列表
	f1 = os.getcwd() + '/config/'
	f2 = os.listdir(f1)
	filename = []
	for i in f2:
        #正则找出所有结尾为txt的文件，然后添加到filename列表里
		if ''.join(re.findall('.tx(t$)',i)) == 't':
			filename.append(i)
	return filename

def main():
	# print ('正在连接服务器...')
	ftp = ftpconnect('192.168.31.254', 'config', 'config')
        #获取路径/root/python_code/config_script
	path1 = os.getcwd()
        #/root/python_code/config_script + '/config/'
	fullpath = path1 + '/config/'
	# print ('文件所在路径'+fullpath)
        #获取待上传的文件名
	fn = filename()
        #文件上传到ftp服务器后的文件名称，与源文件保持一致eg:123.txt
	fullremotepath = fn
	# print (fullremotepath)
        #本地路径需要加上路径+具体文件名eg:/root/python_code/config_script/123.txt
	fulllocalpath = []
	for i in fn:
		fulllocalpath.append(fullpath + i)
	for r in range(len(fulllocalpath)):
		for l in range(len(fulllocalpath)):
# '''
# 1，首先第一个for第一次循环第二个for也是第一次循环时r=0，l=0，r=l，此时p1和p2会被赋值,
# 2，然后第二个for循环的第二次循环r依然=0，l=1，p1和p2不会被赋值
# 3，当第一个for第二次循环时第二个for第一次循环r=1，l=0，p1和p2不会被赋值, 
# 4，第二个for的第二次循环r=1，l=1，此时p1和p2会被赋值
# '''
			if r == l:
				p1 = fulllocalpath[l]
				p2 = fullremotepath[r]
#得出的结果就是uploadfile(ftp, '/root/python_code/config_script/123.txt', '123.txt')
				uploadfile(ftp, p1, p2)
	print ('列出目标服务器文件列表：')
	ftp.dir()
	ftp.quit()

if __name__ == '__main__':
	main()