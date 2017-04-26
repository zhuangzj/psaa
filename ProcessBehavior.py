#!/usr/bin/python
# -*- coding: utf-8 -*-
from util import Util, HMM
import pandas as pd
from datetime import datetime
from collections import OrderedDict
import numpy as np

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



class PB:
    def __init__(self, verb, obj_id, obj_cn, obj_type, timestamp, state):
        self.verb = verb
        self.obj_id = obj_id
        self.obj_cn = obj_cn
        self.obj_type = obj_type
        self.state = state
        self.timestamp = timestamp
        self.lib_task = None
        
class Student:
    def __init__(self, id):
        self.id = id
        self.pbs = []
        self.task_score = dict()
        self.serialized_pbs = ''
        self.score_list = []

class Score:
    def __init__(self, task_id, score):
        self.task_id = task_id
        self.score = score
        self.relevant_lib_long_freq = 0
        self.relevant_lib_mid_freq = 0
        self.relevant_lib_short_freq = 0
        self.irrelevant_lib_long_freq = 0
        self.irrelevant_lib_mid_freq = 0
        self.irrelevant_lib_short_freq = 0
        
def get_score(json):
    obj, specify_obj = get_former_latter(get_obj_id(json['object']['id']), '#')
    score = json['result']['response'].get('score')  
    if web_task_map.get(obj) != None:
        if score == None:
            score = 'null'
        
        return {'task':obj, 'score':score}
    
    return None    
def process_behavior(data):
    pbs = []
    task_score = dict()
    for i in range(0,len(data)):
        type = task_or_lib(data[i], web_task_map)
#         if type == '':
#             continue
        
        obj = data[i]['object']['id']
        obj_id = get_obj_id(obj)
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp']
        
        verb, state = parse_verb_click(data[i])
        
        pb = PB(verb, obj_id, obj_cn, type, timestamp[:-6], state)
        pbs.append(pb)
        
        if obj.__contains__('statistic'):
            score_obj = get_score(data[i])
            if score_obj != None:
                task = score_obj.get('task')
                if task not in task_score:
                    task_score[task] = score_obj.get('score')
                    
#                 else:
#                     print('this task already has a score')
            else:
                print('this task does not in task map')
            
    #filtered_pbs = filter_verb_scored(pbs)
    
    specify_pbs = specify_task_obj(pbs)
    
    #filtered_spec_pbs = filter_specify_pb(specify_pbs)
           
    return specify_pbs, task_score

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
            obj, specify_obj = get_former_latter(pb.obj_id, '#')
            task_id = obj
        elif (pb.obj_type == 'lib') & (in_task == True) & (task_id != ''):
            pb.lib_task = task_id
            if lib_usefulness(task_id, pb.obj_id):
                #print('有关资料' + pb.obj_cn + ':' + pb.obj_id)
                pb.obj_id = 'relevant_lib'
                pb.obj_cn = '有关资料' #+ pb.obj_cn
            else:
                #print('无关资料' + pb.obj_cn + ':' + pb.obj_id)
                pb.obj_id = 'irrelevant_lib'
                pb.obj_cn = '无关资料' #+ f_pb.obj_cn
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'completed') & (pb.obj_id.__contains__('statistic')) & (pb.obj_id == task_id):
            in_task = False  
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'launched') & (pb.obj_id != task_id):
            task_id = pb.obj_id
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
                        
                #pb.obj_id = obj + ' ' + specify_obj
                pb.obj_cn = specify_obj

    return pbs

def filter_specify_pb(pbs):
    filtered_pbs = []
    for pb in pbs:
        obj, specify_obj = get_former_latter(pb.obj_id, '#')
        if obj == '602.htm': #不要讨价还价
            continue
        elif (pb.verb == 'drag') | (pb.verb == 'launched') | ((pb.verb == 'completed') & (specify_obj == 'statistic')):
            filtered_pbs.append(pb)
        elif (pb.verb == 'click') & ((specify_obj == 'goto2') | (specify_obj == 'giveup') | (specify_obj == 'restart')):
            filtered_pbs.append(pb)
        elif (pb.obj_type == 'task') & (pb.state != None):
            filtered_pbs.append(pb)
        elif pb.obj_type == 'lib':
            filtered_pbs.append(pb)
            
    return filtered_pbs

def merge_obj(pbs):
    for pb in pbs:
        if pb.obj_type == 'task':
            if (pb.verb == 'click') & (pb.obj_cn == 'restart') | (pb.obj_cn == 'goto2') | (pb.obj_cn == 'giveup'):
                pb.obj_cn =  ',' + pb.obj_cn
            elif (pb.verb == 'drag'):
                pb.obj_cn =  ',' + pb.obj_cn
            else: #将除了以上的obj，其余的都变成一样
                pb.obj_cn =  ''
    
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
    else:
        return 'subtask'
    

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

def filter_useless(pbs):
    filtered = []
    for i, pb in enumerate(pbs):
        if pb.verb == 'scored':
            continue
        elif (pb.verb == 'completed') & (pbs[i-1].verb == 'scored'):
            continue
        
        if pb.obj_type == 'subtask':
            continue
        
        filtered.append(pb)  
        
    return filtered   

