def Get_CRC():
    try:
        pynet1 = {
        'device_type': "hp_comware",
        'ip': "10.10.10.10",
        'username': "CTyunuser",
        'password': "P@ssw0rd6900",
        }
        conn1 = ConnectHandler(**pynet1)
        cmd='display counters inbound interface '
        #cmd = 'display interface brief \n'
        outp=conn1.send_command_timing(cmd)
        if "---- More ----" in outp:
            outp += conn1.send_command_timing(
                '            \n', strip_prompt=False, strip_command=False, normalize=False
            )      *###遇到more，就多输入几次个空格，normalize=False表示不取消命令前后空格*。
        outp1 = outp.split("\n")
        print (outp1)

    except (EOFError,NetMikoTimeoutException):
        print('Can not connect to Device')
    except (EOFError, NetMikoAuthenticationException):
        print('username/password wrong!')
    except (ValueError, NetMikoAuthenticationException):
        print('enable password wrong!')

if __name__=="__main__":
     Get_CRC()

