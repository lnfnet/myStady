#backup.py
import time
from telnetlib import Telnet

def tel(addr,user,pwd,secret):
        tn = Telnet(addr)
        tn.write(user+'\n')
        tn.write(pwd+'\n')
        tn.write('enable\n')
        tn.write(secret+'\n')
        tn.write('terminal length 0\n')#将show run的内容一次性全部显示完
        time.sleep(1)
        tn.write('show run\n')
        time.sleep(1)
        rsp = tn.expect([],timeout=1)[2]  
        return rsp

if __name__ == "__main__":
        fp = open('./ip.txt','r')
        for ip in fp:
          print("backing up "+ip.strip())
          conf = tel(ip.strip(),'cisco','cisco','cisco') #第一个cisco 是账户，第二个Cisco是密码，第三个Cisco是enable密码
          print(ip.strip()+' was finished!')
          print(conf)#这里是用于查看函数返回的内容，可以删除
          fw = open(ip.strip(),'w')#每台主机的配置以IP地址为文件名，建议先使用OS模块创建一个目录，然后将所有配置放到目录下
          fw.write(conf)
          fw.close()
        print('done!')
        fp.close()

