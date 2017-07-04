# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 17:34:23 2017

@author: zhuangzijun
"""

import pandas as pd
from scipy.stats import pearsonr

def main():
    df = pd.read_csv('D:/WorkSpace/PSSA/pssa/task_score_relevance2.csv', skiprows=1, names=['stuId', '601_score', '601_ol', '601_sl', '601_ml', '601_wl', '601_om', '601_sm', '601_mm', '601_wm', '601_os', '601_ss', '601_ms', '601_ws', '601_on', '601_sn', '601_mn', '601_wn',
                                                                                           '603_score', '603_ol', '603_sl', '603_ml', '603_wl', '603_om', '603_sm', '603_mm', '603_wm', '603_os', '603_ss', '603_ms', '603_ws', '603_on', '603_sn', '603_mn', '603_wn',
                                                                                           '701_score', '701_ol', '701_sl', '701_ml', '701_wl', '701_om', '701_sm', '701_mm', '701_wm', '701_os', '701_ss', '701_ms', '701_ws', '701_on', '701_sn', '701_mn', '701_wn',
                                                                                           '801_score'])
    
    # correlation between scores
    df2 = df[['601_score', '701_score', '801_score']]
    df2['total'] = df2['601_score'] + df2['701_score'] + df2['801_score']
    #print(df2)
    corr = df2.corr(method='pearson')
    #print(corr)
    
    df_601 = df.iloc[:, 1:18]
    df_603 = df.iloc[:, 18:35]
    df_701 = df.iloc[:, 35:52]
    #print(df_601)
    
    #corr_601 = df_601.corr(method='pearson')
    #print(corr_601.loc['601_score'])
     
    corr_601 = corr_pvalue(df_601)
    print(corr_601)
    
    corr_603 = corr_pvalue(df_603)
    print(corr_603)
    
    corr_701 = corr_pvalue(df_701)
    print(corr_701)
    


def corr_pvalue(df):
    data = []
    y = df.iloc[:, 0]
    for i, col in enumerate(df.columns):
        if i != 0:
            x = df.iloc[:, i]
            peason_corr, p_value = pearsonr(x, y)
            row = {'task_lib': col, 'corr': peason_corr, 'p_value': p_value}
            data.append(row)
    corr_df = pd.DataFrame(data)
    corr_df.set_index('task_lib', inplace=True)
    
    return corr_df

if __name__ == "__main__": main() 