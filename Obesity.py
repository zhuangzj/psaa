from util import Util

web_task_map={
              '1602.htm':'judgement of obesity',
              '1706.htm':'reasons of obesity',
              '1707.htm':'path measurement',
              '1708.htm':'energy calculation'}


def main():
    data = Util.data_read('PSA-T0010')
    Util.parse(data, web_task_map)
    
if __name__ == "__main__": main()