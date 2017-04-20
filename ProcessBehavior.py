#!/usr/bin/python
# -*- coding: utf-8 -*-
from util import Util, HMM
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


task_score = dict()

class PB:
    def __init__(self, verb, obj_id, obj_cn, obj_type, timestamp, state):
        self.verb = verb
        self.obj_id = obj_id
        self.obj_cn = obj_cn
        self.obj_type = obj_type
        self.state = state
        self.timestamp = timestamp
        
class Student:
    def __init__(self, id):
        self.id = id
        self.pbs = []
        self.task_score = dict()
        self.serialized_pbs = ''

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
        
        obj = data[i]['object']['id']
        if obj.__contains__('statistic'):
            get_score(data[i])
        obj_id = get_obj_id(obj)
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp']
        
        verb, state = parse_verb_click(data[i])
        
        pb = PB(verb, obj_id, obj_cn, type, timestamp[:-6], state)
        pbs.append(pb)
    
    filtered_pbs = filter_verb_scored(pbs)
    
    specify_pbs = specify_task_obj(filtered_pbs)
            
    return specify_pbs

def parse_verb_click(json):
    v = get_verb(json['verb']['id'])
    obj = get_obj_id(json['object']['id'])
    
    state = None
    #deal with click of 701、601htm 
    if (v.__contains__('click')) & (v.__contains__(',')): 
        list = v.split(',')
        if obj.__contains__('701.htm'):
            if len(list) == 4:
                valid = list[1]
                correct = list[2]
                if (valid == '1') & (correct == '1'):
                    state = 'valid,correct'
                elif (valid == '1') & (correct == '0'):
                    state = 'valid,incorrect'
                elif (valid == '0') & (correct == '1'):
                    state = 'invalid,correct'
                elif (valid == '0') & (correct == '0'):
                    state = 'invalid,incorrect'
            elif len(list) == 3:
                correct = list[2]
                if correct == '1':
                    state = 'correct'
                else:
                    state = 'incorrect'
        elif obj.__contains__('601.htm'):
            correct = list[2]
            if correct == '1':
                state = 'correct'
            else:
                state = 'incorrect'
   
    #verb != click    
    if v.__contains__(','):
        v = v[:v.index(',')]
        
    return v, state

def differentiate_lib(pbs):
    in_task = False
    task_id = ''
    for pb in pbs:
        if (pb.obj_type == 'lib') & (in_task == False):
            #print('资料' + pb.obj_cn + ':' + pb.obj_id)
            pb.obj_id = 'task_out_lib'
            pb.obj_cn = '资料' #+ pb.obj_cn
        elif (pb.obj_type == 'task') & (in_task == False) & (pb.verb == 'launched'):
            in_task = True
            task_id = pb.obj_id
        elif (pb.obj_type == 'lib') & (in_task == True):
            if lib_usefulness(task_id, pb.obj_id):
                #print('有关资料' + pb.obj_cn + ':' + pb.obj_id)
                pb.obj_id = 'relevant_lib'
                pb.obj_cn = '有关资料' #+ pb.obj_cn
            else:
                #print('无关资料' + pb.obj_cn + ':' + pb.obj_id)
                pb.obj_id = 'irrelevant_lib'
                pb.obj_cn = '无关资料' #+ f_pb.obj_cn
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'completed'):
            in_task = False  
            
    return pbs
  
def specify_task_obj(pbs):
    
    for pb in pbs:
        if pb.obj_type == 'task':    
            obj, specify_obj = get_former_latter(pb.obj_id, '#')
            if specify_obj != None:   
                if pb.verb == 'drag':
                    if (specify_obj != 'women') & (specify_obj != 'man') & (specify_obj != 'boy') & (specify_obj != 'girl'):
                        specify_obj = 'out'
                    else:
                        specify_obj = 'in'
                        
                pb.obj_id = obj + ' ' + specify_obj
                pb.obj_cn = pb.obj_cn + specify_obj

    return pbs

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

def filter_verb_scored(pbs):
    filtered = []
    for i, pb in enumerate(pbs):
        if pb.verb == 'scored':
            continue
        elif (pb.verb == 'completed') & (pbs[i-1].verb == 'scored'):
            continue
        filtered.append(pb)  
        
    return filtered   

