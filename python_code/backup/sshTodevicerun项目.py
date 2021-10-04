#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
使用说明：
1.设备列表为csv格式（文本），第一行为注释，执行时会自动跳过第一行
数据中心,网络分区,设备名称,设备IP,用户名,密码,厂商
2.主函数中的参数即为该设备列表的名称
3.日志：3.1实时打印日志
        3.2详细日志和结果日志会生成在脚本目录log
4.配置备份目录，自动生成，目录为YMD网络配置备份，YMD分别为年月日，二三级目录根据数据中心，网络分区生产

当前版本1.3
版本更新说明
初始版本：支持华为display cu,测试screen-length 0 temporary
1.0更新，将各厂商设备方法get_config和get_config_more转成Device类的通用方法
1.1更新：1.locale在不同的操作系统可能报错，时间显示修改成默认，
        2.各提示修改为英文,读写编码修改为GBK，解决某些设备写入错误问题。
        3.解决paramiko recv 65535问题，通过while语句，config+=outbuf.decode
        4.写入配置前替换不支持分屏命令的设备记录日志时有 ---- More ----[42D                                          [42D 字符
        5.增加了异常抛出登录时ssh版本问题Incompatible version
        5.增加异常抛出，设备型号不支持记录并继续下一步class ErrorType(Device)
1.1.1更新：提示为中文
1.2更新：1.配置记录不全的设备尝试重新登录备份
1.3更新：1.增加执行详细记录log和执行结果log
        2.增加详细日志和结果日志里的password显示为******
        3.将devicelist独立为一个参数，放到main函数上
        4.4.F5不分屏modify cli preference pager disabled display-threshold 0
'''
import socket, os, time, re
import paramiko
#定义设备类
class Device(object):
    # 初始化参数，与设备devicelist的列参数一一对应
    #定义通用方法，login登录，screenCMD判断是否支持分屏命令，
    # get_config通用分屏命令取配置，get_config_more为不支持分屏命令的取配置方法
    def __init__(self, dc, zone, hostname, ip, user, passwd):
        self.dc=dc
        self.zone=zone
        self.hostname = hostname
        self.ip = ip
        self.user = user
        self.passwd = passwd
        self.success_flag = True
        self.screen_cmd_flag = True
        self.success_login_count = 0#登录成功次数
        self.success_backup_count = 0#备份成功次数
        self.fail_backup_count = 0#备份失败次数
        self.fail_login_count = 0#登陆失败次数
        self.fail_backup_context = ''#存放备份失败的设备信息
        self.fail_login_context = ''#存放登录失败的设备信息
        self.exe_detail_log=''# 保存执行过程详细日志
        self.ssh= paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #登录
    def login(self):
        if self.success_flag:
            try:
                self.ssh.connect(hostname=self.ip, username=self.user, password=self.passwd, look_for_keys=False, timeout=5)
                self.success_login_count = 1
            except paramiko.ssh_exception.AuthenticationException as e:
                self.success_flag = False
                self.fail_login_count = 1
                self.fail_login_context='%s-%s - %s' % (self.hostname,self.ip, e)
                self.exe_detail_log+=(TimeOps.get_time_stamp()+','+self.fail_login_context+'\n')
                print(self.fail_login_context)
            except paramiko.ssh_exception.SSHException as e:
                #paramiko.ssh_exception.SSHException: Incompatible version (1.5 instead of 2.0)
                self.success_flag = False
                self.fail_login_count = 1
                self.fail_login_context='%s-%s - %s' % (self.hostname,self.ip, e)
                self.exe_detail_log+=(TimeOps.get_time_stamp()+','+self.fail_login_context+'\n')
                print(self.fail_login_context)
            except socket.timeout as e:
                self.success_flag = False
                self.fail_login_count = 1
                self.fail_login_context='%s-%s - %s' % (self.hostname,self.ip, e)
                self.exe_detail_log+=(TimeOps.get_time_stamp()+','+self.fail_login_context+'\n')
                print(self.fail_login_context)
            else:
                pass
    #判断是否支持分屏
    def screenCMD(self,scmd):
        Device.login(self)
        if self.success_flag :
            cmd = self.ssh.invoke_shell()
            cmd.send(scmd+'\n')
            time.sleep(1)
            out_buf = cmd.recv(65535).decode('gbk', 'ignore')
            self.ssh.close()
            if re.findall(r'Error:|Unrecognized command|Incomplete command|Wrong parameter', out_buf):
                self.screen_cmd_flag = False
                self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + '%s-%s设备不支持分屏disable命令'%(self.hostname,self.ip)+'\n')
    #支持分屏的获取命令，并将日志写入为文件
    def get_config(self,log_return,*args):#log_return为配置完成的返回值（比如return），*args为命令集list
        recv_config=''#str类型
        start_time=time.time()
        Device.login(self)#登录设备
        if self.success_flag :
            success_log='%s-%s 登录成功。'%(self.hostname,self.ip)
            print(success_log,end='')
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + success_log+'\n')
            cmd=self.ssh.invoke_shell()
            for i in args:  # 循环读取命令集，并逐一执行
                time.sleep(0.3)
                cmd.send(i + "\n")
            time.sleep(3)  # 测试3s能完整记录，有些设备登录比较慢（H3C），在下一环节进行时间等待if 'return' not in str(out_buf)
            while True:  # 持续接受通道的数据流，解决recv 65535问题
                if cmd.recv_ready():
                    out_buf = cmd.recv(65535)  # byte类型
                    if len(out_buf) == 0:
                        raise EOFError('通道数据流被远程设备关闭。')
                    recv_config += out_buf.decode('gbk', 'ignore')
                    if log_return not in str(out_buf):#如果记录未完成，继续等待记录
                        time.sleep(0.3)
                else:
                    break
            if log_return in recv_config:
                self.success_backup_count = 1
                success_log = '日志数据流记录成功。'
                print(success_log, end='')
                self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + success_log+'\n')
            else:
                self.fail_backup_count = 1
                self.fail_backup_context='%s日志中没有包含关键字 %s 。'%(self.ip,log_return)
                self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + self.fail_backup_context+'\n')
                print('%s日志中没有包含关键字 \033[0;31m%s\033[0m 。'%(self.ip,log_return),end='')
            self.ssh.close()
            recv_config = recv_config.replace('\r\n', '\n')  # Windows显示\r\n分行替换为\n
            FileOps.writecfg(self.dc, self.zone, self.hostname, recv_config)#将日志写到文件
            end_time=time.time()
            time_log='耗时 %s 秒。'%int(end_time-start_time)
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + time_log+'\n')
            print(time_log)

    # 不支持分屏的获取命令，并将日志写入为文件
    def get_config_more(self,log_return,*args):#接受命令集
        recv_config=''#str类型
        start_time=time.time()
        Device.login(self)#设备登录
        if self.success_flag :
            success_log='%s-%s 登录成功。'%(self.hostname,self.ip)
            print(success_log,end='')
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + success_log+'\n')
            cmd=self.ssh.invoke_shell()
            for i in args:#循环读取命令集，并逐一执行
                time.sleep(0.3)
                cmd.send(i+"\n")
            while True:#持续接受通道的数据流，解决recv 65535问题
                if cmd.recv_ready():
                    out_buf=cmd.recv(65535)#byte类型
                    if len(out_buf)==0:
                        raise EOFError('通道数据流被远程设备关闭。')
                    recv_config +=out_buf.decode('gbk', 'ignore')
                if log_return not in str(out_buf) and str(out_buf).endswith('--')==False:#可能有多种情况的more--，取--
                    cmd.send(' ')
                    time.sleep(0.1)
                else:
                    break
            if log_return in recv_config:
                self.success_backup_count = 1
                success_log = '日志数据流记录成功。'
                print(success_log, end='')
                self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + success_log+'\n')
            else:
                self.fail_backup_count = 1
                self.fail_backup_context='%s日志中没有包含关键字 %s 。'%(self.ip,log_return)
                self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + self.fail_backup_context+'\n')
                print('%s日志中没有包含关键字 \033[0;31m%s\033[0m 。'%(self.ip,log_return),end='')
            self.ssh.close()
            recv_config = recv_config.replace('\r\n','\n')#Windows显示\r\n分行替换为\n
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + '执行替换\\r\\n为\\n动作。'+'\n')
            recv_config = recv_config.replace('  ---- More ----[42D                                          [42D','')
            recv_config = recv_config.replace(' ---- More ----[42D                                          [42D ','')
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + '执行替换---- More ----动作。'+'\n')
            #解决More的显示问题
            FileOps.writecfg(self.dc, self.zone, self.hostname, recv_config)
            end_time=time.time()
            time_log='耗时 %s 秒。'%int(end_time-start_time)
            self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + time_log+'\n')
            print(time_log)
#华为
class Huawei(Device):
    #华为需要判断是否支持分屏
    def ops(self):
        #测试是否支持分屏命令
        Huawei.screenCMD(self,'screen-length 0 temporary')
        if self.success_flag:
            if self.screen_cmd_flag:
                Huawei.get_config(self,'return','screen-length 0 temporary','display cu')
                # 第一个为记录配置完成标志的返回值，后面为命令集
            else:
                Huawei.get_config_more(self,'return','display cu')
                # 第一个为记录配置完成标志的返回值，后面为命令集
class H3C(Device):
    def ops(self):
        if self.success_flag:
            H3C.get_config(self,'return','screen-length disable','display cu')
            # 第一个为记录配置完成标志的返回值，后面为命令集
class Cisco(Device):
    def ops(self):
        if self.success_flag:
            Cisco.get_config(self,'line vty','terminal length 0','show run')
            # 第一个为记录配置完成标志的返回值，后面为命令集
class ZTE(Device):
    def ops(self):
        if self.success_flag:
            ZTE.get_config(self,'end','terminal length 0','show run')
            # 第一个为记录配置完成标志的返回值，后面为命令集
class A10(Device):
    def ops(self):
        if self.success_flag:
            A10.get_config(self,'end','enable\n','terminal length 0','show running-config all-partitions')
            # 第一个为记录配置完成标志的返回值，后面为命令集
class FiberHome(Device):
    def ops(self):
        if self.success_flag:
            FiberHome.get_config(self,'#','enable','terminal length 0','show running-config')
            # 第一个为记录配置完成标志的返回值，后面为命令集
class F5(Device):
    def ops(self):
        if self.success_flag:
            F5.get_config(self,'(tmos)#','tmsh','modify cli preference pager disabled display-threshold 0','show running-config')
class TOPSEC(Device):
    def ops(self):
        if self.success_flag:
            TOPSEC.get_config(self,'config implement','show-running nostop')
class Forti(Device):
    def ops(self):
        if self.success_flag:
            Forti.get_config(self,'router setting','config system console','set output standard','end','show full-configuration')
class Maipu(Device):
    def ops(self):
        if self.success_flag:
            Maipu.get_config(self,'end','more off','show running-config')
class ErrorType(Device):
    def ops(self):
        self.fail_login_count = 1
        self.fail_login_context = '不支持 %s-%s 该设备型号。' % (self.hostname, self.ip)
        self.exe_detail_log += (TimeOps.get_time_stamp() + ',' + self.fail_login_context+'\n')
        print('不支持 \033[0;31m%s-%s\033[0m 该设备型号。' % (self.hostname, self.ip))

#定义文件操作，包括读取设备列表文件，设备配置存档
class FileOps(object):
    #文件读取
    cur_path = os.getcwd()
    write_main_path = cur_path + ('\\%s网络配置备份' % time.strftime('%Y%m%d'))#备份的主目录
    @staticmethod
    def readcfg(file):
        with open(file, 'r', encoding='GBK') as f:
            filelist = f.read().split('\n')
            filelist.pop(0)#配置文件首行为注释行
        return filelist
    # 文件保存
    @staticmethod
    def writecfg(dc,zone,hostname,cfg):
        dev_path='\\%s\\%s'%(dc,zone)#设备子目录，根据设备数据中心/网络分区划分
        write_path=FileOps.write_main_path+dev_path#写入的详细目录
        if not os.path.exists(write_path):
            os.makedirs(write_path)
        file='%s.txt'%(hostname)
        with open(write_path+'\\'+file, 'w',encoding='gbk') as f:
            f.write(cfg)
            print('配置备份成功，保存为 %s\%s' % (dev_path,file),end='。')#只显示设备子目录
    #日志写入
    @staticmethod
    def writelog(logstr,logname):
        logpath='log'
        log_separator='分 隔 行'.center(60,'-')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        logname=logname+'%s.log'%time.strftime('%Y%m%d')
        with open(logpath+'\\'+logname, 'a',encoding='gbk') as f:
            f.write('\n'+log_separator+'\n'+logstr)
#设备厂商判断，返回设备厂商函数，自动实例化
class DeviceVendor(object):
    # 判断设备厂商，自动实例化
    @staticmethod
    def OPS(*args):#任意列表参数
        if str(args[6]).upper() == 'HUAWEI':
            return Huawei(*args[0:-1])
        elif str(args[6]).upper() == 'H3C':
            return H3C(*args[0:-1])
        elif str(args[6]).upper() == 'CISCO':
            return Cisco(*args[0:-1])
        elif str(args[6]).upper() == 'ZTE':
            return ZTE(*args[0:-1])
        elif str(args[6]).upper() == 'A10':
            return A10(*args[0:-1])
        elif str(args[6]).upper() == 'FIBERHOME':
            return FiberHome(*args[0:-1])
        elif str(args[6]).upper() == 'F5':
            return F5(*args[0:-1])
        elif str(args[6]).upper() == 'TOPSEC':
            return TOPSEC(*args[0:-1])
        elif str(args[6]).upper() == 'FORTI':
            return Forti(*args[0:-1])
        elif str(args[6]).upper() == 'MAIPU':
            return Maipu(*args[0:-1])
        else:
            return ErrorType(*args[0:-1])#不支持的设备类型
class TimeOps(object):#计算时间戳到毫秒
    @staticmethod
    def get_time_stamp():
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        data_secs = (ct - int(ct)) * 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)
        return time_stamp
def main(devicelist):
    all_exe_detail_log=''#运行详细日志
    all_exe_result_log=''#运行结果日志
    start_time = time.time()
    start_log='%s，配置备份程序正在运行，请等待！！！'%time.strftime('%Y/%m/%d %H:%M:%S')+\
              '\n'+'备份路径为 : %s'%FileOps.write_main_path
    all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + start_log+'\n')
    print(start_log)
    devicelist=FileOps.readcfg(devicelist)#读取设备列表，这里已转为list[]
    all_success_login_count = 0  # 登录成功次数
    all_success_backup_count = 0  # 备份成功次数
    all_fail_backup_count = 0  # 备份失败次数
    all_fail_login_count = 0  # 登陆失败次数
    devicelistErr_count=0
    all_fail_backup_context = []  # 存放备份失败的设备信息
    all_fail_login_context = []  # 存放登录失败的设备信息
    devicelistErr_context=[]    # 存放设备list参数错误的设备信息
    all_fail_backup_dev_dict={} # 存放设备备份记录不全的设备列表，用于下次尝试继续登录备份
    devicenum=0#统计总的设备数量
    for i in devicelist:#循环设备列表[]的每行
        list=i.split(',')#将每行的str转换为list[]
        if len(list)==7:#判定该行的参数是否完整，可能出现空行，需要跳过
            devicenum+=1
            DeviceOps=DeviceVendor().OPS(*list)#判断设备厂商，执行设备厂商class，参数以list传入
            DeviceOps.ops()#调用厂商方法
            all_success_login_count+=DeviceOps.success_login_count#记录登录成功的次数
            all_success_backup_count+=DeviceOps.success_backup_count#记录备份成功的次数
            all_fail_login_count+=DeviceOps.fail_login_count#记录登录失败的次数
            all_fail_backup_count+=DeviceOps.fail_backup_count#记录备份失败的次数
            if DeviceOps.fail_login_context != '':
                all_fail_login_context.append(DeviceOps.fail_login_context)#记录登录失败的日志
            if DeviceOps.fail_backup_context != '':
                all_fail_backup_context.append(DeviceOps.fail_backup_context)#记录备份失败的日志
                fail_backup_index=all_fail_backup_context.index(DeviceOps.fail_backup_context)#该设备失败日志在总的失败日志里的index
                all_fail_backup_dev_dict[fail_backup_index]=i
                #将设备信息加入到备份失败字典，用于下次继续尝试登录备份，key为败日志里的index（方便后续删除），value为设备参数信息
            all_exe_detail_log += DeviceOps.exe_detail_log  # 记录运行详细日志
        else:#否则记录错误设备参数并打印
            devicenum+=1
            devicelistErr_count+=1
            if len(list)>5:
                list[5]='******'#将密码替换成******
            devicelistErr='Devicelist第 %s 行参数不对或者空行,行信息如下: %s'%(devicelist.index(i)+2,','.join(list))
            #devicelist.index(i)+2,list从0开始，且pop了第一行注释，因此需要+2
            devicelistErr_context.append(devicelistErr)
            all_exe_detail_log += (TimeOps.get_time_stamp()+','+devicelistErr)  # 记录运行详细日志
            print('Devicelist第 \033[0;31m%s\033[0m 行参数不对或者空行,行信息如下: %s'%(devicelist.index(i)+2,','.join(list)))
    #尝试重新登录备份
    if all_fail_backup_dev_dict!={}:
        re_backup_log='\n尝试重新登录备份失败的设备！'
        print('\n\033[1m尝试重新登录备份失败的设备！\033[0m')
        all_exe_detail_log += (TimeOps.get_time_stamp()+','+re_backup_log+'\n')  # 记录运行详细日志
        for k,v in all_fail_backup_dev_dict.items():  # 遍历字典，k为all_fail_backup_context的index，v为设备参数
            list = v.split(',')  # 将每行的str转换为list[]
            DeviceOps = DeviceVendor().OPS(*list)  # 判断设备厂商，执行设备厂商class，参数以list传入
            DeviceOps.ops()  # 调用厂商方法
            if DeviceOps.fail_backup_context != '':#备份失败
                re_backup_failed_log='重新备份失败，%s'%DeviceOps.fail_backup_context
                all_exe_detail_log += (TimeOps.get_time_stamp() +','+ re_backup_failed_log+'\n')
                print(re_backup_failed_log)
            else:
                all_success_backup_count += DeviceOps.success_backup_count  # 增加备份成功的次数
                all_fail_backup_count -= DeviceOps.success_backup_count  # 减少备份失败的次数减
                all_fail_backup_context.pop(k)#删除备份失败的内容
                re_backup_success_log='%s-%s重新备份成功'%(DeviceOps.hostname,DeviceOps.ip)
                all_exe_detail_log += (TimeOps.get_time_stamp() +','+ re_backup_success_log)
                print(re_backup_success_log)

    #结果信息
    result_log='\n#*#*#*#*备 份 结 果*#*#*#*#'
    all_exe_detail_log+=(TimeOps.get_time_stamp()+','+result_log+'\n')
    all_exe_result_log+=(TimeOps.get_time_stamp()+'\n'+result_log+'\n')
    print('\n\033[1m#*#*#*#*备 份 结 果*#*#*#*#\033[0m')
    dev_log='设备总数 %s ，成功备份的设备数量 %s .'%(devicenum,all_success_backup_count)
    all_exe_detail_log+=(TimeOps.get_time_stamp()+','+dev_log+'\n')
    all_exe_result_log+=(dev_log+'\n')
    print('设备总数 \033[1m%s \033[0m，成功备份的设备数量 \033[1m%s \033[0m.'%(devicenum,all_success_backup_count))
    if all_fail_backup_count > 0 :#备份失败设备信息
        all_fail_backup_log='\n#备份失败的设备数量： %s ,具体如下： '%all_fail_backup_count
        all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + all_fail_backup_log+'\n')
        all_exe_result_log += (all_fail_backup_log+'\n')
        print('\n#\033[1;31m备份失败\033[0m的设备数量： \033[1;31m%s\033[0m ,具体如下： '%all_fail_backup_count)
        for i in all_fail_backup_context:
            print('\t',i)
            all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + '\t'+i+'\n')
            all_exe_result_log += ('\t'+i+'\n')
    if all_fail_login_count > 0 :#登录失败设备信息
        all_fail_login_log='登录失败的设备数量： %s ,具体如下： '%all_fail_login_count
        all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + all_fail_login_log+'\n')
        all_exe_result_log += (all_fail_login_log+'\n')
        print('\033[1;31m登录失败\033[0m的设备数量： \033[1;31m%s\033[0m ,具体如下： '%all_fail_login_count)
        for i in all_fail_login_context:
            print('\t',i)
            all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + '\t'+i+'\n')
            all_exe_result_log += ('\t'+i+'\n')
    if devicelistErr_count > 0 :#设备列表参数错误
        dev_err_log='在devicelst.csv文件中，有 %s 行参数错误，具体如下：'%devicelistErr_count
        all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + dev_err_log+'\n')
        all_exe_result_log += (dev_err_log+'\n')
        print('在devicelst.csv文件中，有 \033[1;31m%s 行参数错误\033[0m，具体如下：'%devicelistErr_count)
        for i in devicelistErr_context:
            list=i.split(',')#将每行的str转换为list[]
            if len(list) >= 6:#因为devicelistErr_context里多了Devicelist第 x 行参数不对或者空行', '行信息如下:,里面有一个‘，’，因此+1
                list[6]='******'#将密码加密
            i=','.join(list)#重新转换成str
            print('\t',i)
            all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + '\t'+i+'\n')
            all_exe_result_log += ('\t'+i+'\n')
    end_time = time.time()
    end_log='\n程序运行总耗时: %s 秒。'%(int(end_time - start_time))
    all_exe_detail_log += (TimeOps.get_time_stamp() + ',' + end_log+'\n')
    all_exe_result_log += (end_log+'\n')
    FileOps.writelog(all_exe_detail_log,'detail')
    FileOps.writelog(all_exe_result_log, 'result')
    print(end_log)
if __name__ == "__main__":
    main('devicelist.csv')
