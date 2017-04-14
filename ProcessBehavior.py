#!/usr/bin/python
# -*- coding: utf-8 -*-
from util import Util 
import pandas as pd
from datetime import datetime

web_task_map={'601.htm':'ticket purchase-multiple choice',
              '602.htm':'ticket purchase-price threshold',
              '701.htm':'measure the tent',
              '801.htm':'tent assignment',
              '603.htm':'tour plan'}

stu_ids=['stu1','stu2','stu3','stu4','stu5','stu6','stu7','stu8','stu9','stu10','stu11','stu12','stu13','stu15','stu16','stu17','stu18','stu20',
         'stu21','stu22','stu23','stu24','stu25','stu27','stu28','stu29','stu32','stu35','stu37','stu38','stu39','stu40']

task_libs = {'601.htm': ['601.json'],
             '701.htm': ['603.json'],
             '603.htm': ['607.json']}

pb_type = dict()
task_score = dict()

class PB:
    def __init__(self, verb, obj_id, obj_cn, obj_type, timestamp, valid, correct):
        self.verb = verb
        self.obj_id = obj_id
        self.obj_cn = obj_cn
        self.obj_type = obj_type
        self.timestamp = timestamp
        self.valid = valid
        self.correct = correct
        self.time_interval = []
        
class Student:
    def __init__(self, id):
        self.id = id
        self.pbs = []
        self.serlized_pbs = ''
        self.task_score = dict()

def get_score(json):
    obj, specify_obj = get_former_latter(get_obj_id(json['object']['id']), '#')
    score = json['result']['response'].get('score')  
    if web_task_map.get(obj) != None:
        if score != None:
            task_score[obj] = score
        else:
            task_score[obj] = 'null'
            
def process_behavior(data):
    pbs = []
    for i in range(0,len(data)):
        type = task_or_lib(data[i], web_task_map)
        if type == '':
            continue
        
        verb, valid, correct = parse_verb_click(data[i])
        
        obj = data[i]['object']['id']
        if obj.__contains__('statistic'):
            get_score(data[i])
        obj_id = get_obj_id(obj)
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp']
        
        #print(verb + obj + ':'  + timestamp)
        pb = PB(verb, obj_id, obj_cn, type, timestamp[:-6], valid, correct)
        pbs.append(pb)
    
    #filter scored    
    filtered_pbs = filter_verbs(pbs)
    
    specify_pbs = specify_obj(filtered_pbs)
                
    return specify_pbs

def parse_verb_click(json):
    v = get_verb(json['verb']['id'])
    obj = get_obj_id(json['object']['id'])
    #deal with click of 701、601htm 
    if v.__contains__('click'): 
        list = v.split(',')
        v = list[0]
        if obj.__contains__('701.htm'):
            if len(list) == 4:
                valid = list[1]
                correct = list[2]
                return v, valid, correct 
            elif len(list) == 3:
                valid = list[2]
                return v, valid, None
        elif obj.__contains__('601.htm'):
            correct = list[2]
            return v, None, correct
    #verb != click    
    if v.__contains__(','):
        return v[:v.index(',')], None, None
    return v, None, None
    
def specify_obj(filtered_pbs):
    #differentiate lib, specify obj
    in_task = False
    task_id = ''
    for i, f_pb in enumerate(filtered_pbs):
        if (f_pb.obj_type == 'lib') & (in_task == False):
            f_pb.obj_id = 'task_out_lib'
            f_pb.obj_cn = '资料' #+ f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == False) & (f_pb.verb == 'launched'):
            in_task = True
            task_id = f_pb.obj_id
        elif (f_pb.obj_type == 'lib') & (in_task == True):
            if lib_usefulness(task_id, f_pb.obj_id):
                f_pb.obj_id = 'relevant_lib'
                f_pb.obj_cn = '有关资料' #+ f_pb.obj_cn
            else:
                f_pb.obj_id = 'irrelevant_lib'
                f_pb.obj_cn = '无关资料' #+ f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == True) & (f_pb.verb == 'completed'):
            in_task = True
        
        elif (f_pb.obj_type == 'task') & (in_task == True) & (f_pb.verb != 'completed'):
            obj, specify_obj = get_former_latter(f_pb.obj_id, '#')
            if specify_obj != None:   
                if f_pb.verb == 'drag':
                    if (specify_obj != 'women') & (specify_obj != 'man') & (specify_obj != 'boy') & (specify_obj != 'girl'):
                        specify_obj = 'out'
                    else:
                        specify_obj = 'in'
                        
                f_pb.obj_id = obj + ' ' + specify_obj
                f_pb.obj_cn = f_pb.obj_cn + ' ' + specify_obj

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
    
    obj_id = get_obj_id(object)
    obj, specify_obj = get_former_latter(obj_id, '#')
        
    if web_task_map.get(obj):
        return 'task'
    
    return ''

