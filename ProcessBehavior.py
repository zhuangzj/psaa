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

# task_libs = {'601.htm': {'origin_rel':['601.json'], 'strong':['601.json', '604.json', '617.json'], 'medium':['701.json', '611.json', '616.json', '618.json', '619.json']},
#              '701.htm': {'origin_rel':['603.json'], 'strong':['701.json', '602.json', '603.json', '614.json'], 'medium':['613.json', '616.json', '618.json']},
#              '603.htm': {'origin_rel':['607.json', '619.json'], 'strong':['607.json', '618.json', '619.json'], 'medium':['617.json', '616.json']}}

task_libs = {'601.htm': {'strong':['601.json', '604.json', '617.json'], 'medium':['701.json', '611.json', '616.json', '618.json', '619.json']},
             '701.htm': {'strong':['701.json', '602.json', '603.json', '614.json'], 'medium':['613.json', '616.json', '618.json']},
             '603.htm': {'strong':['607.json', '618.json', '619.json'], 'medium':['617.json', '616.json']}}

class PB:
    def __init__(self, verb, obj_id, obj_cn, obj_type, timestamp, state):
        self.verb = verb
        self.obj_id = obj_id # 行为的对象id 任务(#具体对象)
        self.obj_cn = obj_cn # 对象的中文
        self.obj_type = obj_type # 对象的类型（task或者lib）
        self.state = state # 对象的状态（task:(in)valid,(in)correct; lib:short,!short）
        self.timestamp = timestamp # 行为发生的时间
        self.lib_task = None # 若对象是lib且发生在做任务期间，则记录它属于哪个任务
        
class Student:
    def __init__(self, id):
        self.id = id # 学生编号
        self.pbs = [] # 学生一系列的行为序列
        self.task_score = dict() # 各任务的得分
        self.task_time = None # 做题时间
        self.serialized_pbs = '' # 将所有的行为序列转成一行字符串
        self.score_list = [] # 每项任务得分（包括资料阅读情况统计）

class Score:
    def __init__(self, task_id, score):
        self.task_id = task_id # 任务编号
        self.score = score # 做题得分
        self.strong_lib = {'long': 0, 'mid': 0, 'short': 0, 'no_time': 0, '!short': 0} # 阅读强相关资料分别用时统计
        self.medium_lib = {'long': 0, 'mid': 0, 'short': 0, 'no_time': 0, '!short': 0} # 阅读中等相关资料分别用时统计
        self.weak_lib = {'long': 0, 'mid': 0, 'short': 0, 'no_time': 0, '!short': 0} # 阅读弱相关资料分别用时统计
        self.origin_lib = {'long': 0, 'mid': 0, 'short': 0, 'no_time': 0, '!short': 0} # 阅读原始相关资料分别用时统计

# 获得该json的obj id
def get_obj_id(obj):

    obj_id = obj[obj.rindex('/')+1:]

    if obj_id.__contains__('?'):
        obj_id = obj_id.split('?')[0]
    
    return obj_id

# 获得某任务的得分        
def get_score(json):
    obj = get_obj_id(json['object']['id'])[:7]
    score = json['result']['response'].get('score')  
    if web_task_map.get(obj) != None:
        if score == None:
            score = 'null'
        
        return {'task':obj, 'score':score}
    
    return None  

# 返回对象类型（task,lib）
def task_or_lib(json, web_task_map):
    obj = json['object']['id']
    if 'liberary' in obj:
        return 'lib'
    
    obj_id = get_obj_id(obj)[:7]
        
    if web_task_map.get(obj_id):
        return 'task'
    else:
        return 'subtask'  

