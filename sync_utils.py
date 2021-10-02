#!/usr/bin/env python
# encoding: utf-8
# 访问 http://tool.lu/pyc/ 查看更多信息
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import datetime
import time
import dict4ini
import pyodbc
import heapq
import logging
import sched
from collections import namedtuple
from traceback import print_exc
from mysite.personnel.models.model_dept import Department
from mysite.personnel.models.model_emp import Employee, format_pin
from models.model_leave import LeaveLog
from models.model_dept_erp import Department_ERP
from models.model_log_erp import ERP_LOG
from models.model_emp_erp import Employee_ERP
from redis.server import start_dict_server, queqe_server
q_server = queqe_server()
cursor = None

def customSql(sql, action = True):
    cur = connection.cursor()
    cur.execute(sql)
    if action:
        connection._commit()
    
    return cur


def get_timestamp(now = None):
    if isinstance(now, datetime.datetime):
        timeStamp = time.mktime(now.timetuple())
        return timeStamp


def getList(key = None):
    is_exist = q_server.has_key(key)
    if not is_exist:
        q_server.set_to_file(key, repr([]))
    
    if key:
        itemList = eval(q_server.get_from_file(key))
        return itemList


def setFile(key = None, new_item = None, isNull = None):
    if isNull:
        q_server.set_to_file(key, repr([]))
    
    if not key:
        raise Exception(_(u'key-value\xe4\xb8\x8d\xe5\x85\x81\xe8\xae\xb8\xe7\xa9\xba'))
    return key
    is_exist = q_server.has_key(key)
    if not is_exist:
        q_server.set_to_file(key, repr([]))
    
    if q_server.has_key(key):
        q_server.lock(key)
        old_item = getList(key)
        if isinstance(new_item, list):
            new_list = old_item + new_item
        
        if isinstance(new_item, int):
            old_item.append(new_item)
            new_list = old_item
        
        new_set = set(new_list)
        new_list = list(new_set)
        new_list = repr(new_list)
        q_server.set_to_file(key, new_list)
        q_server.unlock(key)
    


def set_log(log_str = None):
    now = datetime.datetime.now()
    log_str = u'end date:' + str(now) + '  log: ' + log_str
    logfile = 'tmp/ERP_SYCN_ZK.log'
    logger = logging.getLogger()
    handler = logging.FileHandler(logfile)
    logger.addHandler(handler)
    logger.setLevel(logging.NOTSET)
    logger.info(str(log_str))


def get_dbinfo():
    db_dict = { }
    bak_dict = dict4ini.DictIni(settings.APP_HOME + '/attsite.ini')['DATABASE_BAK']
    db_dict['SERVER'] = bak_dict['HOST']
    db_dict['DATABASE'] = bak_dict['NAME']
    db_dict['UID'] = bak_dict['USER']
    db_dict['PWD'] = bak_dict['PASSWORD']
    return db_dict


def db_connect():
    global cursor
    if cursor:
        return None
    db_dict = get_dbinfo()
    db_str = 'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (db_dict['SERVER'], db_dict['DATABASE'], db_dict['UID'], db_dict['PWD'])
    conn = pyodbc.connect(db_str)
    cursor = conn.cursor()


def select_sql(sql = None, param = None):
    global cursor
    
    try:
        if not cursor:
            db_connect()
        
        if not param:
            rows = cursor.execute(sql).fetchall()
    except Exception:
        e = None
        cursor = None
        db_connect()
        if not param:
            rows = cursor.execute(sql).fetchall()
        

    return rows

Dept = namedtuple('Dept', 'code, name')
EMP = namedtuple('EMP', 'PIN,EName, DeptCode,rEmployState,ruzhilaiyuan')

def getERPDeptCount():
    sql_count = 'select count(*) from Department'
    count = select_sql(sql_count)[0][0]
    return count


def getERPEmpOnCount():
    sql_count = 'select count(*) from hr_hi_person where rEmployState=10'
    count = select_sql(sql_count)[0][0]
    return count


def getERPOffCount():
    sql_count = 'select count(*) from hr_hi_person where rEmployState=30'
    count = select_sql(sql_count)[0][0]
    return count


