# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 14:58:58 2020

@author: 98061
"""

#---------------------------dependencies-----------------------------
import pandas as pd
import numpy as np
#import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import learning_curve
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
# from sklearn.linear_model import LinearRegression
# from sklearn.tree import DecisionTreeRegressor
# from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import time
from copy import deepcopy
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
#---------------------------const value -----------------------------
road_name = ['NanPing_W2E', 'NanPing_E2W', 'FuLong_S2N', 'FuLong_N2S', 'LiuXian_W2E', 'LiuXian_E2W',
             'YuLong_S2N', 'YuLong_N2S', 'XinQu_S2N', 'XinQu_N2S', 'ZhiYuan_S2N', 'ZhiYuan_N2S']
assert(len(road_name)==12)

dict_road_id = {276183:'NanPing_W2E', 276184:'NanPing_E2W', 275911:'FuLong_S2N',  275912:'FuLong_N2S',
                276240:'LiuXian_W2E', 276241:'LiuXian_E2W', 276264:'YuLong_S2N',  276265:'YuLong_N2S',
                276268:'XinQu_S2N',   276269:'XinQu_N2S',   276737:'ZhiYuan_S2N', 276738:'ZhiYuan_N2S'
                }  # map road names to the road ids

dict_road_index = {276183: 0, 276184: 1, 275911: 2,  275912: 3,
                   276240: 4, 276241: 5, 276264: 6,  276265: 7,
                   276268: 8, 276269: 9, 276737: 10, 276738: 11
                   }

models = []
lzc = []
params = {
    'task': 'train',
    'boosting_type': 'gbdt',  # 设置提升类型
    'objective': 'regression_l1',  # 目标函数
    'metric': {'l1'},  # 评估函数
    'num_leaves': 31,  # 叶子节点数
    'learning_rate': 0.1,  # 学习速率
    'feature_fraction': 0.9,  # 建树的特征选择比例
    'bagging_fraction': 0.8,  # 建树的样本采样比例
    'bagging_freq': 5,  # k 意味着每 k 次迭代执行bagging
    'verbose': 1  # <0 显示致命的, =0 显示错误 (警告), >0 显示信息
}
def gen_train(train_data):
    feature = []
    label = [[], [], []]
    for row in range(6, train_data.shape[0]-2):
        tmp = []
        for i in range(6,0,-1):
            tmp.append((train_data.iloc[row-i][0] % 86400) / 600) # related to time
            tmp.append(train_data.iloc[row-i][1])  # TTI
            tmp.append(train_data.iloc[row-i][2])  # num
            tmp.append(train_data.iloc[row-i][3])  # speed
        feature.append(tmp)
        label[0].append(train_data.iloc[row][1])
        label[1].append(train_data.iloc[row+1][1])
        label[2].append(train_data.iloc[row+2][1])
    feature = np.array(feature)
    label = np.array(label)
    return feature, label

def train(train_X, train_y, eval_X, eval_y,road_index):
    # params = {
    #     'booster': 'gbtree',
    #     'objective': 'reg:gamma',
    #     'gamma': 0.1,
    #     'max_depth': 6,
    #     'lambda': 3,
    #     'subsample': 0.7,
    #     'colsample_bytree': 0.7,
    #     'min_child_weight': 3,
    #     'eta': 0.1,
    #     'seed': 1000,
    #     'nthread': 4,
    # }
    # num_round = 1
    # # plst = params.items()
    # evallist = [(deval, 'eval'), (dtrain, 'train')]
    # bst = xgb.train(params, dtrain, num_round, evallist)
    # model_name = road_name[road_index] + ".model"
    # bst.save_model(model_name)
    # return bst
    #model_total = []
    train_y = train_y.T
    eval_y = eval_y.T
    model = [0,0,0]
    #print(train_y.shape)
    for i in range(3):
        if i==0:
            lgb_train1 = lgb.Dataset(train_X,train_y[0])
            lgb_test1 = lgb.Dataset(eval_X,eval_y[0])
            gbm1 = lgb.train(params, lgb_train1, num_boost_round=30, valid_sets=lgb_test1, early_stopping_rounds=5)
            model[i] = gbm1
        if i==1 or i==2:    
            pre1 = model[i-1].predict(train_X,num_iteration=model[i-1].best_iteration)
            tmp = []
            for j in range(pre1.shape[0]):
                tmp.append([pre1[j]])
            tmp = np.array(tmp)
            train_X = np.hstack((train_X,tmp))
            
            pre1 = model[i-1].predict(eval_X,num_iteration=model[i-1].best_iteration)
            tmp = []
            for j in range(pre1.shape[0]):
                tmp.append([pre1[j]])
            tmp = np.array(tmp)
            eval_X = np.hstack((eval_X,tmp))
            
            lgb_train = lgb.Dataset(train_X,train_y[0])
            lgb_test = lgb.Dataset(eval_X,eval_y[0])
            gbm = lgb.train(params, lgb_train, num_boost_round=30, valid_sets=lgb_test, early_stopping_rounds=5)
            model[i] = gbm
            
  
    
    models.append(model)
    #model_total.append(model)
    #models.append(model_total)
    return model
        
    

def gen_test(test_data):
    feature = []
    for row in range(0, test_data.shape[0]-5,6):
        tmp = []
        for i in range(6):
            tmp.append((test_data.iloc[row+i][0] % 86400) / 600) # related to time
            tmp.append(test_data.iloc[row+i][1])  # TTI
            tmp.append(test_data.iloc[row+i][2])  # num
            tmp.append(test_data.iloc[row+i][3])  # speed
        feature.append(tmp)
    feature = np.array(feature)
    return feature
    


def evaluate(model, X, y):
    mae = 0
    y_t = y.T
    lst = predict(model,X)
    re = [[],[],[]]
    for i in range(0,len(lst),6):
        re[0].append(lst[i])
        re[1].append(lst[i+1])
        re[2].append(lst[i+2])
    for i in range(3):
        mae += mean_absolute_error(y_t[i],re[i])*len(re[i])
        
    print("mae:", mae/(X.shape[0]))
    return mae/(X.shape[0])
    
    

def predict(model,X_test):
    lst = []
    lst1 = []
    lst2 = []
    lst3 = []
    lst1 = model[0].predict(X_test,num_iteration=model[0].best_iteration)
    
    
    pre1 = lst1
    tmp = []
    for j in range(pre1.shape[0]):
        tmp.append([pre1[j]])
    tmp = np.array(tmp)
    X_test = np.hstack((X_test,tmp))
    lst2 = model[1].predict(X_test,num_iteration=model[1].best_iteration)
    
    pre1 = lst2
    tmp = []
    for j in range(pre1.shape[0]):
        tmp.append([pre1[j]])
    tmp = np.array(tmp)
    X_test = np.hstack((X_test,tmp))
    lst3 = model[2].predict(X_test,num_iteration=model[2].best_iteration)
    
    for i in range(lst1.shape[0]):
        lst.extend([lst1[i],lst2[i],lst3[i],0,0,0])
    return lst
    
   
        

def main():
    mae = 0
    #pre_df_lst = [0,0,0,0,0,0,0,0,0,0,0,0]
    pre_df_lst = [0,0,0,0,0,0,0,0,0,0,0,0]

    for i in range(12):
        test_data = pd.read_csv("../datasets/stage2_test_"+road_name[i]+".csv", sep=',')
        test_data = test_data.sort_values(by = 'timestamp')
        #X, y = gen_train(train_data)#np array
        #X_test = gen_test(test_data)
        X_filename = 'train_array/X_0103_' + road_name[i] + '.npy'
        X = np.load(X_filename)
        X = X.T
        for j in range(1,90,3):
            X[j] = X[j]*0.01
            
        y_filename = 'train_array/y_0103_' + road_name[i] + '.npy'
        y = np.load(y_filename)
        y = y.T
        X_test_file = 'train_array/test_X_0103_' + road_name[i] + '.npy'
        X_test = np.load(X_test_file)
        X_test = X_test.T
        for j in range(1,90,3):
            X_test[j] = X_test[j]*0.01
        X = X.T
        X_test = X_test.T
        #PCA 
        #pca1 = PCA(n_components = 20)
        #pca2 = PCA(n_components = 20)
        #X = pca1.fit_transform(X)
        #X_test = pca2.fit_transform(X_test)
        
        
        #cluster num calculation
        #X_total = np.vstack((X,X_test))
       # N_CLUSTERS = 1
       # kmeans_model = KMeans(n_clusters = N_CLUSTERS)
       # kmeans_model.fit(X_total)
       # cluster_label = kmeans_model.labels_
        #print(cluster_label)
        
       # train_X, eval_X, train_y, eval_y,cluster_X,cluster_y = train_test_split(X,y,cluster_label[:X.shape[0]],test_size=0.25,random_state=1591545677)
        train_X, eval_X, train_y, eval_y = train_test_split(X,y,test_size=0.25,random_state=1591545677)
        #train_y.shape = (...,3)
        
        model= train(train_X, train_y, eval_X, eval_y,i)
        mae += evaluate(model, eval_X, eval_y)
        #print(X_test)
        pre_df = predict(model,X_test)
        #print(len(pre_df),test_data.shape[0])
        test_data['predict'] = pre_df
        df = pd.DataFrame()
        df['TTI'] = None
        for row in range(0,test_data.shape[0]-5,6):
            tss = test_data.iloc[row+5][0]
            df.loc[tss+600] = test_data.iloc[row][4]
            df.loc[tss+600*2] = test_data.iloc[row+1][4]
            df.loc[tss+600*3] = test_data.iloc[row+2][4]
        pre_df_lst[i] = df
        #pre_df_lst[i] = gen_test(model, test_data)
        #pd.DataFrame.to_csv(pre_df_lst[i], "D:/test_data/"+road_name[i]+"_pred.csv", sep=',')
    print(mae / 12)
    #print(pre_df_lst[0])
    #lzc = pre_df_lst[0]
    
    
    noLabel = pd.read_csv("../stage2_data/stage2/toPredict_noLabel_stage2.csv", sep=',')
    result = pd.DataFrame()
    result['TTI'] = None
    for row in range(noLabel.shape[0]):
        road_id = noLabel.loc[row, 'id_road']
        num = dict_road_index[road_id]
        time_str = noLabel.loc[row, 'time']
        timeArray = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(timeArray)
        #print(timestamp)
        try:
            x = pre_df_lst[num].loc[timestamp]['TTI']
            result.loc[row] = x
        except:
            assert(0)
    #print(time_cost)
    #print(result)
    result.to_csv("../model_result/lgbm0708.csv")
    #pd.DataFrame.to_csv(noLabel['pred'], "D:/test_data/pred_TTI3.csv", sep=',')

if __name__ == "__main__":
    main()