def clean(stus, duration_list):
    lib_cleaned_stus = clean_lib(stus, duration_list)
    obj_cleaned_stus = clean_obj(lib_cleaned_stus)
    return obj_cleaned_stus

def clean_lib(stus, duration_list):
    duration_segments = get_duration_segment(duration_list)
    for i, stu in enumerate(stus):
        #标识区分lib的有效性
        pbs1 = differentiate_lib(stu.pbs)  
        #计算lib时长获得lib的时长状态 
        pbs2 = get_lib_state(pbs1, duration_segments)
        #过滤资料的exit
        cleaned_pbs = filter_lib_verb_exited(pbs2)
        
        stus[i].pbs = cleaned_pbs
    return stus
        
    return stus
def clean_obj(stus):
    for stu in stus:
        #过滤掉subtask，过滤scored
        filtered_pbs = filter_useless(stu.pbs)
        #过滤和保留某些对象
        filtered_spec_pbs = filter_specify_pb(filtered_pbs)
        #print_pbs(filtered_spec_pbs)
        
        #除了特殊的specify对象，其余对象都为‘’
        stu.pbs = merge_obj(filtered_spec_pbs)
    return stus

def print_pbs(pbs):
    for pb in pbs:
        print(pb.verb+pb.obj_cn)
        
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
    pb_type = OrderedDict()#dict()
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
                if (pb.obj_type == 'lib') & (pb.verb == 'launched'):
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
    
    type_code_dict = OrderedDict()
    i = 0
    for key, value in pb_type.items():
        type_code_dict[key] = i
        i = i + 1
        
#     for key, value in type_code_dict.items():
#         print(key, value)  
          
    for stu in stus:
        xi = []
        str = serialize_pbs(stu.pbs)
        observations = str.split('->')
        for ob in observations:
            if ob in type_code_dict:
                code = type_code_dict.get(ob)
                xi.append(code)
            else:
                print('can not find ' + ob + ' in type_code map!')
        
        length_list.append(len(observations))    
        #print(xi)        
        X.append(xi)
        
    return X, length_list, len(pb_type), type_code_dict

def print_pb_type(py_type):
    pb_type_file = open('process_behavior_type19.txt', 'w')
    print_dict(pb_type_file, py_type, True, None)
    pb_type_file.close()
    
def print_task_score(output):
#     task_score_file = open('task_score.txt', 'w')
#     for stu in stus:
#         print_dict(task_score_file, stu.task_score, True, stu.id)
#     task_score_file.close()
#     output = []
#     for stu in stus:
#         data = [stu.id, stu.task_score['601.htm'], stu.task_score['603.htm'], stu.task_score['701.htm'], stu.task_score['801.htm']]
#         output.append(data)
    to_csv(output, ['stuId', '601', 'relevant_long', 'relevant_mid', 'relevant_short', 'irrelevant_long', 'irrelevant_mid', 'irrelevant_short', 
                             '603', 'relevant_long', 'relevant_mid', 'relevant_short', 'irrelevant_long', 'irrelevant_mid', 'irrelevant_short',
                             '701', 'relevant_long', 'relevant_mid', 'relevant_short', 'irrelevant_long', 'irrelevant_mid', 'irrelevant_short',
                             '801', 'relevant_long', 'relevant_mid', 'relevant_short', 'irrelevant_long', 'irrelevant_mid', 'irrelevant_short'], 
                    'task_score6.csv')
    
def print_lib_reading_duration(duration_list):
    to_csv(duration_list, ['duration'], 'lib_reading_duration3.csv')  
    
def print_cleaned_process_behavior(stus):
    output = []
    for stu in stus:
        serialized_pbs = serialize_pbs(stu.pbs)
        data = [stu.id, serialized_pbs]
        output.append(data)
    to_csv(output, ['id','process behavior'], 'process_behavior8.csv')
    
def code2type(code_seqs, pb_code_dict):  
    code_lists = code_seqs.tolist() 
    type_seqs = []
    for code_list in code_lists:
        code_list.reverse()
        type_seq = []
        for code in code_list:
            pb = ''
            for key, value in pb_code_dict.items():
                if value == code:
                    pb = key
                    break
            type_seq.append(pb)
            
        type_seqs.append(type_seq)
    
    type_arr = np.array(type_seqs)       
    return type_arr

def drag2click(stus):
    for stu in stus:
        for pb in stu.pbs:
            if (pb.verb == 'drag'):
                if pb.obj_cn == ',in':
                    pb.state = 'correct'
                elif pb.obj_cn == ',out':
                    pb.state = 'incorrect'
                pb.verb = 'click'
                pb.obj_cn = ''
                
def delete_launch_complete_goto2(stus):
    
    for stu in stus:
        filtered = []
        for pb in stu.pbs:
            if (pb.obj_type == 'task') & (pb.verb == 'launched') | (pb.verb == 'completed'):
                continue
            elif (pb.verb == 'click') & (pb.obj_cn == ',goto2'):
                continue
            filtered.append(pb)
        
        stu.pbs = filtered
            