def getERPOfMaxID():
    sql_maxID = 'select cPsn_Num,cPsn_Name,cDept_num,rEmployState ,ruzhilaiyuan from hr_hi_person'
    id_list = select_sql(sql_maxID)
    max_list = []
    erp_emp_message_list = []
    for item in id_list:
        id = int(item[0].strip())
        emp = (item[0].strip(), item[1].strip(), item[2].strip(), item[3].strip(), item[4].strip())
        erp_emp_message_list.append(emp)
        max_list.append(id)
    
    maxID = max(max_list)
    is_exist = q_server.get_from_file('erp_frist')
    if not is_exist:
        q_server.set_to_file('erp_emp_message_list', repr(erp_emp_message_list))
    else:
        last_one = eval(q_server.get_from_file('erp_emp_message_list'))
        (on_list, off_list) = getErpEmpList()
        (on_new_list, off_new_list) = getErpEmpList(isNew = True, newList = erp_emp_message_list)
        if len(erp_emp_message_list) > last_one and len(on_list) != len(on_new_list) or len(off_list) != len(off_new_list):
            q_server.set_to_file('erp_emp_message_list', repr(erp_emp_message_list))
        
    return maxID


def checkERPOfEmpData():
    u'''
        \xe4\xba\xba\xe5\x91\x98\xe7\xbc\x96\xe5\x8f\xb7\xef\xbc\x8c\xe4\xba\xba\xe5\x91\x98\xe5\x90\x8d\xe7\xa7\xb0\xef\xbc\x8c\xe9\x83\xa8\xe9\x97\xa8\xe5\x8f\xb7\xef\xbc\x8c\xe4\xba\xba\xe5\x91\x98\xe7\x8a\xb6\xe6\x80\x81\xef\xbc\x8c\xe5\x85\xa5\xe8\x81\x8c\xe6\x9d\xa5\xe6\xba\x90\xef\xbc\x8c\xe5\x8d\xa1\xe5\x8f\xb7
    '''
    sql_maxID = 'select cPsn_Num,cPsn_Name,cDept_num,rEmployState ,ruzhilaiyuan,vCardNo from hr_hi_person'
    id_list = select_sql(sql_maxID)
    max_list = []
    erp_emp_message_list = []
    for item in id_list:
        if item[5] is None:
            item[5] = ''
        
        if not len(item[0]) or item[0] is None:
            err_str = 'pin is null'
            set_log(err_str)
            continue
        
        
        try:
            emp = (item[0].strip(), item[1].strip(), item[2].strip(), item[3].strip(), item[4].strip(), item[5].strip())
        except Exception:
            e = None
            err_str = 'PIN=' + item[0] + 'EName=' + item[1] + 'DeptCode=' + item[2] + 'rEmployState=' + item[3] + 'ruzhilaiyuan=' + item[4] + 'rCardNo=' + item[5]
            set_log(err_str)
            continue

        erp_emp_message_list.append(emp)
    
    is_exist = q_server.get_from_file('erp_frist')
    if not is_exist:
        q_server.set_to_file('erp_emp_message_list', repr(erp_emp_message_list))
        (on_list, off_list) = getErpEmpList()
        setFile('on_list', on_list)
        setFile('off_list', off_list)
    else:
        getSum(erp_emp_message_list)


def getErpEmpList(isNew = False, newList = None):
    emp_list = eval(q_server.get_from_file('erp_emp_message_list'))
    if isNew:
        emp_list = newList
    
    on_list = []
    off_list = []
    for item in emp_list:
        if int(item[3]) == 10:
            on_list.append(item)
            continue
        if int(item[3]) == 30:
            off_list.append(item)
            continue
        if int(item[3]) == 20:
            off_list.append(item)
            continue
    
    return (on_list, off_list)


def getDeptOfCode(code):
    sql_dept = 'select cDepName from Department where cDepCode=%s' % code
    dept_list = select_sql(sql_dept)
    name = dept_list[0][0]
    return name


def checkERPOfDeptData():
    sql_all_dept = 'select cDepCode,cDepName from Department'
    dept_item = select_sql(sql_all_dept)
    dept_list = []
    for item in dept_item:
        if item[0] is None or not len(item[0]):
            continue
        
        dept = (item[0].strip(), item[1].strip())
        dept_list.append(dept)
    
    is_exist = q_server.get_from_file('erp_frist')
    if not is_exist:
        q_server.set_to_file('erp_dept_message_list', repr(dept_list))
        setFile('new_dept', dept_list)
    else:
        last_one = eval(q_server.get_from_file('erp_dept_message_list'))
        if len(dept_list) > len(last_one):
            newList = list(set(dept_list) - set(last_one))
            setFile('new_dept', newList)
            q_server.set_to_file('erp_dept_message_list', repr(dept_list))
        
    return dept_list


