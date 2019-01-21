import easygui as g 
import urllib
import urllib2
import json

#以下弹出窗口获取用户输入的账号密码
msg="Login In remote desktop" 
title="Login" 
fieldNames=["*User:","*Password:"] 
fieldValues=[] 
fieldValues=g.multpasswordbox(msg,title,fieldNames) 
while True:
    if fieldValues==None: 
        errmseg=""
        break
    for i in range(len(fieldNames)): 
        option=fieldNames[i].strip() 
        if fieldValues[i].strip()=="" and option[0]=="*": 
            errmsg+=("[%s] must input" %fieldNames[i]) 
        if errmsg=="": 
            break 
        fieldValues=g.multpasswordbox(errmsg,title,fieldNames,fieldValues) 

#以下获取分配给用户的虚拟机列表
url = "http://192.168.0.100:8000/login/" 
params={"u":fieldValues[0],"p":fieldValues[1],"t":"cs"}
data = urllib.urlencode(params) 
req = urllib2.Request(url, data) 
response = urllib2.urlopen(req)
html = response.read()
vmlist=json.loads(html)
vmarr=[]
for vm in vmlist:
        vmarr.append(vm.get('vmname'))

#显示虚拟机列表让用户选择
selvm=g.buttonbox("please select desktop?",choices=vmarr)

#获取选择虚拟机的ID
myvmid=""
for vm in vmlist:
        if vm.get('vmname')==selvm:
                myvmid= vm.get('vmid')
                break

#getvncport服务端程序根据虚拟机ID启动该虚拟机，并获取连接URL
url="http://192.168.0.100:8000/getvncport/?ty=spice&vm=" + myvmid
req = urllib2.Request(url) 
response = urllib2.urlopen(req)
spice = response.read()

#spice是云桌面连接url，以下程序启动连接，并在退出连接后关闭瘦客户机电源
os.popen('remote-viewer -f ' + spice + ' && poweroff')
