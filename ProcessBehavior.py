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
             '603.htm': ['607.json', '619.json']}

pb_type = dict()
task_score = dict()
time_list = []

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
            print('资料' + f_pb.obj_cn + ':' + f_pb.obj_id)
            f_pb.obj_id = 'task_out_lib'
            f_pb.obj_cn = '资料' #+ f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == False) & (f_pb.verb == 'launched'):
            in_task = True
            task_id = f_pb.obj_id
        elif (f_pb.obj_type == 'lib') & (in_task == True):
            if lib_usefulness(task_id, f_pb.obj_id):
                print('有关资料' + f_pb.obj_cn + ':' + f_pb.obj_id)
                f_pb.obj_id = 'relevant_lib'
                f_pb.obj_cn = '有关资料' #+ f_pb.obj_cn
            else:
                print('无关资料' + f_pb.obj_cn + ':' + f_pb.obj_id)
                f_pb.obj_id = 'irrelevant_lib'
                f_pb.obj_cn = '无关资料' #+ f_pb.obj_cn
        elif (f_pb.obj_type == 'task') & (in_task == True) & (f_pb.verb == 'completed'):
            in_task = False
        
        elif (f_pb.obj_type == 'task') & (in_task == True) & (f_pb.verb != 'completed'):
            obj, specify_obj = get_former_latter(f_pb.obj_id, '#')
            if specify_obj != None:   
                if f_pb.verb == 'drag':
                    if (specify_obj != 'women') & (specify_obj != 'man') & (specify_obj != 'boy') & (specify_obj != 'girl'):
                        specify_obj = 'out'
                    else:
                        specify_obj = 'in'
                        
                f_pb.obj_id = obj + ' ' + specify_obj
                f_pb.obj_cn = f_pb.obj_cn + specify_obj

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

def serialize_pbs(pbs, segments):
    str = ''
    for i, pb in enumerate(pbs):  
        if (pb.obj_type == 'lib') & (pb.verb == 'exited'):
            continue
        elif (pb.obj_type == 'lib') & (pb.verb == 'launched'):
            state = get_duration_state(pbs, i, segments)
            str += pb.verb + pb.obj_cn + ',' + state + '->'
            continue
            
        if (pb.valid != None) & (pb.correct != None):
            str += pb.verb + pb.obj_cn + ',' + pb.valid + ',' + pb.correct + '->' 
        elif (pb.valid != None) & (pb.correct == None):
            str += pb.verb + pb.obj_cn + ',' + pb.valid + '->' 
        elif (pb.valid == None) & (pb.correct != None):
            str += pb.verb + pb.obj_cn + ',' + pb.correct + '->'
        else:
            str += pb.verb + pb.obj_cn + '->' 
    
    str = str[:-2]
    
    return str

def pb_type_map(pbs):   
    for pb in pbs:
        key = pb.verb + pb.obj_cn
        if (pb.valid != None) & (pb.correct != None):
            key += ',' + pb.valid + ',' + pb.correct
        elif (pb.valid != None) & (pb.correct == None):
            key += ',' + pb.valid
        elif (pb.valid == None) & (pb.correct != None):
            key += ',' + pb.correct
            
        if key in pb_type:
            pb_type[key] += 1
        else:
            pb_type[key] = 1
           
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

def get_duration_state(pbs, i, segments):
    short = segments[0]
    long = segments[1]
    second = get_duration(pbs, i)
    if second <= short:
        return 'short'
    elif (short < second) & (second < long):
        return 'mid'
    elif second >= long:
        return 'long'

def get_duration(pbs, i):           
    pb = pbs[i]
    begin_time = datetime.strptime(pb.timestamp, '%Y-%m-%dT%H:%M:%S')
    pb_next = pbs[i+1]
    if (pb_next.obj_type == 'lib') & (pb.verb == 'favorite'):#还是属于launch状态，肯定会有下一个，但又会有重复favourite
        end_time = datetime.strptime(pbs[i+2].timestamp, '%Y-%m-%dT%H:%M:%S')
    else:
        end_time = datetime.strptime(pb_next.timestamp, '%Y-%m-%dT%H:%M:%S')
    time = end_time - begin_time
    return time.total_seconds()    
    
def get_duration_segment(durations):
    size = len(durations)
    q = int(size / 3)
    short = 0
    long = 0
    s = sorted(durations)
    for i, duration in enumerate(s):
        if i == q:  
            short = duration
        elif i == 2*q:  
            long = duration                   
    return [short, long]

def tidy_stu_lib(stus, segments):
    data = []
    for stu in stus:
        serialized_pbs = serialize_pbs(stu.pbs, segments)
        output = [stu.id, serialized_pbs]
        data.append(output)  
    return data  
    
def to_csv(data, title, output_file_name):
    d = pd.DataFrame(data = data, columns = title)
    d.to_csv(output_file_name)
            
def main():
    task_score_file = open('task_score.txt', 'w')
    pb_type_file = open('process_behavior_type5.txt', 'w')
    time_file = open('time_file.txt', 'w')
    stu_list = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs = process_behavior(Util.data_read('20170328/' + id))
        pb_type_map(stu.pbs)
        stu.task_score = task_score
        stu_list.append(stu)
        print_dict(task_score_file, task_score, True, stu.id)
    print_dict(pb_type_file, pb_type, True, None)
    pb_type_file.close()
    task_score_file.close()
    time_file.close()
    to_csv(time_list, ['duration'], 'lib_reading_duration.csv')
    segments = get_duration_segment(time_list)
    pbs_output = tidy_stu_lib(stu_list, segments)
    to_csv(pbs_output, ['id','process behavior'], 'process_behavior4.csv')
    
        
if __name__ == "__main__": main()