def getAllDept():
    is_exist = q_server.get_from_file('erp_frist')
    if not is_exist:
        dept_item = eval(q_server.get_from_file('erp_dept_message_list'))
    
    dept_code = []
    dept_list = []
    for item in dept_item:
        dept = Dept(code = item[0].strip(), name = item[1].strip())
        dept_code.append(dept.code)
        dept_list.append(dept)
    
    return (dept_list, dept_code)


def getEmpOfRT():
    sql_all_rt = 'select cPsn_Num,cPsn_Name,cDept_num,rEmployState ,ruzhilaiyuan from hr_hi_person where ruzhilaiyuan=3 and rEmployState=10'
    emp_item = select_sql(sql_all_rt)
    emp_pin = []
    emp_list = []
    for item in emp_item:
        emp = EMP(PIN = item[0].strip(), EName = item[1].strip(), DeptCode = item[2].strip(), rEmployState = item[3].strip(), ruzhilaiyuan = item[4].strip())
        emp_pin.append(emp.PIN)
        emp_list.append(emp)
    
    return (emp_list, emp_pin)


def getEmpOfOnOrOff(isOn = True):
    (emp_on, emp_off) = getErpEmpList()
    if isOn:
        emp_item = emp_on
    elif not isOn:
        emp_item = emp_off
    
    emp_pin = []
    emp_list = []
    for item in emp_item:
        emp = EMP(PIN = item[0].strip(), EName = item[1].strip(), DeptCode = item[2].strip(), rEmployState = item[3].strip(), ruzhilaiyuan = item[4].strip())
        emp_pin.append(emp.PIN)
        emp_list.append(emp)
    
    return (emp_list, emp_pin)


def getERPOfData():
    
    try:
        empOfMaxID = getERPOfMaxID()
        (on_empOfErp, off_empOfErp) = getErpEmpList()
        empOnCount = len(on_empOfErp)
        empOffCount = len(off_empOfErp)
        deptOfERP = getDeptForFile()
        deptCount = len(deptOfERP)
        is_exist = q_server.get_from_file('erp_frist')
        now = datetime.datetime.now()
        if is_exist:
            erp_log = ERP_LOG.objects.get(log_flat = 'log')
            if int(deptCount) > int(erp_log.log_dept_erp_count):
                (dept_erp_list, dept_erp_code) = getAllDept()
                dept_new_list = list(set(dept_erp_code) - set(getList('dept_list_bak')))
                for dept in dept_erp_list:
                    if dept.code in dept_new_list:
                        Department_ERP(code = dept.code, name = dept.name, erp_date = now).save()
                        setFile('dept_list', dept_new_list)
                        continue
                
            
            if int(empOfMaxID) > int(erp_log.log_emp_pin):
                (emp_list, emp_pin) = getEmpOfOnOrOff(isOn = True)
                emp_new_list = list(set(emp_pin) - set(getList('emp_list_bak')))
                for emp in emp_list:
                    if emp.PIN in emp_new_list:
                        Employee_ERP(PIN = emp.PIN, EName = emp.EName, DeptCode = emp.DeptCode, ruzhilaiyuan = emp.ruzhilaiyuan, rEmployState = emp.rEmployState, Hiredday = now, erp_date = now, operation = 1).save()
                        continue
                
                setFile('emp_list', emp_new_list)
            
            if int(empOffCount) > int(erp_log.log_emp_erp_off_count):
                (emp_list, emp_pin) = getEmpOfOnOrOff(isOn = False)
                emp_new_list = list(set(emp_pin) - set(getList('emp_list_off')))
                for emp in emp_list:
                    if emp.PIN in emp_new_list:
                        empERP = Employee_ERP.objects.get(PIN = emp.PIN)
                        empERP.rEmployState = 30
                        empERP.offday = now
                        empERP.erp_date = now
                        empERP.operation = 0
                        empERP.is_pass = 0
                        empERP.save(force_update = True)
                        continue
                
                setFile('emp_list', emp_new_list)
                setFile('emp_list_off', emp_new_list)
            
            if int(empOffCount) < int(erp_log.log_emp_zk_off_count):
                (emp_list_off, emp_pin_off) = getEmpOfOnOrOff(isOn = False)
                emp_rt_list = list(set(getList('emp_list_off')) - set(emp_pin_off))
                (emp_list_rt, emp_pin_rt) = getEmpOfRT()
                for emp in emp_list_rt:
                    empERP = Employee_ERP.objects.get(PIN = emp.PIN)
                    empERP.rEmployState = 10
                    empERP.offday = None
                    empERP.erp_date = now
                    empERP.Hiredday = now
                    empERP.operation = 2
                    empERP.is_pass = 0
                    empERP.save(force_update = True)
                
                setFile('emp_list', emp_rt_list)
                setFile('emp_list_off', emp_pin_off, isNull = True)
            
            setLogERP(deptCount = deptCount, empOnCount = empOnCount, empOffCount = empOffCount, empOfMaxID = empOfMaxID, isFrist = False, logStr = 'dept sync :', doAction = 2)
        else:
            getDeptOfERP(isFrist = True)
            getEmpOfERP(isFrist = True)
            setLogERP(deptCount = deptCount, empOnCount = empOnCount, empOffCount = empOffCount, empOfMaxID = empOfMaxID, isFrist = True, logStr = 'frist sync :', doAction = 0)
    except Exception:
        e = None
        print_exc()


