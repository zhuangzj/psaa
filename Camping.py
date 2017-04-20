import json
import pandas as pd

web_task_map={'601.htm':'ticket purchase-multiple choice',
              '602.htm':'ticket purchase-price threshold',
              '701.htm':'measure the tent',
              '801.htm':'tent assignment',
              '603.htm':'tour plan'}
debug=False


def get_title():
    title= ['id','correct_ref_p','good_drag_p','restart_count','litsubmit_correct_p','midsubmit_correct_p','bigsubmit_correct_p',
            'litvalid','litmeasured','midvalid','midmeasured','bigvalid','bigmeasured']
    return title

class Side:
    def __init__(self,name,valid):
        self.name=name
        self.valid=valid
        self.change_times=0

class Student:
    def __init__(self,id):
        self.id=id
        self.correct_ref=0
        self.total_ref=0
        self.total_drag=0
        self.back_drag=0
        self.cur_task=-1
        self.restart_count=0
        self.litright=0
        self.litsubmit=0
        self.midright=0
        self.midsubmit=0
        self.bigright=0
        self.bigsubmit=0

        self.init_sides()


    def init_sides(self):
        self.sides = dict()
        self.sides['big1']=Side('big1',False)
        self.sides['big2']=Side('big2', False)
        self.sides['big3']=Side('big3', False)
        self.sides['big4']=Side('big4', True)
        self.sides['big5']=Side('big5', True)

        self.sides['mid1']=Side('mid1', False)
        self.sides['mid2']=Side('mid2', False)
        self.sides['mid3']=Side('mid3', False)
        self.sides['mid4']=Side('mid4', True)
        self.sides['mid5']=Side('mid5', True)

        self.sides['lit1']=Side('lit1', False)
        self.sides['lit2']=Side('lit2', False)
        self.sides['lit3']=Side('lit3', False)
        self.sides['lit4']=Side('lit4', True)
        self.sides['lit5']=Side('lit5', True)

    def measure_side(self,side_name):
        self.sides[side_name].change_times+=1

    def cal_measure_stats(self):
        self.litvalid_measured = 0
        self.lit_measured = 0
        self.midvalid_measured = 0
        self.mid_measured = 0
        self.bigvalid_measured = 0
        self.big_measured = 0
        for side_name in self.sides.keys():
            if side_name.startswith('big'):
                if self.sides[side_name].change_times>0:
                    if self.sides[side_name].valid:
                        self.bigvalid_measured+=1
                    self.big_measured+=1
            elif side_name.startswith('mid'):
                if self.sides[side_name].change_times>0:
                    if self.sides[side_name].valid:
                        self.midvalid_measured+=1
                    self.mid_measured+=1
            elif side_name.startswith('lit'):
                if self.sides[side_name].change_times>0:
                    if self.sides[side_name].valid:
                        self.litvalid_measured+=1
                    self.lit_measured+=1

    def ref_check(self,is_right):
        if is_right:
            self.correct_ref+=1
        self.total_ref+=1

    def drag(self,back):
        if back:
            self.back_drag+=1
        self.total_drag+=1

    def go2task(self,
                task_htm #html page url
                ):
        self.cur_task=task_htm

    def click_restart(self):
        if self.cur_task=='801.htm':
            self.restart_count+=1

    def print_stats(self):
        self.cal_measure_stats()
        print ('id: '+str(self.id))
        if self.total_ref>0:
            print ('correct_ref percentage: '+str(self.correct_ref*1.0/self.total_ref))
        else:
            print ('correct_ref percentage: no ref action')
        print ("good drag percentage: "+str((self.total_drag-(self.back_drag*2))*1.0/self.total_drag))
        print ("restart count "+str(self.restart_count))
        print ("little submit correct percentage: "+str(self.litright*1.0/self.litsubmit))
        print ("middle submit correct percentage: " + str(self.midright * 1.0 / self.midsubmit))
        print ("big submit correct percentage: " + str(self.bigright * 1.0 / self.bigsubmit))
        print ("little_valid,little_total,mid_valid,mid_total,big_valid,big_total: "+str(self.litvalid_measured)+","+str(self.lit_measured)+"," \
        +str(self.midvalid_measured)+","+str(self.mid_measured)+","+str(self.bigvalid_measured)+","+str(self.big_measured))

    def gen_stats(self):
        self.cal_measure_stats()
        id=str(self.id)
        if self.total_ref > 0:
            correct_ref_p=str(self.correct_ref * 1.0 / self.total_ref)
        else:
            correct_ref_p=str(-1)
        good_drag_p=str((self.total_drag - (self.back_drag * 2)) * 1.0 / self.total_drag)
        restart_count=str(self.restart_count)
        #print 'test-----litsubmit:' + str(self.litsubmit)
        litsubmit_correct_p=str(quotient(self.litright, self.litsubmit))
        midsubmit_correct_p=str(quotient(self.midright, self.midsubmit))
        bigsubmit_correct_p=str(quotient(self.bigright, self.bigsubmit))
        stats=[id,correct_ref_p,good_drag_p,restart_count,litsubmit_correct_p,midsubmit_correct_p,bigsubmit_correct_p,self.litvalid_measured,self.lit_measured,
               self.midvalid_measured,self.mid_measured,self.bigvalid_measured,self.big_measured]
        return stats
    