# 解析json串    
def process_behavior(data, stuId):
    pbs = []
    task_score = dict()
    begin_timestamp = None
    end_timestamp = None
    for i in range(0,len(data)):
        pb_type = task_or_lib(data[i], web_task_map)
        obj = data[i]['object']['id']
        obj_id = get_obj_id(obj)
        obj_cn = '“' + data[i]['object']['definition']['name']['zh_CN'] + '”'
        timestamp = data[i]['timestamp'][:-6]
        
        if i == 0:
            begin_timestamp = timestamp
        
        verb, state = parse_verb_click(data[i])
        pb = PB(verb, obj_id, obj_cn, pb_type, timestamp, state)
        pbs.append(pb)
        
        if obj.__contains__('statistic'):
            end_timestamp = timestamp
            score_obj = get_score(data[i])
            if score_obj != None:
                task = score_obj.get('task')
                score = score_obj['score']
                if task not in task_score:
                    task_score[task] = score_obj.get('score')
#                 else:
#                     print(stuId + 'task' + task + 'already has a score')
#                     print('former score:' + str(task_score[task]))
#                     print('new score:' + str(score))
            else:
                print('this task does not in task map')
         
    # 明确801拖拽的是哪个对象（girl,boy,woman,man）            
    specify_pbs = specify_801_obj(pbs)
    # 完成测试的总时长
    task_time = time_lag(begin_timestamp, end_timestamp)
           
    return specify_pbs, task_score, task_time

def time_lag(begin_str, end_str):
    begin_time = datetime.strptime(begin_str, '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%S')
    lag = end_time - begin_time
    return lag.total_seconds()
    
def parse_verb_click(json):
    v = get_verb(json['verb']['id'])
    obj = get_obj_id(json['object']['id'])
    state = ''
    #deal with click of 701、601htm 
    if (v.__contains__('click')) & (v.__contains__(',')): 
        states = v.split(',')
        if obj.__contains__('701.htm'):
            if len(states) == 4:
                valid = states[1]
                correct = states[2]
                if (valid == '1') & (correct == '1'):
                    state = 'valid,correct'
                elif (valid == '1') & (correct == '0'):
                    state = 'valid,incorrect'
                elif (valid == '0') & (correct == '1'):
                    state = 'invalid,correct'
                elif (valid == '0') & (correct == '0'):
                    state = 'invalid,incorrect'
            elif len(states) == 3:
                correct = states[2]
                if correct == '1':
                    state = 'correct'
                else:
                    state = 'incorrect'
        elif obj.__contains__('601.htm'):
            correct = states[2]
            if correct == '1':
                state = 'correct'
            else:
                state = 'incorrect'
   
    # 去掉states，只保留真正的verb   
    if v.__contains__(','):
        v = v[:v.index(',')]
        
    return v, state

# 区分资料是不在任务期间阅读的资料（task_out_lib）还是在任务期间阅读的资料（strong_lib,medium_lib,weak_lib）
def differentiate_lib(pbs):
    in_task = False
    task_id = ''
    for pb in pbs:
        if (pb.obj_type == 'lib') & (in_task == False): # 不在任务中阅读的资料
            pb.obj_id = 'task_out_lib'
            pb.obj_cn = 'task_out_lib' #+ pb.obj_cn
        elif (pb.obj_type == 'task') & (in_task == False) & (pb.verb == 'launched'): # 任务开始
            in_task = True
            # 记录做的是哪个任务
            task_id = pb.obj_id[:7]
        elif (pb.obj_type == 'lib') & (in_task == True) & (task_id != ''): # 在任务中阅读的资料
            # 为该lib类型的pb记录其对应的task
            pb.lib_task = task_id
            # 根据阅读的资料和任务看资料的相关程度
            lib_rel = lib_relevance(task_id, pb.obj_id) 
            # 将lib类型的pb的id改为显示相关程度的id
            pb.obj_id = lib_rel
            pb.obj_cn = lib_rel
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'completed') & (pb.obj_id.__contains__('statistic')) & (pb.obj_id == task_id): # 任务结束
            in_task = False  
        elif (pb.obj_type == 'task') & (in_task == True) & (pb.verb == 'launched') & (pb.obj_id != task_id): # 任务中又重启了该任务
            task_id = pb.obj_id[:7]
        
        # favorite check