action = ((0, 'OFF Emp'), (1, 'ADD Emp'), (2, 'RT Emp'), (3, 'ADD Department'), (4, 'INFO SYCN ALL DATA EMP'))

def setLogFromERP(str = '', doAction = 4):
    startStr = 'FROM ERP TABLE :' + action[doAction][1]
    logstr = startStr + str
    set_log(logstr)


def setLogToZK(str = '', doAction = 4):
    startStr = 'TO ZKECO TABLE :' + action[doAction][1]
    logstr = startStr + str
    print 'log:' + logstr
    set_log(logstr)


def setLogERP(deptCount = 0, empOnCount = 0, empOffCount = 0, empOfMaxID = 0, isFrist = None, logStr = '', doAction = 0):
    time_stamp = get_timestamp(now = datetime.datetime.now())
    zk_on_count = Employee_ERP.objects.filter(rEmployState = 10).count()
    zk_off_count = Employee_ERP.objects.filter(rEmployState = 30).count()
    zk_dept_count = Department_ERP.objects.all().count()
    dict_log = {
        'erp_on': empOnCount,
        'erp_off': empOffCount,
        'erp_dept': deptCount,
        'zk_on': zk_on_count,
        'zk_off': zk_off_count,
        'zk_dept': zk_dept_count }
    if isFrist:
        ERP_LOG(log_dept_erp_count = deptCount, log_emp_pin = empOfMaxID, log_emp_erp_on_count = empOnCount, log_emp_erp_off_count = empOffCount, log_emp_zk_on_count = zk_on_count, log_emp_zk_off_count = zk_off_count, log_dept_zk_count = zk_dept_count, is_frist = 0, log_stamp = time_stamp).save()
        log_str = 'frist sycn :' + repr(dict_log)
        q_server.set_to_file('erp_frist', 'True')
    else:
        erpLog = ERP_LOG.objects.get(log_flat = 'log')
        erpLog.log_emp_pin = empOfMaxID
        erpLog.log_emp_erp_on_count = empOnCount
        erpLog.log_emp_erp_off_count = empOffCount
        erpLog.log_dept_erp_count = deptCount
        erpLog.log_emp_zk_on_count = zk_on_count
        erpLog.log_emp_zk_off_count = zk_off_count
        erpLog.log_dept_zk_count = zk_dept_count
        erpLog.is_frist = doAction
        erpLog.log_stamp = time_stamp
        erpLog.save(force_update = True)
        log_str = logStr + repr(dict_log)
    set_log(log_str)


def getDeptOfERP(isFrist = None):
    (dept_erp_list, dept_erp_code) = getAllDept()
    if isFrist:
        deptList = []
        for dept in dept_erp_list:
            if len(dept.code) and len(dept.name):
                now = datetime.datetime.now()
                deptListOld = getList('dept_list')
                if dept.code in deptListOld:
                    continue
                
                Department_ERP(code = dept.code, name = dept.name, erp_date = now).save()
                deptList.append(dept.code)
                setFile('dept_list', deptList)
                continue
        
        setLogFromERP(str(dept_erp_code), 3)
    


