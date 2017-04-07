#!/usr/bin/python
# -*- coding: utf-8 -*-
from util import Util 
import pandas as pd

web_task_map={'601.htm':'ticket purchase-multiple choice',
              '602.htm':'ticket purchase-price threshold',
              '701.htm':'measure the tent',
              '801.htm':'tent assignment',
              '603.htm':'tour plan'}

stu_ids=['stu1','stu2','stu3','stu4','stu5','stu6','stu7','stu8','stu9','stu10','stu11','stu12','stu13','stu15','stu16','stu17','stu18','stu20',
         'stu21','stu22','stu23','stu24','stu25','stu27','stu28','stu29','stu32','stu35','stu37','stu38','stu39','stu40']

class PB:
    def __init__(self, verb, obj, timestamp):
        self.verb = verb
        self.obj = obj
        self.timestamp = timestamp
        
class Student:
    def __init__(self, id):
        self.id = id
        self.pbs = []
        self.serlized_pbs = ''
        
def process_behavior(data):
    pbs = []
    in_task = False;
    for i in range(0,len(data)):
        result = task_or_lib(data[i], web_task_map)
        if result == '':
            continue
        verb = Util.parse_verb_id(data[i]['verb']['id'])
        obj_cn = data[i]['object']['definition']['name']['zh_CN']
        timestamp = data[i]['timestamp']
        if result == 'lib':
            obj = '资料“' + obj_cn + '”'
        else:
            obj = '“' + obj_cn + '”'
            
        #print(verb + obj + ':'  + timestamp)
        pb = PB(verb, obj, timestamp)
        pbs.append(pb)
        
    filtered_pbs = filter_verbs(pbs)
    
    return filtered_pbs
            
def task_or_lib(json, web_task_map):
    object = json['object']['id']
    if 'liberary' in object:
        return 'lib'
    elif web_task_map.get(get_obj_id(object)):
        return 'task'
    else:
        return ''

def get_obj_id(object):

    obj = object[object.rindex('/')+1:]
    
    if object.__contains__('#'):
        obj = obj.split('#')[0] #why1not0 

    if obj.__contains__('?'):
        obj = obj.split('?')[0]
    
    return obj

def filter_verbs(pbs):
    filtered = []
    for i, pb in enumerate(pbs):
        if pb.verb == 'scored':
            continue
        elif (pb.verb == 'completed') & (pbs[i-1].verb == 'scored'):
            continue
        filtered.append(pb)  
        
    return filtered      

def serialize_pbs(pbs):
    str = ''
    for pb in pbs:  
        str += pb.verb + pb.obj + ':' + pb.timestamp + '->'      
    
    str = str[:-2]
    
    return str

def get_title():
    title= ['id','process behavior']
    return title
        
def main():
    data = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs = process_behavior(Util.data_read('20170328/' + id))
        stu.serialized_pbs = serialize_pbs(stu.pbs)
        print(stu.id + '——' + stu.serialized_pbs)
        stu_output = [stu.id, stu.serialized_pbs]
        data.append(stu_output)
        
    d = pd.DataFrame(data = data, columns = get_title())
    d.to_csv('process_behavior.csv')
        
if __name__ == "__main__": main()