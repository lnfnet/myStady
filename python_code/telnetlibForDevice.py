import logging
import telnetlib
import time
'''
python 库 telnetlib: Telnet客户端:
telnetlib模块提供的Telnet类实现了Telnet协议。它为协议字符和telnet选项提供符号常量，符号常量来源于arpa/telnet.h去掉了前缀TELOPT_
1.Telnet.read_all(): 读取所有数据直到EOF，阻塞直到连接关闭
2.Telnet.read_some(): 读取至少一个字节的数据，除非EOF。如果没有数据则阻塞。
3.Telnet.read_until(expected[, timeout]):常用于登录，与write连用； 读取直到遇到了给定的字符串    expected或超时秒数
4.Telnet.read_very_eager(): 非阻塞地读取。连接关闭或者没有数据时触发EOFError异常，返回b''如果没有数据。 获取命令执行结果：获取的内容是上次获取之后本次获取之前的所有输入输出
5.Telnet.read_eager(): 读取已有数据(快)
6.Telnet.read_lazy(): 读取已有数据(懒)
7.Telnet.read_sb_data(): 返回的SB/SE pair(suboption begin/end)之间的数据，此方法永远不会阻塞
8.Telnet.open(host[,port[,timeout]]): 连接到主机，可选的第二个参数是默认为标准的Telnet端口（23）的端口号。
                                      可选的超时参数（以秒指定）阻塞操作（如连接尝试超时（如果不指定，默认使用全局超时设置））
9.Telnet.msg(msg[, *args]): 当调试级别为>0打印调试信息
10.Telnet.set_debuglevel(debuglevel)：设置调试级别。debuglevel越高信息越多。
11.Telnet.close() 关闭连接
12.Telnet.get_socket()：返回套接字供内部使用
13.Telnet.fileno(): 返回套接字对象内部使用的文件描述
14.Telnet.write(buffer): 常用于执行命令；写入字符串到套接字，加倍IAC的任何字符。连接关闭时可能触发OSError异常。
15.Telnet.interact(): 交由用户控制
16.Telnet.mt_interact(): 多线程版本的interact()
17.Telnet.expect(list[, timeout]): 读取直到匹配正则表达式项列表中的一个。list是一个正则表达式列表，包含编译(regx对象)或未编译
                                   （字节字符串）。timeout以秒为单位，默认值为无限期阻塞。返回元祖的三个项目：
                                   1.index为匹配正则表达式的位置；
                                   2.match对象
                                   3.此时读了的字节
18.Telnet.set_option_negotiation_callback(callback):每次从输入流读取telnet选项时，调用callback,后续步骤不会执行。
'''
 
 
class TelnetClient():
    def __init__(self,):
        self.tn = telnetlib.Telnet()
 
    # 此函数实现telnet登录主机
    def login_host(self,host_ip,username,password):
        try:
            # self.tn = telnetlib.Telnet(host_ip,port=23)
            self.tn.open(host_ip,port=23)
        except:
            logging.warning('%s网络连接失败'%host_ip)
            return False
        # 等待login出现后输入用户名，最多等待10秒
        self.tn.read_until(b'login: ',timeout=10)
        self.tn.write(username.encode('ascii') + b'\n')
        # 等待Password出现后输入用户名，最多等待10秒
        self.tn.read_until(b'Password: ',timeout=10)
        self.tn.write(password.encode('ascii') + b'\n')
        # 延时两秒再收取返回结果，给服务端足够响应时间
        time.sleep(2)
        # 获取登录结果
        # read_very_eager()获取到的是的是上次获取之后本次获取之前的所有输出
        command_result = self.tn.read_very_eager().decode('ascii')
        if 'Login incorrect' not in command_result:
            logging.warning('%s登录成功'%host_ip)
            return True
        else:
            logging.warning('%s登录失败，用户名或密码错误'%host_ip)
            return False
 
    # 此函数实现执行传过来的命令，并输出其执行结果
    def execute_some_command(self,command):
        # 执行命令
        self.tn.write(command.encode('ascii')+b'\n')
        time.sleep(2)
        # 获取命令结果
        command_result = self.tn.read_very_eager().decode('ascii')
        logging.warning('命令执行结果：\n%s' % command_result)
 
    # 退出telnet
    def logout_host(self):
        self.tn.write(b"exit\n")
 
if __name__ == '__main__':
    host_ip = '192.168.0.172'
    username = 'admin'
    password = 'mdlwlnet64'
    command = 'dis cur'
    command1 = ''
    telnet_client = TelnetClient()
    # 如果登录结果返加True，则执行命令，然后退出
    if telnet_client.login_host(host_ip,username,password):
        telnet_client.execute_some_command(command)
        for i in range(1,5):
            telnet_client.execute_some_command(command1)
        time.sleep(5)
        telnet_client.logout_host()