def getEmpOfERP(isFrist = None):
    now = datetime.datetime.now()
    if isFrist:
        (emp_list, emp_pin) = getEmpOfOnOrOff(isOn = True)
        for emp_on in emp_list:
            _emp = []
            if len(emp_on.PIN) and len(emp_on.DeptCode):
                Employee_ERP(PIN = emp_on.PIN, EName = emp_on.EName, DeptCode = emp_on.DeptCode, ruzhilaiyuan = emp_on.ruzhilaiyuan, rEmployState = emp_on.rEmployState, Hiredday = now, erp_date = now, operation = 1).save()
                _emp.append(emp_on.PIN)
                setFile('emp_list', _emp)
                continue
            continue
        
        (emp_list_off, emp_pin_off) = getEmpOfOnOrOff(isOn = False)
        for emp_off in emp_list_off:
            _emp_off = []
            if len(emp_off.PIN) and len(emp_off.DeptCode):
                Employee_ERP(PIN = emp_off.PIN, EName = emp_off.EName, DeptCode = emp_off.DeptCode, offday = now, erp_date = now, ruzhilaiyuan = emp_off.ruzhilaiyuan, rEmployState = emp_off.rEmployState, operation = 0).save()
                _emp_off.append(emp_off.PIN)
                setFile('emp_list', _emp_off)
                setFile('emp_list_off', _emp_off)
                continue
            continue
        
    
    setLogFromERP(str(getList('emp_list')), 1)
    setLogFromERP(str(getList('emp_list_off')), 0)


def dataToZK():
    get_dept_list = getList('dept_list')
    get_emp_list = getList('emp_list')
    if not len(get_dept_list) or True:
        pass
    isDept = False
    if not len(get_emp_list) or True:
        pass
    isEmp = False
    now = datetime.datetime.now()
    erp_log = ERP_LOG.objects.get(log_flat = 'log')
    doDept = 0
    doEmp = 0
    if isDept:
        
        try:
            for deptCode in get_dept_list:
                dept = Department_ERP.objects.get(code = deptCode)
                Department(code = deptCode, name = dept.name).save()
                dept.is_pass = 1
                dept.zk_date = now
                dept.save()
            
            doDept = 1
            setFile('dept_list_bak', get_dept_list)
            setFile('dept_list', new_item = [], isNull = True)
            setLogToZK(str(get_dept_list), 3)
        except Exception:
            e = None
        

    if isEmp:
        is_exist = eval(q_server.get_from_file('erp_frist'))
        if is_exist:
            q_server.set_to_file('erp_frist', 'False')
            getOffEmp = getList('emp_list_off')
            for e in getOffEmp:
                empOff = Employee_ERP.objects.get(PIN = e)
                deptObj = Department.objects.get(code = empOff.DeptCode)
                Employee(PIN = empOff.PIN, DeptID = deptObj, EName = empOff.EName).save()
            
        
        for pin in get_emp_list:
            empERP = Employee_ERP.objects.get(PIN = pin)
            if int(empERP.operation) == 1:
                deptObj = Department.objects.get(code = empERP.DeptCode)
                Employee(PIN = empERP.PIN, DeptID = deptObj, EName = empERP.EName).save()
            elif int(empERP.operation) == 2:
                emp = Employee.all_objects.get(PIN = format_pin(empERP.PIN))
                leaveEmp = LeaveLog.objects.get(UserID = emp)
                leaveRestoreEmp = leaveEmp.OpRestoreEmpLeave(leaveEmp)
                leaveRestoreEmp.action()
            elif int(empERP.operation) == 0:
                offEmp = Employee.objects.get(PIN = format_pin(empERP.PIN))
                operationObj = offEmp.OpLeave(offEmp)
                leavedate = now
                leavetype = 3
                isReturnTools = 1
                isReturnClothes = 1
                isReturnCard = 1
                closeAtt = 1
                closeAcc = 1
                isblacklist = 0
                reason = ''
                operationObj.action(leavedate, leavetype, reason, isReturnTools, isReturnClothes, isReturnCard, closeAtt, isblacklist, closeAcc)
            
            doEmp = 2
            empERP.zk_date = now
            empERP.is_pass = 1
            empERP.save()
        
        setFile('emp_list_bak', get_emp_list)
        setFile('emp_list', new_item = [], isNull = True)
        setLogToZK(str(get_emp_list), 4)
    
    erp_log.is_frist = doDept + doEmp
    erp_log.save()