#         if pb.verb.__contains__('favorite'):
#             print(pb.verb + ' ' + pb.lib_task + ' ' + pb.obj_cn) 
              
#         if pb.obj_type == 'lib':
#             if pb.lib_task != None:
#                 print(pb.obj_id + '<-' + pb.lib_task)
#             else:
#                 print(pb.obj_id + '<-' + 'its lib_task is none')
#         elif pb.obj_type == 'task':
#             print(pb.obj_id)
#         else:
#             print('type wrong:'+pb.obj_type)
    
    return pbs

# 明确拖拽对象，赋值到obj_cn
def specify_801_obj(pbs):
    for pb in pbs:
        if pb.obj_type == 'task':    
            specify_obj = pb.obj_id[8:]
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
        # check give up
#         if specify_obj == 'giveup':
#             print(pb.verb + ' ' + pb.obj_id)

        #不要讨价还价, 801.htm没有相关资料库，不输出
        if (obj == '602.htm') | (pb.lib_task == '602.htm') | (obj == '801.htm') | (pb.lib_task == '801.htm'): 
            continue
        elif (pb.verb == 'drag') | (pb.verb == 'launched') | ((pb.verb == 'completed') & (specify_obj == 'statistic')):
            filtered_pbs.append(pb)
        elif (pb.verb == 'click') & ((specify_obj == 'goto2') | (specify_obj == 'giveup') | (specify_obj == 'restart')):
            filtered_pbs.append(pb)
        elif (pb.obj_type == 'task') & (pb.state != ''):
            filtered_pbs.append(pb)
        elif pb.obj_type == 'lib':
            filtered_pbs.append(pb)
        
            
    return filtered_pbs

def merge_obj(pbs):
    for pb in pbs:
        if pb.obj_type == 'task':
            if (pb.verb == 'click') & (pb.obj_cn == 'restart') | (pb.obj_cn == 'goto2') | (pb.obj_cn == 'giveup'):
                pb.obj_cn =  pb.obj_cn
            elif (pb.verb == 'drag'):
                pb.obj_cn =  pb.obj_cn
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
        # 保留一开始相关的任务和资料
#         origin_rel_lib = ['origin_lib' for lib in task['origin_rel'] if lib == lib_id]
#         if origin_rel_lib: # origin_rel_lib not empty
#             origin_rel_lib = ''.join(origin_rel_lib)
#             rel_lib += ',' + origin_rel_lib
    else: # 602.htm或801.htm任务中阅读的lib
        rel_lib = 'no_relevant_lib'
    return rel_lib
    
def get_former_latter(string, sign):
    if string.__contains__(sign):
        former = string.split(sign)[0]
        latter = string.split(sign)[1]
        return former, latter
    
    return string, None
 
def get_verb(s):
    s=s[s.rindex('/')+1:]
    return s   

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
    # 获得阅读时长长短的分界线
    duration_segments = get_duration_segment(duration_list)
    for i, stu in enumerate(stus):
        #计算lib时长获得lib的时长状态 
        stated_lib = get_lib_state(stu.pbs, duration_segments)
        #过滤资料的exit
        filtered_pbs = filter_lib_verb_exited(stated_lib)
        #标识区分lib的有效性
        differed_lib = differentiate_lib(filtered_pbs)
        
        stus[i].pbs = differed_lib
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
    string = ''
    for pb in pbs:  
        string = string + pb.verb + ' ' + pb.obj_cn + pb.state + '->'
    
    return string[:-2]

def pb_type_map(stu_list):
    pb_type = OrderedDict()#dict()
    for stu in stu_list:   
        for pb in stu.pbs:
            key = pb.verb + ' ' + pb.obj_cn + pb.state
            if key in pb_type:
                pb_type[key] += 1
            else:
                pb_type[key] = 1
    return pb_type
           