def quotient(a, b):
    if b != 0:
        return a * 1.0 / b
    else:
        return 0
    

def parse_obj_id(s,stu):

    if s.__contains__('#'):
        rs = s.split('#')[1]
    else:
        rs = s[s.rindex('/')+1:]

    if rs.__contains__('?'):
        rs=rs.split('?')[0]
    if rs=='restart':
        stu.click_restart()
    return rs

def parse_obj_for_complete(s):
    if s.__contains__('#'):
        if s[s.rindex('/')+1:].split('#')[1]=='statistic':
            return s[s.rindex('/') + 1:].split('#')[0]

def parse_verb_id(s):
    s=s[s.rindex('/')+1:]
    if s.__contains__(','):
        return s[:s.index(',')]
    else:
        return s

def verb_launch(json_obj,
                stu #class Student
                ):
    obj=parse_obj_id(json_obj['object']['id'],stu)
    if web_task_map.has_key(obj):
        stu.go2task(obj)
        if debug:
            print ("launched "+ web_task_map[obj])
    if obj.endswith('json'):   #library reference
        is_right=json_obj['result']['score']['raw']
        stu.ref_check(is_right)

def verb_complete(json_obj):
    obj=parse_obj_for_complete(json_obj['object']['id'])
    if web_task_map.has_key(obj):
        if debug:
            print  ("completed "+ web_task_map[obj])
            print (json_obj['result']['response'])

def verb_drag(json_obj,
              stu #class Student
              ):
    obj = parse_obj_id(json_obj['object']['id'],stu)
    if (obj!='women') & (obj!='man') & (obj!='boy') & (obj!='girl'): #drag back
        stu.drag(True)
    else:
        stu.drag(False)

def parse_submit(json_obj,obj,stu):
    verb=json_obj['verb']['id']
    verb=verb[verb.rindex('/') + 1:]
    verb,num,right=verb.split(',')
    if obj=='litsubmit':
        if right=='1':
            stu.litright+=1
        stu.litsubmit+=1
    elif obj=='midsubmit':
        if right=='1':
            stu.midright+=1
        stu.midsubmit+=1
    elif obj=='bigsubmit':
        if right=='1':
            stu.bigright+=1
        stu.bigsubmit+=1

def parse_701_measure(json_obj,stu): #check whether the student submitted the right capacity of the tent
    verb = json_obj['verb']['id']
    verb = verb[verb.rindex('/') + 1:]
    verb,valid,right,line=verb.split(',')
    stu.measure_side(line)


def process_one_stu(stu_id):

    f_path='./data/20170328/'+stu_id+'.json'
    stu=Student(stu_id)

    log_data=[]
    with open(f_path) as f:
        log_data=json.load(f)

    objs=dict()
    actors=dict()
    verbs=dict()

    for i in range(0,len(log_data)):
        #print log_data[i]['object']['id']
        obj_id=parse_obj_id(log_data[i]['object']['id'],stu)
        actor_id = log_data[i]['actor']['name']
        verb_id = parse_verb_id(log_data[i]['verb']['id'])

        if verb_id=='launched':
            verb_launch(log_data[i],stu)
        elif verb_id=='completed':
            verb_complete(log_data[i])
        elif verb_id=='drag':
            verb_drag(log_data[i],stu)

        if objs.has_key(obj_id):
            objs[obj_id]+=1
        else:
            objs[obj_id]=1
        if (verb_id=='click') & ((obj_id=='bigsubmit') | (obj_id=='midsubmit') | (obj_id=='litsubmit')):
            parse_submit(log_data[i],obj_id,stu)
        if (stu.cur_task=='701.htm') & ((obj_id=='yes1') | (obj_id=='yes2') | (obj_id=='yes3')):
            parse_701_measure(log_data[i],stu)

        if actors.has_key(actor_id):
            actors[actor_id] += 1
        else:
            actors[actor_id] = 1

        if verbs.has_key(verb_id):
            verbs[verb_id] += 1
        else:
            verbs[verb_id] = 1

    return stu


stu_ids=['stu1','stu2','stu3','stu4','stu5','stu6','stu7','stu8','stu9','stu10','stu11','stu12','stu13','stu15','stu16','stu17','stu18','stu20',
         'stu21','stu22','stu23','stu24','stu25','stu27','stu28','stu29','stu32','stu35','stu37','stu38','stu39','stu40']
#stu_ids=['stu29']
students=dict()

for id in stu_ids:
    students[id]=process_one_stu(id)

data=[]
for stu in students.values():
    #stu.print_stats()
    data.append(stu.gen_stats())

d=pd.DataFrame(data=data,columns=get_title())
d.to_csv('test.csv')