def fromERPToFile():
    checkERPOfEmpData()
    checkERPOfDeptData()
    is_exist = q_server.get_from_file('erp_frist')
    if not is_exist:
        q_server.set_to_file('erp_frist', 'True')
    


def getDeptObject(code):
    deptObject = None
    if cache.get('ZKDept'):
        deptList = cache.get('ZKDept')
        for dept in deptList:
            if dept[0] == code:
                deptObject = dept[1]
                break
                continue
        
    else:
        deptObject = Department.objects.get(code = code)
    if deptObject is None:
        deptObject = Department.objects.get(code = code)
    
    return deptObject


def checkDataToZK():
    import copy as copy
    import sys as sys
    dept_list = getList('new_dept')
    on_list = getList('on_list')
    off_list = getList('off_list')
    rt_list = getList('rt_list')
    is_exist = eval(q_server.get_from_file('erp_frist'))
    now = datetime.datetime.now()
    tmp_dept_list = copy.deepcopy(dept_list)
    tmp_on_list = copy.deepcopy(on_list)
    tmp_off_list = copy.deepcopy(off_list)
    tmp_rt_list = copy.deepcopy(rt_list)
    if len(dept_list) > 0:
        deptObjectList = []
        for dept in dept_list:
            
            try:
                d = Department(code = dept[0], name = dept[1])
                d.save()
                deptObjectList.append((d.code, d))
                print 'deptObjectList==', deptObjectList
                tmp_dept_list.remove(dept)
                setFile('new_dept', new_item = tmp_dept_list, isNull = True)
            continue
            except Exception:
                e = None
                dr = Department_ERP(code = dept[0], name = dept[0], erp_date = now)
                dr.save()
                continue
                continue
            

        
        cache.set('ZKDept', deptObjectList)
    
    print 'is_exist==', is_exist
    if is_exist:
        if len(off_list) > 0:
            empObjectList = []
            for emp in off_list:
                
                try:
                    deptObj = getDeptObject(emp[2])
                    print 'add  off_list to zk emp===', emp
                    e = Employee(PIN = emp[0], DeptID = deptObj, EName = emp[1], Card = emp[5])
                    e.save()
                    empObjectList.append(e)
                continue
                except Exception:
                    e = None
                    Employee_ERP(PIN = emp[0], DeptCode = emp[2], EName = emp[1], rEmployState = emp[3], ruzhilaiyuan = emp[4], erp_date = now).save()
                    print_exc()
                    errFile = open('tmp/TOZKError.log', 'wb')
                    sys.stderr = errFile
                    errFile.close()
                    continue
                    continue
                

            
            cache.set('ZKEmp', empObjectList)
            q_server.set_to_file('erp_frist', 'False')
        
    
    if len(on_list) > 0:
        for emp in on_list:
            
            try:
                rt_emp = Employee.all_objects.filter(PIN = emp[0])
                if len(rt_emp) > 0:
                    leaveEmp = LeaveLog.objects.get(UserID = rt_emp[0])
                    leaveRestoreEmp = leaveEmp.OpRestoreEmpLeave(leaveEmp)
                    leaveRestoreEmp.action()
                    print 'leaveEmp==', leaveEmp
                else:
                    deptObj = getDeptObject(emp[2])
                    print 'add on_list to zk emp===', emp
                    Employee(PIN = emp[0], DeptID = deptObj, EName = emp[1], Card = emp[5]).save()
                tmp_on_list.remove(emp)
                print 'add on - tmp_on_list=', tmp_on_list
                setFile('on_list', new_item = tmp_on_list, isNull = True)
            continue
            except Exception:
                e = None
                print_exc()
                continue
                continue
            

        
    
    if len(off_list) > 0:
        empObjectList = []
        if is_exist:
            empObjectList = cache.get('ZKEmp')
        else:
            for emp in off_list:
                print 'add off_list to zk emp===', emp
                e = Employee.objects.get(PIN = format_pin(emp[0]))
                empObjectList.append(e)
            
        if empObjectList is None or len(empObjectList) == 0:
            if empObjectList is None:
                empObjectList = []
            
            for emp in off_list:
                print 'too add off_list to zk emp===', emp
                e = Employee.objects.get(PIN = format_pin(emp[0]))
                empObjectList.append(e)
            
        
        for emp in empObjectList:
            
            try:
                operationObj = emp.OpLeave(emp)
                leavedate = now
                leavetype = 3
                isReturnTools = 1
                isReturnClothes = 1
                isReturnCard = 1
                closeAtt = 1
                closeAcc = 1
                isblacklist = 0
                reason = ''
                operationObj.action(leavedate, leavetype, reason, isReturnTools, isReturnClothes, isReturnCard, closeAtt, isblacklist, closeAcc)
            continue
            except Exception:
                e = None
                print_exc()
                continue
                continue
            

        
        setFile('off_list', new_item = [], isNull = True)
    
    if len(rt_list) > 0:
        for e in rt_list:
            print 'add rt_list to zk emp===', e
            
            try:
                emp = Employee.all_objects.get(PIN = format_pin(e[0]))
                leaveEmp = LeaveLog.objects.get(UserID = emp)
                leaveRestoreEmp = leaveEmp.OpRestoreEmpLeave(leaveEmp)
                leaveRestoreEmp.action()
                tmp_rt_list.remove(e)
                setFile('rt_list', new_item = tmp_rt_list, isNull = True)
            continue
            except Exception:
                ex = None
                continue
                continue
            

        
    


