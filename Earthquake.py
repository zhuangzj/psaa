from util import Util

web_task_map={
              '203.htm':'PSA01 sort',
              '201.htm':'PSA02 emergency response',
              '2.htm':'PSA03-01 medical rescue road selection',
              '202.htm':'PSA03-02 classify casualty',
              '301.htm':'PSA03-03 estimate casualty',
              '302.htm':'PSA04-01 road reparation selection',
              '303.htm':'PSA04-02 time estimation',
              '304.htm':'PSA05-01 place satellite phone',
              '306.htm':'PSA05-02 circuit reparation selection',
              '307.htm':'PSA06-01 information selection',
              '308.htm':'PSA06-02 resource calculation',
              '309.htm':'PSA06-03 flight route',
              '310.htm':'PSA06-04 cargo loading',
              '311.htm':'PSA07-01 sort second times'}


def main():
    data = Util.data_read('T0006')
    Util.parse(data, web_task_map)
    
if __name__ == "__main__": main()