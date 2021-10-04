import paramiko
import os
import sys
from stat import S_ISDIR as isdir

#建立连接，获取sftp句柄
def sftp_connect(username,password,host,port=22):
    client = None
    sftp = None
    try:
        client = paramiko.Transport((host,port))
    except Exception as error:
        print ("error")
    else:
        try:
            client.connect(username=username, password=password)
        except Exception as error:
            print ("error")
        else:
            sftp = paramiko.SFTPClient.from_transport(client)
    return client,sftp
#断开连接
def disconnect(client):
    try:
        client.close()
    except Exception as error:
        print ("error")

#重远程下载文件
def _check_local(local):
    if not os.path.exists(local):
        try:
            os.mkdir(local)
        except IOError as err:
            print ("error")
def get(sftp,remote,local):
    #检查远程文件是否存在
    try:
        result = sftp.stat(remote)
    except IOError as err:
        error = '[ERROR %s] %s: %s' %(err.errno,os.path.basename(os.path.normpath(remote)),err.strerror)
        print (error)
    else:
        #判断远程文件是否为目录
        if isdir(result.st_mode):
            dirname = os.path.basename(os.path.normpath(remote))
            local = os.path.join(local,dirname)
            _check_local(local)
            for file in sftp.listdir(remote):
                sub_remote = os.path.join(remote,file)
                sub_remote = sub_remote.replace('\\','/')
                get(sftp,sub_remote,local)
        else:   
        #拷贝文件
            if os.path.isdir(local):
                local = os.path.join(local,os.path.basename(remote))
            try:
                sftp.get(remote,local)
            except IOError as err:
                print ("error")
            else:
                print ('[get]',local,'<==',remote)
#上截文件到设备
def put(sftp,local,remote):
    #检查路径是否存在
    def _is_exists(path,function):
        path = path.replace('\\','/')
        try:
            function(path)
        except Exception as error:
            return False
        else:
            return True
    #拷贝文件
    def _copy(sftp,local,remote):
        #判断remote是否是目录
        if _is_exists(remote,function=sftp.chdir):
            #是，获取local路径中的最后一个文件名拼接到remote中
            filename = os.path.basename(os.path.normpath(local))
            remote = os.path.join(remote,filename).replace('\\','/')
        #如果local为目录
        if os.path.isdir(local):
            #在远程创建相应的目录
            _is_exists(remote,function=sftp.mkdir)
            #遍历local
            for file in os.listdir(local):
                #取得file的全路径
                localfile = os.path.join(local,file).replace('\\','/')
                #深度递归_copy()
                _copy(sftp=sftp,local=localfile,remote=remote)
        #如果local为文件
        if os.path.isfile(local):
            try:
                sftp.put(local,remote)
            except Exception as error:
                print ("error")
                print ('[put]',local,'==>',remote,'FAILED')
            else:
                print ('[put]',local,'==>',remote,'SUCCESSED')
    #检查local
        if not _is_exists(local,function=os.stat):
            print ("'"+local+"': No such file or directory in local")
            return False
    #检查remote的父目录
        remote_parent =  os.path.dirname(os.path.normpath(remote))
        if not _is_exists(remote_parent,function=sftp.chdir):
            print ("'"+remote+"': No such file or directory in remote")
            return False
    #拷贝文件
        _copy(sftp=sftp,local=local,remote=remote)
def main():
   
    connect = sftp_connect('admin','mdlwlnet64','192.168.0.172')
    print (connect[0],'\n')
    print (connect[1],'\n')
    remote="/$_backup/running_config/20201223090929.my.zip"
    local="C:\\backpup"
    get(connect[1],local,remote)



if __name__ == '__main__':
        main()
