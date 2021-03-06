# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 17:34:23 2017

@author: zhuangzijun
"""

import pandas as pd
from scipy.stats import pearsonr

def main():
    df = pd.read_csv('D:/Data/PSAA/task_score_relevance2.csv', skiprows=1, names=['stuId', '601_score', '601_ol', '601_sl', '601_ml', '601_wl', '601_om', '601_sm', '601_mm', '601_wm', '601_os', '601_ss', '601_ms', '601_ws', '601_on', '601_sn', '601_mn', '601_wn', 
                                                                                           '603_score', '603_ol', '603_sl', '603_ml', '603_wl', '603_om', '603_sm', '603_mm', '603_wm', '603_os', '603_ss', '603_ms', '603_ws', '603_on', '603_sn', '603_mn', '603_wn',
                                                                                           '701_score', '701_ol', '701_sl', '701_ml', '701_wl', '701_om', '701_sm', '701_mm', '701_wm', '701_os', '701_ss', '701_ms', '701_ws', '701_on', '701_sn', '701_mn', '701_wn',
                                                                                           '801_score'])
    
    df2 = pd.read_csv('D:/Data/PSAA/task_score_relevance3.csv', skiprows=1, names=['stuId', '601_score', '601_ol', '601_sl', '601_ml', '601_wl', '601_om', '601_sm', '601_mm', '601_wm', '601_os', '601_ss', '601_ms', '601_ws', '601_on', '601_sn', '601_mn', '601_wn', '601_o!s', '601_s!s', '601_m!s', '601_w!s',
                                                                                           '603_score', '603_ol', '603_sl', '603_ml', '603_wl', '603_om', '603_sm', '603_mm', '603_wm', '603_os', '603_ss', '603_ms', '603_ws', '603_on', '603_sn', '603_mn', '603_wn', '603_o!s', '603_s!s', '603_m!s', '603_w!s',
                                                                                           '701_score', '701_ol', '701_sl', '701_ml', '701_wl', '701_om', '701_sm', '701_mm', '701_wm', '701_os', '701_ss', '701_ms', '701_ws', '701_on', '701_sn', '701_mn', '701_wn', '701_o!s', '701_s!s', '701_m!s', '701_w!s',
                                                                                           '801_score'])
    
    # correlation between scores
    score_df = df[['601_score', '603_score', '701_score', '801_score']]
    score_df['total'] = score_df['601_score'] + score_df['603_score'] + score_df['701_score'] + score_df['801_score']
    #print(score_df)
    corr = score_df.corr(method='pearson')
    #print(corr.loc['total'])
    
    df_601 = df.iloc[:, 1:18]
    df_603 = df.iloc[:, 18:35]
    df_701 = df.iloc[:, 35:52]
    #print(df_601)
    
    # correlation between score and lib
#    corr_601 = corr_pvalue(df_601)
#    print(corr_601)
    
#    corr_603 = corr_pvalue(df_603)
#    print(corr_603)
    
#    corr_701 = corr_pvalue(df_701)
#    print(corr_701)

#    df2_601 = df2[['601_score', '601_os', '601_ss', '601_ms', '601_ws', '601_o!s', '601_s!s', '601_m!s', '601_w!s']]
#    df2_603 = df2[['603_score', '603_os', '603_ss', '603_ms', '603_ws', '603_o!s', '603_s!s', '603_m!s', '603_w!s']]
#    df2_701 = df2[['701_score', '701_os', '701_ss', '701_ms', '701_ws', '701_o!s', '701_s!s', '701_m!s', '701_w!s']]
    
#    corr_601 = corr_pvalue(df2_601)
#    print(corr_601)
    
#    corr_603 = corr_pvalue(df2_603)
#    print(corr_603)
    
#    corr_701 = corr_pvalue(df2_701)
#    print(corr_701)
    
#    concat_df = pd.concat([corr_601, corr_603, corr_701])
#    print(concat_df)
    
    df2['total'] = df2['601_score'] + df2['603_score'] + df2['701_score'] # + df2['801_score']
    df2['total_os'] = df2['601_os'] + df2['603_os'] + df2['701_os']
    df2['total_ss'] = df2['601_ss'] + df2['603_ss'] + df2['701_ss']
    df2['total_ms'] = df2['601_ms'] + df2['603_ms'] + df2['701_ms']
    df2['total_ws'] = df2['601_ws'] + df2['603_ws'] + df2['701_ws']
    df2['total_o!s'] = df2['601_o!s'] + df2['603_o!s'] + df2['701_o!s']
    df2['total_s!s'] = df2['601_s!s'] + df2['603_s!s'] + df2['701_s!s']
    df2['total_m!s'] = df2['601_m!s'] + df2['603_m!s'] + df2['701_m!s']
    df2['total_w!s'] = df2['601_w!s'] + df2['603_w!s'] + df2['701_w!s']
    df2_total = df2[['total', 'total_os', 'total_ss', 'total_ms', 'total_ws', 'total_o!s', 'total_s!s', 'total_m!s', 'total_w!s']]
    corr_total = corr_pvalue(df2_total)
    print(corr_total)    

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