def adjust_data(stus):
    drag2click(stus)
    delete_launch_complete_goto2(stus) 
    
def reverse(e):
    e_list = e.tolist()
    for ei in e_list:
        ei.reverse()
    e_arr = np.array(e_list)      
    return e_arr

def task_601_score(stu):
    for pb in stu.pbs:
        if (pb.verb == 'click') & (pb.obj_cn == 'answer1'):
            if pb.state == 'correct':
                stu.task_score['601.htm'] = str(100)
            elif pb.state == 'incorrect':
                stu.task_score['601.htm'] = str(0)
                    
# def task_score_lib_freq(stus):
#     for stu in stus:
#         in_task_state = 'not_in_task' #False和None是区分结束和不在
#         in_task_id = ''
#         natural_complete = True
#         in_task_pbs = []
#         for pb in stu.pbs:
#             if (pb.obj_type == 'task') & (in_task_state == 'not_in_task') & (pb.verb == 'launched'):
#                 in_task_state = 'not_in_task'
#                 in_task_id = pb.obj_id
#             elif (pb.obj_type == 'task') & (in_task_state == 'start') & (pb.verb == 'completed'):
#                 in_task_state = 'stop'
#                 natural_complete = True
#             elif (pb.obj_type == 'task') & (in_task_state == 'start') & (pb.verb == 'launched') & (pb.obj_id != in_task_id):#下一个任务开始
#                 in_task_state = 'stop'
#                 natural_complete = False
#             
#             if in_task_state == 'start':
#                 in_task_pbs.append(pb)        
#             elif in_task_state = 'not_in_task' == False:

def task_lib_freq(stus):
    task_score_libfreq = []
    for stu in stus:
        score_map = dict()
        score_map['601.htm'] = Score('601.htm', stu.task_score['601.htm'])
        score_map['603.htm'] = Score('603.htm', stu.task_score['603.htm'])
        score_map['701.htm'] = Score('701.htm', stu.task_score['701.htm'])
        score_map['801.htm'] = Score('801.htm', stu.task_score['801.htm'])
        
        for pb in stu.pbs:
            if (pb.obj_type == 'lib') & (pb.lib_task != None):  
                task_id = pb.lib_task
                score_obj = score_map.get(task_id)
                #602.htm有阅读资料操作，但不算其分数和频率
                if score_obj != None:
                    if pb.obj_id == 'relevant_lib':
                        if pb.state == 'long':
                            score_obj.relevant_lib_long_freq += 1
                        elif pb.state == 'mid':
                            score_obj.relevant_lib_mid_freq += 1
                        elif pb.state == 'short':
                            score_obj.relevant_lib_short_freq += 1   
                    elif pb.obj_id == 'irrelevant_lib':
                        if pb.state == 'long':
                            score_obj.irrelevant_lib_long_freq += 1
                        elif pb.state == 'mid':
                            score_obj.irrelevant_lib_mid_freq += 1
                        elif pb.state == 'short':
                            score_obj.irrelevant_lib_short_freq += 1     
        score_list = [score_map['601.htm'], score_map['603.htm'], score_map['701.htm'], score_map['801.htm']]
        
        data = []
        data.append(stu.id)
        for e in score_list:
            data.append(e.score)
            data.append(e.relevant_lib_long_freq)
            data.append(e.relevant_lib_mid_freq)
            data.append(e.relevant_lib_short_freq)
            data.append(e.irrelevant_lib_long_freq)
            data.append(e.irrelevant_lib_mid_freq)
            data.append(e.irrelevant_lib_short_freq)
            
        task_score_libfreq.append(data) 
    return task_score_libfreq
def main():
    stus = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs, stu.task_score = process_behavior(Util.data_read('20170328/' + id))
        task_601_score(stu)
        stus.append(stu)
    
    #获得阅读资料的所有时长
    duration_list = lib_reading_duration(stus)
#    print_lib_reading_duration(duration_list)
    #lib处理
    stus = clean_lib(stus, duration_list) 
    #计算任务得分和任务里的lib各个频率
    task_score_output = task_lib_freq(stus)
#    print_task_score(task_score_output)
    
    stus = clean_obj(stus)

    adjust_data(stus)
     
    type_frequency_dict = pb_type_map(stus)   
    print_pb_type(type_frequency_dict)
    
    
    
#    print_cleaned_process_behavior(stus)
    
#     observations, length_list, py_type_num, type_code_dict = get_observations(type_frequency_dict, stus)
#     startprob, transmat, emissionprob, code_sequence = HMM.hidden_markov(observations, length_list, py_type_num)
#     type_sequence = code2type(code_sequence, type_code_dict)
#     reversed_emissprob = reverse(emissionprob)
#     HMM.output_model(startprob, transmat, reversed_emissprob, type_sequence)
#     print(type_sequence)
    
if __name__ == "__main__": main()