def print_dict(file_name, dict, has_key, stu_id):
    file = open(file_name, 'w')
    if stu_id != None:
        file.write(stu_id + '\n')
    for key, value in dict.items():
        if has_key:
            file.write(key + ':' + str(value) + '\n')
            #print (key + ':' + str(value))
        else:
            file.write(str(value) + '\n')
            #print (str(value))
    file.close()   
         
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
        return  '!short'#'mid'
    elif second >= long:
        return '!short'#'long'

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

# 将所有学生阅读资料的时间排序后分为三等分，得出阅读的短时长、中时长和长时长    
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

# def print_pb_type(py_type):
#     pb_type_file = open('process_behavior_type3.txt', 'w')
#     print_dict(pb_type_file, py_type, True, None)
#     pb_type_file.close()
    
def print_task_score(output):
    Util.to_csv(output, ['stuId', '601', 'strong_short', 'medium_short', 'weak_short', 'strong_!short', 'medium_!short', 'weak_!short', #'origin_short', 'origin_!short',  'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_notime', 'strong_notime', 'medium_notime', 'weak_notime', 
                             '603', 'strong_short', 'medium_short', 'weak_short', 'strong_!short', 'medium_!short', 'weak_!short', #'origin_short', 'origin_!short',  'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_notime', 'strong_notime', 'medium_notime', 'weak_notime', 
                             '701', 'strong_short', 'medium_short', 'weak_short', 'strong_!short', 'medium_!short', 'weak_!short', #'origin_short', 'origin_!short',  'origin_long', 'strong_long', 'medium_long', 'weak_long', 'origin_mid', 'strong_mid', 'medium_mid', 'weak_mid', 'origin_notime', 'strong_notime', 'medium_notime', 'weak_notime', 
                             'total'#'801'
                             ], 
                    'three_task_score_lib_relevance.csv')
    
def print_lib_reading_duration(duration_list):
    Util.to_csv(duration_list, ['duration'], 'lib_reading_duration3.csv')  
    
def print_cleaned_process_behavior(stus):
    output = []
    for stu in stus:
        serialized_pbs = serialize_pbs(stu.pbs)
        data = [stu.id, serialized_pbs]
        output.append(data)
    Util.to_csv(output, ['id','process behavior'], 'process_behavior4.csv')
    
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
            elif (pb.verb == 'click') & (pb.obj_id.__contains__('goto2')):
                
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
                if (score_obj != None) & (pb.state != ''):
                    if pb.obj_id.__contains__('strong_lib'):
                        score_obj.strong_lib[pb.state] += 1
#                         score_obj.strong_lib['no_time'] += 1
#                         if pb.state != 'short':
#                             score_obj.strong_lib['!short'] += 1 
                    elif pb.obj_id.__contains__('medium_lib'):
                        score_obj.medium_lib[pb.state] += 1
#                         score_obj.medium_lib['no_time'] += 1
#                         if pb.state != 'short':
#                             score_obj.medium_lib['!short'] += 1 
                    elif pb.obj_id.__contains__('weak_lib'):
                        score_obj.weak_lib[pb.state] += 1
#                         score_obj.weak_lib['no_time'] += 1
#                         if pb.state != 'short':
#                             score_obj.weak_lib['!short'] += 1 
                    if pb.obj_id.__contains__('origin_lib'):
                        score_obj.origin_lib[pb.state] += 1
#                         score_obj.origin_lib['no_time'] += 1
#                         if pb.state != 'short':
#                             score_obj.origin_lib['!short'] += 1 
                           
        score_list = [score_map['601.htm'], score_map['603.htm'], score_map['701.htm'], score_map['801.htm']]
        
        data = []
        data.append(stu.id)
        total_score = 0
        for s in score_list:
            if s.task_id != '801.htm':
                total_score += int(s.score)
                data.append(s.score)
