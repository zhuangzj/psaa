#!/usr/bin/python
# -*- coding: utf-8 -*-
from util import Util, HMM
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

task_libs = {'601.htm': {'origin_rel':['601.json'], 'strong':['601.json', '604.json', '617.json'], 'medium':['701.json', '611.json', '616.json', '618.json', '619.json']},
             '701.htm': {'origin_rel':['603.json'], 'strong':['701.json', '602.json', '603.json', '614.json'], 'medium':['613.json', '616.json', '618.json']},
             '603.htm': {'origin_rel':['607.json', '619.json'], 'strong':['607.json', '618.json', '619.json'], 'medium':['617.json', '616.json']}}



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
        self.task_time = None
        self.serialized_pbs = ''
        self.score_list = []

class Score:
    def __init__(self, task_id, score):
        self.task_id = task_id
        self.score = score
        self.strong_lib = {'long': 0, 'mid': 0, 'short': 0}
        self.medium_lib = {'long': 0, 'mid': 0, 'short': 0}
        self.weak_lib = {'long': 0, 'mid': 0, 'short': 0}
        self.origin_lib = {'long': 0, 'mid': 0, 'short': 0}
        
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
    begin_timestamp = None
    end_timestamp = None
    for i in range(0,len(data)):
        type = task_or_lib(data[i], web_task_map)
#         if type == '':
#             continue
        
        obj = data[i]['object']['id']
        obj_id = get_obj_id(obj)
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp'][:-6]
        
        if i == 0:
            begin_timestamp = timestamp
        
        verb, state = parse_verb_click(data[i])
        
        pb = PB(verb, obj_id, obj_cn, type, timestamp, state)
        pbs.append(pb)
        
        if obj.__contains__('statistic'):
            end_timestamp = timestamp
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
    task_time = time_lag(begin_timestamp, end_timestamp)
    #filtered_spec_pbs = filter_specify_pb(specify_pbs)
           
    return specify_pbs, task_score, task_time

def time_lag(begin_str, end_str):
    begin_time = datetime.strptime(begin_str, '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%S')
    lag = end_time - begin_time
    return lag.total_seconds()
    
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
        if (pb.obj_type == 'lib') & (in_task == False): # 不在任务中阅读的资料
            #print('资料' + pb.obj_cn + ':' + pb.obj_id)
            pb.obj_id = 'task_out_lib'
            pb.obj_cn = '资料' #+ pb.obj_cn
        elif (pb.obj_type == 'task') & (in_task == False) & (pb.verb == 'launched'): # 任务开始
            in_task = True
            obj, specify_obj = get_former_latter(pb.obj_id, '#')
            task_id = obj
        elif (pb.obj_type == 'lib') & (in_task == True) & (task_id != ''): # 在任务中阅读的资料
            pb.lib_task = task_id
            lib_rel = lib_relevance(task_id, pb.obj_id) # 根据阅读的资料和任务看资料是否该任务的有关资料以及其相关程度
            pb.obj_id = lib_rel
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'completed') & (pb.obj_id.__contains__('statistic')) & (pb.obj_id == task_id): # 任务结束
            in_task = False  
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'launched') & (pb.obj_id != task_id): # 任务中又重启了该任务
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
        if (obj == '602.htm') | (pb.lib_task == '602.htm'): #不要讨价还价
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

def lib_relevance(task_id, lib_id):
    task = task_libs.get(task_id)
    if task != None:
        rel_lib = ['strong_lib' for lib in task['strong'] if lib == lib_id]
        if not rel_lib:
            rel_lib = ['medium_lib' for lib in task['medium'] if lib == lib_id]
        if not rel_lib:
            rel_lib = 'weak_lib' 
            
        rel_lib = ''.join(rel_lib)   
        origin_rel_lib = ['origin_lib' for lib in task['origin_rel'] if lib == lib_id]
        if origin_rel_lib: # origin_rel_lib not empty
            origin_rel_lib = ''.join(origin_rel_lib)
            rel_lib += ',' + origin_rel_lib
    else: # task not in task map
        rel_lib = 'out_task_lib'
    return rel_lib
      
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
    

    
def get_observations(pb_type, stus):
    X = []
    length_list = []
    
    type_code_dict = OrderedDict()
    i = 0
    for key, value in pb_type.items():
        type_code_dict[key] = i
        i = i + 1
          
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
    Util.to_csv(output, ['stuId', '601', 'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_short', 'strong_short', 'medium_short', 'weak_short',
                             '603', 'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_short', 'strong_short', 'medium_short', 'weak_short',
                             '701', 'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_short', 'strong_short', 'medium_short', 'weak_short',
                             '801', 'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_short', 'strong_short', 'medium_short', 'weak_short'
                             ], 
                    'task_score_relevance.csv')
    
def print_lib_reading_duration(duration_list):
    Util.to_csv(duration_list, ['duration'], 'lib_reading_duration3.csv')  
    
def print_cleaned_process_behavior(stus):
    output = []
    for stu in stus:
        serialized_pbs = serialize_pbs(stu.pbs)
        data = [stu.id, serialized_pbs]
        output.append(data)
    Util.to_csv(output, ['id','process behavior'], 'process_behavior8.csv')
    
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
                    
