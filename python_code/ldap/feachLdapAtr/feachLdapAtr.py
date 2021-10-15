#coding: utf-8
 
import os
import sys
import ldap
import csv

 
def login_ldap(username, password):
    try:
        print("开始执行")
        Server = "ldap://127.0.0.1：8000"
        baseDN = "dc=domainname,dc=com"
        searchScope = ldap.SCOPE_SUBTREE
        # 设置过滤属性，这里只显示cn=test的信息
         searchFilter = "sAMAccountName=" + username
        # 为用户名加上域名
         username = 'domainname\\' + username
        
        
        # None表示搜索所有属性，['cn']表示只搜索cn属性
         retrieveAttributes = None
    
        conn = ldap.initialize(Server)
        #非常重要
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.protocol_version = ldap.VERSION3
        # 这里用户名是域账号的全名例如domain/name
        print conn.simple_bind_s(username, password)
        print 'ldap connect successfully'
 
    
        #调用search方法返回结果id
        ldap_result_id = conn.search(baseDN, searchScope, searchFilter, retrieveAttributes)
        result_set = []
        print ldap_result_id
 
        print("****************")
        while 1:
            result_type, result_data = conn.result(ldap_result_id, 0)
            if(result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
 
        #print result_set
        Name,Attrs = result_set[0][0]
        if hasattr(Attrs, 'has_key') and Attrs.has_key('name'):
            print("test3")
            distinguishedName = Attrs['mail'][0]
            #distinguishedName = Attrs['name'][0]
            #distinguishedName = Attrs['displayName'][0]
            #distinguishedName = Attrs['mail'][0]
            #distinguishedName = Attrs['memberOf'][0]
            #distinguishedName = Attrs['mailNickname'][0]
            #distinguishedName = Attrs['sAMAccountName'][0]
            #distinguishedName = Attrs['distinguishedName'][0]
            #distinguishedName = Attrs['title'][0]
            #distinguishedName = Attrs['department'][0]
            #distinguishedName = Attrs['manager'][0]
            print "Login Info for user : %s" % distinguishedName
 
            print Attrs['mail'][0]
            print Attrs['name'][0]
            print Attrs['displayName'][0]
            print Attrs['memberOf'][0]
            print Attrs['sAMAccountName'][0]
            print Attrs['title'][0]
            print Attrs['department'][0]
 
 
            
            return distinguishedName
 
        else:
            print("in error")
            return None
    except ldap.LDAPError, e:
        print("out error")
        print e
        return None
    
if __name__ == "__main__":
    username = "username" # ldap中用户名
    password = "password" # ldap中密码
    
    login_ldap(username, password)