def fromFileToZK():
    checkDataToZK()

from apscheduler.scheduler import Scheduler
scheduler = Scheduler()
scheduler.start()

def schedFunc():
    now = datetime.datetime.now()
    fromERPToFile()
    fromFileToZK()

if len(scheduler.get_jobs()) == 0:
    job = scheduler.add_cron_job(schedFunc, hour = '16')
    print 'sync job=1111=', job


def getSum(erp_emp_message_list = None):
    u'''
        \xe5\xb0\x86\xe4\xba\xba\xe5\x91\x98\xe6\x95\xb0\xe7\xbb\x9f\xe8\xae\xa1
    '''
    LeaveLog = LeaveLog
    import mysite.personnel.models.model_leave
    Employee = Employee
    import mysite.personnel.models.model_emp
    emp_list = []
    on_list = []
    off_list = []
    if erp_emp_message_list is None:
        emp_list = eval(q_server.get_from_file('erp_emp_message_list'))
        (on_list, off_list) = getErpEmpList()
    else:
        emp_list = erp_emp_message_list
        (on_list, off_list) = getErpEmpList(isNew = True, newList = erp_emp_message_list)
    all_emp = Employee.all_objects.all().values_list('PIN')
    on_emp = Employee.objects.all().values_list('PIN')
    off_emp = list(set(all_emp) - set(on_emp))
    emp_count_list = len(emp_list)
    on_count_list = len(on_list)
    off_count_list = len(off_list)
    all_emp_count = len(all_emp)
    on_emp_count = len(on_emp)
    off_emp_count = len(off_emp)
    len_str = '%s === %s === %s === %s === %s === %s' % (emp_count_list, on_count_list, off_count_list, all_emp_count, on_emp_count, off_emp_count)
    set_log(len_str)
    exception_on_list = []
    exception_off_list = []
    excepttion_all_list = []
    on_emp_list = []
    for emp in on_emp:
        on_emp_list.append(emp[0])
    
    off_emp_list = []
    for emp in off_emp:
        off_emp_list.append(emp[0])
    
    all_emp_list = []
    for emp in all_emp:
        all_emp_list.append(emp[0])
    
    if on_count_list - on_emp_count:
        for on in on_list:
            if on[0] in on_emp_list:
                continue
                continue
            exception_on_list.append(on)
        
    
    if off_count_list - off_emp_count:
        for off in off_list:
            if off[0] in off_emp_list:
                continue
                continue
            exception_off_list.append(off)
        
    
    if emp_count_list - all_emp_count:
        for all in emp_list:
            if all[0] in all_emp_list:
                continue
                continue
            excepttion_all_list.append(all)
        
    
    if len(exception_off_list) > 0:
        setFile('off_list', new_item = exception_off_list, isNull = True)
        q_server.set_to_file('erp_emp_message_list', repr(erp_emp_message_list))
    
    if len(exception_on_list) > 0:
        setFile('on_list', new_item = exception_on_list, isNull = True)
        q_server.set_to_file('erp_emp_message_list', repr(erp_emp_message_list))
    