def task_lib_freq(stus):
    task_score_libfreq = []
    for stu in stus:
        score_map = dict()
        score_map['601.htm'] = Score('601.htm', stu.task_score['601.htm'])
        score_map['603.htm'] = Score('603.htm', stu.task_score['603.htm'])
        score_map['701.htm'] = Score('701.htm', stu.task_score['701.htm'])
        score_map['801.htm'] = Score('801.htm', stu.task_score['801.htm'])
        
        for pb in stu.pbs:
            #602.htm有阅读资料操作，但不算其分数和频率
            if (pb.obj_type == 'lib') & (pb.lib_task != None):  
                task_id = pb.lib_task
                score_obj = score_map.get(task_id)
                time = pb.state
                if (score_obj != None) & (pb.state != None):
                    if pb.obj_id.__contains__('strong_lib'):
                        score_obj.strong_lib[pb.state] += 1
                    elif pb.obj_id.__contains__('medium_lib'):
                        score_obj.medium_lib[pb.state] += 1
                    elif pb.obj_id.__contains__('weak_lib'):
                        score_obj.weak_lib[pb.state] += 1
                    if pb.obj_id.__contains__('origin_lib'):
                        score_obj.origin_lib[pb.state] += 1
                           
        score_list = [score_map['601.htm'], score_map['603.htm'], score_map['701.htm'], score_map['801.htm']]
        
        data = []
        data.append(stu.id)
        for s in score_list:
            data.append(s.score)
            data.append(s.origin_lib['long'])
            data.append(s.strong_lib['long'])
            data.append(s.medium_lib['long'])
            data.append(s.weak_lib['long'])
            data.append(s.origin_lib['mid'])
            data.append(s.strong_lib['mid'])
            data.append(s.medium_lib['mid'])
            data.append(s.weak_lib['mid'])
            data.append(s.origin_lib['short'])
            data.append(s.strong_lib['short'])
            data.append(s.medium_lib['short'])
            data.append(s.weak_lib['short'])
            
        task_score_libfreq.append(data) 
    return task_score_libfreq

def print_task_time(stus):
    file = open('task_completed_duration2.txt', 'w')
    for stu in stus:
        file.write(stu.id + ',' + str(stu.task_time) + '\n')
    file.close()    

def tent_measure_time(stus):
    list = []
    for stu in stus:
        data = []
        data.append(stu.id)
        big_finished = False 
        mid_finished = False
        lit_finished = False
        launched = False
        begin_timestamp = None
        end_timestamp = None
        last_timestamp = None
        for pb in stu.pbs:
            if not big_finished:
                if (pb.obj_id.__contains__('701.htm')) & (pb.verb == 'launched') & (not launched):
                    begin_timestamp = pb.timestamp
                    launched = True
                if (pb.obj_cn == 'bigsubmit') & (pb.verb == 'click') & (launched) :
                    end_timestamp = pb.timestamp
                    launched = False
                    big_finished = True
                    last_timestamp = end_timestamp
            else:
                if not mid_finished:
                    if last_timestamp != None:
                        begin_timestamp = last_timestamp
                    if (pb.obj_cn == 'midsubmit') & (pb.verb == 'click'):
                        end_timestamp = pb.timestamp
                        mid_finished = True
                        last_timestamp = end_timestamp
                else:
                    if not lit_finished:
                        if last_timestamp != None:
                            begin_timestamp = last_timestamp
                        if (pb.obj_cn == 'litsubmit') & (pb.verb == 'click'):
                            end_timestamp = pb.timestamp
                            lit_finished = True
                    else:
                        break
            if (begin_timestamp != None) & (end_timestamp != None):
                time = time_lag(begin_timestamp, end_timestamp)
                data.append(time)
                begin_timestamp = None
                end_timestamp = None
                
        list.append(data)
    return list

def print_tent_measure_time(list):
    Util.to_csv(list, ['stuId', 'big', 'mid', 'lit'], 'tent_measure_time2.csv')
    
def main():
    stus = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs, stu.task_score, stu.task_time = process_behavior(Util.data_read('20170328/' + id))
        task_601_score(stu)
        stus.append(stu)
    
    #获得阅读资料的所有时长
    duration_list = lib_reading_duration(stus)
#    print_lib_reading_duration(duration_list)

    #获取每个帐篷的测量时间
#    time_list = tent_measure_time(stus)
#    print_tent_measure_time(time_list)
    
    #lib处理
    stus = clean_lib(stus, duration_list) 
    #计算任务得分和任务里的lib各个频率
    task_score_output = task_lib_freq(stus)
    print_task_score(task_score_output)
    
#     stus = clean_obj(stus)
# 
#     adjust_data(stus)
#      
#     type_frequency_dict = pb_type_map(stus)   
#    print_pb_type(type_frequency_dict)
    
    #打印做题时间
#    print_task_time(stus)
    
#    print_cleaned_process_behavior(stus)
    
#     observations, length_list, py_type_num, type_code_dict = get_observations(type_frequency_dict, stus)
#     startprob, transmat, emissionprob, code_sequence = HMM.hidden_markov(observations, length_list, py_type_num)
#     type_sequence = code2type(code_sequence, type_code_dict)
#     reversed_emissprob = reverse(emissionprob)
#     HMM.output_model(startprob, transmat, reversed_emissprob, type_sequence)
#     print(type_sequence)
    
if __name__ == "__main__": main()