def get_former_latter(str, sign):
    if str.__contains__(sign):
        former = str.split(sign)[0]
        latter = str.split(sign)[1]
        return former, latter
    
    return str, None
 
def get_verb(s):
    s=s[s.rindex('/')+1:]
    return s   
    
def get_obj_id(object):

    obj = object[object.rindex('/')+1:]
    
    if object.__contains__('#'):
        obj = obj#.split('#')[0]

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
        if (pb.valid != None) & (pb.correct != None):
            str += pb.verb + pb.obj_cn + ',' + pb.valid + ',' + pb.correct + ':' + pb.timestamp + '->' 
        elif (pb.valid != None) & (pb.correct == None):
            str += pb.verb + pb.obj_cn + ',' + pb.valid + ':' + pb.timestamp + '->' 
        elif (pb.valid == None) & (pb.correct != None):
            str += pb.verb + pb.obj_cn + ',' + pb.correct + ':' + pb.timestamp + '->'
        else:
            str += pb.verb + pb.obj_cn + ':' + pb.timestamp + '->' 
    
    str = str[:-2]
    
    return str

def pb_type_map(pbs):   
    for pb in pbs:
        if (pb.valid != None) & (pb.correct != None):
            key = pb.verb + ' ' + pb.obj_id + ' ' + pb.valid + ' ' + pb.correct
            if key in pb_type:
                continue
            else:
                pb_type[key] = pb.verb + ' ' + pb.obj_cn + ' ' + pb.valid + ' ' + pb.correct
        elif (pb.valid != None) & (pb.correct == None):
            key = pb.verb + ' ' + pb.obj_id + ' ' + pb.valid
            if key in pb_type:
                continue
            else:
                pb_type[key] = pb.verb + ' ' + pb.obj_cn + ' ' + pb.valid
        elif (pb.valid == None) & (pb.correct != None):
            key = pb.verb + ' ' + pb.obj_id + ' ' + pb.correct
            if key in pb_type:
                continue
            else:
                pb_type[key] = pb.verb + ' ' + pb.obj_cn + ' ' + pb.correct
        else:
            key = pb.verb + ' ' + pb.obj_id
            if key in pb_type:
                continue
            else:
                pb_type[key] = pb.verb + ' ' + pb.obj_cn

def print_dict(file, dict, has_key, stu_id):
    
    if stu_id != None:
        file.write(stu_id + '\n')
    for key, value in dict.items():
        if has_key:
            file.write(key + ':' + str(value) + '\n')
            #print (key + ':' + str(value))
        else:
            file.write(str(value) + '\n')
            #print (str(value))
    #print(len(pb_type))  
def print_time_interval(file, list, stu_id):
    if stu_id != None:
        file.write(stu_id + '\n')
    for element in list:
        file.write(str(element[0]) + ':' + str(element[1]))
    file.write('\n')
        
def get_time_interval(pbs):
    list = []
    size = len(pbs)
    for i, pb in enumerate(pbs):
        if i < size - 1:
            if (pb.obj_type == 'lib') & (pb.verb == 'launched'):
                pb_next = pbs[i+1]
                begin_time = datetime.strptime(pb.timestamp, '%Y-%m-%dT%H:%M:%S')
                end_time = datetime.strptime(pb_next.timestamp, '%Y-%m-%dT%H:%M:%S')
                time = end_time - begin_time
                #element = {'obj_id' : pb.obj_id, 'obj_cn' : pb.obj_cn, 'time' : time}
                element = [pb.obj_cn, time.total_seconds()]
                list.append(element)
    #to_csv(list, ['资料', '时长（秒）'], 'time_file.csv')
    return list    
    
def to_csv(data, title, output_file_name):
    d = pd.DataFrame(data = data, columns = title)
    d.to_csv(output_file_name)
                    
def main():
    data = []
    task_score_file = open('task_score.txt', 'w')
    pb_type_file = open('process_behavior_type3.txt', 'w')
    time_file = open('time_file.txt', 'w')
    for id in stu_ids:
        stu = Student(id)
        stu.pbs = process_behavior(Util.data_read('20170328/' + id))
        stu.serialized_pbs = serialize_pbs(stu.pbs)
        #print(stu.id + '——' + stu.serialized_pbs)
        stu_output = [stu.id, stu.serialized_pbs]
        data.append(stu_output)
        pb_type_map(stu.pbs)
        stu.task_score = task_score
        stu.time_interval = get_time_interval(stu.pbs)
        print_time_interval(time_file, stu.time_interval, stu.id)
        #print_dict(task_score_file, task_score, True, stu.id)
    #to_csv(data, ['id','process behavior'], 'process_behavior3.csv')
    #print_dict(pb_type_file, pb_type, False, None)
    pb_type_file.close()
    task_score_file.close()
    time_file.close()
        
if __name__ == "__main__": main()