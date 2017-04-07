from util import Util

web_task_map={
              '1101.htm':'classify ancient poetry(title)',
              '1102.htm':'classify ancient poetry(content)',
              '1103.htm':'classify ancient poetry(explanation)',
              '1104.htm':'classify ancient poetry(analysis)',
              '1305.htm':'history and culture',
              '1401.htm':'view the beauty of the yellow river',
              '1501.htm':'journey to the yellow river'}

def main():
    data = Util.data_read('PSA-T003')
    Util.parse(data, web_task_map)
    
if __name__ == "__main__": main()