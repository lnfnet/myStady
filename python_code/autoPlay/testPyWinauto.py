from pywinauto import Application
import time

app = Application(backend="uia").start('notepad.exe')
app.__setattr__("name","notepad")
time.sleep(2)
app.notepad.edit.TypeKeys('Test ......................')
app.edit.TypeKeys('Test ......................')
time.sleep(2)
#中文版本操作
app.Notepad.MenuSelect(u"文件(F)->另存为(A)...")
app.Dialog.edit.TypeKeys(u'TestFile.txt')
time.sleep(2)
#点击保存
app.Dialog.Button1.Click()
time.sleep(2)
app.Notepad.Close()
