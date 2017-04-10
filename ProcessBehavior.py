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

task_libs = {'601.htm': ['601.json']}

pb_type = dict()

class PB:
    def __init__(self, verb, obj_id, obj_cn, obj_type, timestamp):
        self.verb = verb
        self.obj_id = obj_id
        self.obj_cn = obj_cn
        self.obj_type = obj_type
        self.timestamp = timestamp
        
class Student:
    def __init__(self, id):
        self.id = id
        self.pbs = []
        self.serlized_pbs = ''
        
def process_behavior(data):
    pbs = []
    for i in range(0,len(data)):
        type = task_or_lib(data[i], web_task_map)
        if type == '':
            continue
        verb = Util.parse_verb_id(data[i]['verb']['id'])
        obj_id = get_obj_id(data[i]['object']['id'])
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp']
        
        #print(verb + obj + ':'  + timestamp)
        pb = PB(verb, obj_id, obj_cn, type, timestamp)
        pbs.append(pb)
        
    filtered_pbs = filter_verbs(pbs)
    
    #differentiate lib
    in_task = False
    task_id = ''
    for i, f_pb in enumerate(filtered_pbs):
        if (f_pb.obj_type == 'lib') & (in_task == False):
            f_pb.obj_cn = '资料' + f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == False) & (f_pb.verb == 'launched'):
            in_task = True
            task_id = f_pb.obj_id
        elif (f_pb.obj_type == 'lib') & (in_task == True):
            if lib_usefulness(task_id, f_pb.obj_id):
                f_pb.obj_cn = '有关资料' + f_pb.obj_cn
            else:
                f_pb.obj_cn = '无关资料' + f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == True) & (f_pb.verb == 'completed'):
            in_task = True
            
    return filtered_pbs

def lib_usefulness(task_id, lib_id):
    libs = task_libs.get(task_id)
    if libs != None:
        for lib in libs:
            if lib == lib_id:
                return True
        return False
    
    return None
      
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
        str += pb.verb + pb.obj_cn + ':' + pb.timestamp + '->'      
    
    str = str[:-2]
    
    return str

def get_title():
    title= ['id','process behavior']
    return title

def pb_type_map(pbs):   
    for pb in pbs:
        key = pb.verb + ' ' + pb.obj_id
        if key in pb_type:
            continue
        else:
            pb_type[key] = pb.verb + ' ' + pb.obj_cn

def print_dict(dict):
    file = open('process_behavior_type.txt', 'w')
    for key, value in dict.items():
        file.write(value + '\n')
        print (value)
    print(len(pb_type))  
    file.close()
           
def main():
    data = []
    
    for id in stu_ids:
        stu = Student(id)
        stu.pbs = process_behavior(Util.data_read('20170328/' + id))
        stu.serialized_pbs = serialize_pbs(stu.pbs)
        #print(stu.id + '——' + stu.serialized_pbs)
        stu_output = [stu.id, stu.serialized_pbs]
        data.append(stu_output)
        pb_type_map(stu.pbs)
        
    #d = pd.DataFrame(data = data, columns = get_title())
    #d.to_csv('process_behavior1.csv')
    print_dict(pb_type)
        
if __name__ == "__main__": main()