def clean_lib(stus, duration_list):
    duration_segments = get_duration_segment(duration_list)
    for i, stu in enumerate(stus):
        pbs1 = differentiate_lib(stu.pbs)   
        pbs2 = get_lib_state(pbs1, duration_segments)
        cleaned_pbs = filter_lib_verb_exited(pbs2)
        stus[i].pbs = cleaned_pbs
    return stus

def get_lib_state(pbs, duration_segments):
    for i, pb in enumerate(pbs):  
        if (pb.obj_type == 'lib') & (pb.verb == 'launched'):
            pb.state = get_duration_state(pbs, i, duration_segments)
    return pbs
        
def serialize_pbs(pbs):
    str = ''
    for i, pb in enumerate(pbs):  
        str += pb.verb + pb.obj_cn
        if pb.state != None:
            str += ',' + pb.state
        str += '->' 
    
    str = str[:-2]
    
    return str

def pb_type_map(stu_list):
    pb_type = dict()
    for stu in stu_list:   
        for pb in stu.pbs:
            key = pb.verb + pb.obj_cn
            if pb.state != None:
                key += ',' + pb.state
           
            if key in pb_type:
                pb_type[key] += 1
            else:
                pb_type[key] = 1
    return pb_type
           
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
def lib_reading_duration(stu_list):
    duration_list = []
    for stu in stu_list:
        pbs = stu.pbs
        for i, pb in enumerate(pbs):
            if i < len(pbs) - 1:
                duration = get_duration(pbs, i)
                duration_list.append(duration)
    return duration_list

def filter_lib_verb_exited(pbs):
    l = list(filter((lambda pb: not ((pb.obj_type == 'lib') & (pb.verb == 'exited'))), pbs))
    return l
    #for pb in pbs:  
        #if (pb.obj_type == 'lib') & (pb.verb == 'exited'):
            #pbs.remove(pb) 
    
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

def tidy_stu_lib(stus, duration_segments):
    data = []
    for stu in stus:
        pbs = clean_lib(stu.pbs, duration_segments)
        stu.pbs = pbs
        serialized_pbs = serialize_pbs(pbs)
        stu.serialized_pbs = serialized_pbs
        output = [stu.id, serialized_pbs]
        data.append(output)  
    return data, stus  
    
def to_csv(data, title, output_file_name):
    d = pd.DataFrame(data = data, columns = title)
    d.to_csv(output_file_name)
    
def get_observations(pb_type, stus):
    X = []
    length_list = []
    
    type_code = {}
    i = 0
    for key, value in pb_type.items():
        #print(key, value)
        type_code[key] = i
        i = i + 1
        
    for stu in stus:
        xi = []
        str = serialize_pbs(stu.pbs)
        observations = str.split('->')
        for ob in observations:
            if ob in type_code:
                code = type_code.get(ob)
                xi.append(code)
            else:
                print('can not find ' + ob + ' in type_code map!')
        
        length_list.append(len(observations))            
        X.append(xi)
        
    return X, length_list, len(pb_type)

def print_pb_type(py_type):
    pb_type_file = open('process_behavior_type7.txt', 'w')
    print_dict(pb_type_file, py_type, True, None)
    pb_type_file.close()
    
def print_task_score(stu_list):
    task_score_file = open('task_score.txt', 'w')
    for stu in stu_list:
        print_dict(task_score_file, task_score, True, stu.id)
    task_score_file.close()
    
def print_lib_reading_duration(duration_list):
    to_csv(duration_list, ['duration'], 'lib_reading_duration.csv')  
    
def print_cleaned_process_behavior(stus):
    output = []
    for stu in stus:
        serialized_pbs = serialize_pbs(stu.pbs)
        data = [stu.id, serialized_pbs]
        output.append(data)
    to_csv(output, ['id','process behavior'], 'process_behavior5.csv')
   
def main():
    stu_list = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs = process_behavior(Util.data_read('20170328/' + id))
        stu.task_score = task_score
        stu_list.append(stu)
    
    duration_list = lib_reading_duration(stu_list)
    stus = clean_lib(stu_list, duration_list) 
    
    py_type = pb_type_map(stus)   
    #print_pb_type(py_type)
    
    #print_task_score(stu_list)
    #print_lib_reading_duration(stu_list)
    #print_cleaned_process_behavior(stus)
    
    variables, length_list, py_type_num = get_observations(py_type, stus)
    HMM.hidden_markov(variables, length_list, py_type_num)
    
if __name__ == "__main__": main()