#                 data.append(s.origin_lib['long'])
#                 data.append(s.strong_lib['long'])
#                 data.append(s.medium_lib['long'])
#                 data.append(s.weak_lib['long'])
#                 data.append(s.origin_lib['mid'])
#                 data.append(s.strong_lib['mid'])
#                 data.append(s.medium_lib['mid'])
#                 data.append(s.weak_lib['mid'])
#                data.append(s.origin_lib['short'])
                data.append(s.strong_lib['short'])
                data.append(s.medium_lib['short'])
                data.append(s.weak_lib['short'])
#                 data.append(s.origin_lib['no_time'])
#                 data.append(s.strong_lib['no_time'])
#                 data.append(s.medium_lib['no_time'])
#                 data.append(s.weak_lib['no_time'])
#                data.append(s.origin_lib['!short'])
                data.append(s.strong_lib['!short'])
                data.append(s.medium_lib['!short'])
                data.append(s.weak_lib['!short'])
#             else:
#                 data.append(s.score)
        data.append(total_score)
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

def sortMapByFreq(map):
    sortedMap = OrderedDict()
    # print dic.items()得到[(键，值)]的列表。然后用sorted方法，通过key这个参数，指定排序是按照value，也就是第一个元素d[1的值来排序。reverse = True表示是需要翻转的，默认是从小到大，翻转的话，那就是从大到小。
    for key, value in sorted(map.items(), key=lambda d:d[1], reverse = True):
        #print(key + ':' + str(value))
        sortedMap[key] = value
    
    return sortedMap

def gram(stus, gram_type): 
    pb_type_map = OrderedDict()
    for stu in stus:
        pbs = stu.pbs
        for i, pb in enumerate(pbs): 
            pb1 = pb.verb + ' ' + pb.obj_cn + pb.state
            if i < len(pbs) - 1:
                pb2 = pb1 + '->' + pbs[i+1].verb + ' ' + pbs[i+1].obj_cn + pbs[i+1].state 
            if i < len(pbs) - 2:
                pb3 = pb2 + '->' + pbs[i+2].verb + ' ' + pbs[i+2].obj_cn + pbs[i+2].state 
            
            if gram_type == 'uni':
                key = pb1
            elif gram_type == 'back':
                key = pb2
                if i >= len(pbs) - 2:
                    break
            elif gram_type == 'tree':
                key = pb3
                if i >= len(pbs) - 3:
                    break
            
                
            if key in pb_type_map:
                pb_type_map[key] += 1
            else:
                pb_type_map[key] = 1
                    
    sortedMap = sortMapByFreq(pb_type_map)  
     
    return sortedMap
            
def main():
    stus = []
    for id in stu_ids:
        stu = Student(id)
        stu.pbs, stu.task_score, stu.task_time = process_behavior(Util.data_read('20170328/' + id), id)
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
    
    # 过滤、合并一些pb
#    clean_obj(stus)
 
    # 调整一下数据（将drag in(out) 改为click correct(incorrect)，删除goto2）
#    adjust_data(stus)
      
#    type_frequency_dict = pb_type_map(stus)   
#    print_dict('process_behavior_type3.txt', type_frequency_dict, True, None)
    
    #打印做题时间
#    print_task_time(stus)
    
#    print_cleaned_process_behavior(stus)
    
#     unigram = gram(stus, 'uni')
#     print_dict('unigram.txt', unigram, True, None)
#     bigram = gram(stus, 'back')
#     print_dict('bigram.txt', bigram, True, None)
#     trigram = gram(stus, 'tree')
#     print_dict('trigram.txt', trigram, True, None)
    
#     observations, length_list, py_type_num, type_code_dict = get_observations(type_frequency_dict, stus)
#     startprob, transmat, emissionprob, code_sequence = HMM.hidden_markov(observations, length_list, py_type_num)
#     type_sequence = code2type(code_sequence, type_code_dict)
#     reversed_emissprob = reverse(emissionprob)
#     HMM.output_model(startprob, transmat, reversed_emissprob, type_sequence)
#     print(type_sequence)
    
if __name__ == "__main__": main()