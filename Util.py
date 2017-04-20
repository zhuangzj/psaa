import json
import codecs

def parse_obj_id(web_task_map, s):

    rs = s[s.rindex('/')+1:]
    
    if s.__contains__('#'):
        rs = rs.split('#')[0] #why1not0 

    if rs.__contains__('?'):
        rs = rs.split('?')[0]

    if web_task_map.has_key(rs):
        rs = web_task_map[rs]
    
    return rs

def parse_verb_id(s):
    s=s[s.rindex('/')+1:]
    if s.__contains__(','):
        return s[:s.index(',')]
    else:
        return s

def data_read(file_name):
    file = './data/' + file_name + '.json'
    with codecs.open(file, 'r', 'utf-8') as f: #以utf-8的编码读文件
    #with open(file) as f:
        data = json.load(f)
    return data

def print_events(e):
    for key, value in e.iteritems():
        print (key + ':' + str(value))

def specify_obj(obj_id):
    if obj_id.__contains__('#'):
        obj_id = obj_id.split('#')[1]
    return obj_id

def parse(data, web_task_map):
    events = dict()
    for i in range(0,len(data)):
        obj_id = parse_obj_id(web_task_map, data[i]['object']['id'])
        verb_id = parse_verb_id(data[i]['verb']['id'])
        
        if verb_id == 'click':
            obj_id += '-' + specify_obj(data[i]['object']['id'])
        elif verb_id == 'drag':    
            obj_id += '-' + specify_obj(data[i]['object']['id'])
        elif verb_id == 'hover':    
            obj_id += '-' + specify_obj(data[i]['object']['id'])
        elif verb_id == 'hover-in':    
            obj_id += '-' + specify_obj(data[i]['object']['id'])
        elif verb_id == 'hover-out':    
            obj_id += '-' + specify_obj(data[i]['object']['id'])
            
        event = verb_id + ' ' + obj_id
        if events.has_key(event):
            events[event] += 1
        else:
            events[event] = 1
    print_events(events)