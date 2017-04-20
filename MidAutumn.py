from util import Util

web_task_map={
              '601.htm':'mid-autumn custom',
              '1301.htm':'ask questions about the moon',
              '1302.htm':'reflect poetry about the moon',
              '1601.htm':'prepare mooncake for the guests',
              '1709.htm':'suggestions about buying mooncake',
              '1710.htm':'persuade grandparents'}


def main():
    data = Util.data_read('PSA-T0008')
    Util.parse(data, web_task_map)
    
if __name__ == "__main__": main()