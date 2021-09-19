#!/usr/bin/python
#incoding = utf-8

class SchoolMember:
    '''represents any school member.'''
    def __init__(self,name,age) -> None:
        self.name=name
        self.age=age
        print("init school member! %s",self.name)
    def tell(self):
        '''Tell me details.'''
        print('Name:%s Age: %s',self.name,self.age)

class Teacher(SchoolMember):
    def __init__(self,name,age,salary):
        SchoolMember.__init__(self,name,age)
        self.salary=salary
        print('Initialized Teacher')
    def tell(self):
        SchoolMember.tell()
t=Teacher('Mrs.sheloy',40,7500)
t.tell