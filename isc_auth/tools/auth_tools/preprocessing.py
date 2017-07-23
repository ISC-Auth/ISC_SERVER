#encoding:utf8
import json
from pprint import pprint
import math
import numpy as np
from scipy.spatial.distance import euclidean,cosine,hamming
from operator import itemgetter


feature_size = 10
n_samples = 2
gate = -60

class WiFiDataset:
    def __init__(self,paths,path_labels):
        '''
        paths => 路径列表
        path_labels => 该路径下所有记录的标签
        '''
        self.X = None
        self.y = None
        self.paths = paths
        self.path_labels = path_labels

    def read_raw_records_from_raw_file(self,path):
        '''
        raw_records => [{'mobile':[{'BSSID:'xxx','RSSI':xx},{}],'pc':...}]
        '''
        raw_records = []
        with open(path) as f:
            for line in f:
                if line != '' or line is not None:
                    raw_records.append(json.loads(line.strip()))
        # adjust_raw_records = []
        # for pc_idx in range(len(raw_records)-1):
        #     new_record = {'mobile':raw_records[mobile_idx]['mobile'] ,'pc':raw_records[pc_idx]['pc']}
        #     adjust_raw_records.append(new_record)
        #     mobile_idx = pc_idx + 1
        # return adjust_raw_records
        return raw_records

    def transform_raw_records(self,raw_records):
        '''
        return records : [{'mobile':{'id':rssi},'pc':{'id':rssi}}]
        '''
        records = []
        for raw_record in raw_records:
            record = {'mobile':{},'pc':{}}
            for device in ('mobile','pc'):
                d_wifis = raw_record[device]
                new_d_wifis = record[device]
                for d_wifi in d_wifis:
                    new_d_wifis[d_wifi['BSSID']] = float(d_wifi['RSSI'])
            records.append(record)

        return records


    def __add_records(self,sum_records,cur_records):
        for device in ("mobile","pc"):
            d_sum_records = sum_records[device]
            d_cur_records = cur_records[device]
            for bssid,rssi in d_cur_records.items():
                sum_rssi = d_sum_records.get(bssid,0) + rssi
                d_sum_records[bssid] = sum_rssi

    def __ave_records(self,sum_records,n_samples):
        for device in ("mobile","pc"):
            d = sum_records[device]
            for bssid,rssi in d.items():
                d[bssid] = rssi/n_samples
        return sum_records


    def make_average(self,records,n_samples):
        ave_records = []
        times = len(records)//n_samples
        for time in range(0,times):
            record_idx = time * n_samples
            sum_records = {"mobile":{},"pc":{}}
            for i in range(n_samples):
                self.__add_records(sum_records,records[record_idx+i])
            ave_records.append(self.__ave_records(sum_records,n_samples))
        last_record = (len(records)//n_samples)*n_samples
        if last_record == len(records):
            return ave_records


        remain_records = {"mobile":{},"pc":{}}
        for record_idx in range(last_record,len(records)):
            self.__add_records(remain_records,records[record_idx])
        ave_records.append(self.__ave_records(remain_records,len(records)%n_samples))
        return ave_records

    def make_average_overlap(self,records,n_samples):
        ave_records = []
        for start_idx in range(len(records)-n_samples+1):
            sum_records = {"mobile":{},"pc":{}}
            for i in range(n_samples):
                self.__add_records(sum_records,records[start_idx+i])
            ave_records.append(self.__ave_records(sum_records,n_samples))
        print(len(ave_records))
        return ave_records


    def create_dataset(self,records,labels):
        '''
        构建数据集
        '''
        assert len(records) == len(labels)
        X = []
        extractor = WiFiFeatureExtractor()
        for record in records:
            X.append(extractor.extract_feature(record))

        y = labels
        return X,y

    def run_train_test_seq(self,test_ratio):
        train_X,train_y,test_X,test_y = [],[],[],[]
        for path,path_label in zip(self.paths,self.path_labels):
            raw_records = self.read_raw_records_from_raw_file(path)
            records = self.transform_raw_records(raw_records)
            # records = self.make_average(records,n_samples)
            # records = self.make_average_overlap(records,n_samples)
            labels = [path_label  for i in range(len(records))]
            subX,suby = self.create_dataset(records,labels)
            train_size = int(len(subX) * (1-test_ratio))
            train_X.extend(subX[:train_size])
            train_y.extend(suby[:train_size])
            test_X.extend(subX[train_size:])
            test_y.extend(suby[train_size:])
        return np.array(train_X),np.array(train_y),np.array(test_X),np.array(test_y)

    def run(self):
        assert len(self.paths) == len(self.path_labels)
        X,y = [],[]
        for path,path_label in zip(self.paths,self.path_labels):
            raw_records = self.read_raw_records_from_raw_file(path)
            records = self.transform_raw_records(raw_records)
            print(path)
            #do average
            # records = self.make_average(records,n_samples)
            # records = self.make_average_overlap(records,n_samples)
            labels = [path_label  for i in range(len(records))]
            subX,suby = self.create_dataset(records,labels)
            X.extend(subX)
            y.extend(suby)
        self.X = np.array(X)
        self.y = np.array(y)



class WiFiFeatureExtractor:
    '''
    从一次记录（收集）中提取WIFI特征
    '''
    def __init__(self):
        pass

    def __do_init(self):
        self.record = None   #{'mobile':{'id':rssi},'pc':{'id':rssi}}
        # numpy array shape = 2 * sizeof(union_bssid) 0:mobile 1:pc
        self.union_rssi = None
        self.inter_rssi = None
        self.union_bssid = []
        self.inter_bssid = []

    def transform_raw_record(self,raw_record):
        '''
        return record : {'mobile':{'id':rssi},'pc':{'id':rssi}}
        '''
        record = {'mobile':{},'pc':{}}
        for device in ('mobile','pc'):
            d_wifis = raw_record[device]
            new_d_wifis = record[device]
            for d_wifi in d_wifis:
                new_d_wifis[d_wifi['BSSID']] = float(d_wifi['RSSI'])
        return record

    def rssi_filter(self,record,gate):
        new_record = {"mobile":{},"pc":{}}
        for device in ("mobile","pc"):
            for bssid,rssi in record[device].items():
                if rssi > gate:
                    new_record[device][bssid] = rssi
        return new_record

    def pre_transform_records(self,record):
        '''
        record : {'mobile':{'id':rssi},'pc':{'id':rssi}}
        return
            union_rssi: numpy.array shape = 2 * sizeof(union_bssid) 0:mobile 1:pc
            inter_rssi: numpy.array shape = 2 * sizeof(union_bssid) 0:mobile 1:pc
        '''
        #赋值record
        record = self.rssi_filter(record,gate)
        self.record = record

        #计算bssid的交集和并集
        union_bssid = list(set(record['mobile'].keys()).union(record['pc'].keys()))
        inter_bssid = list(set(record['mobile'].keys()).intersection(record['pc'].keys()))
        self.union_bssid = union_bssid
        self.inter_bssid = inter_bssid

        #计算交并集种mobile和pc各自记录的RSSI,不存在的为-100
        union_rssi = np.zeros((2,len(union_bssid)))
        inter_rssi = np.zeros((2,len(inter_bssid)))
        for rssi_array,bssid_set in zip((union_rssi,inter_rssi),(union_bssid,inter_bssid)):
            for array_idx,device in enumerate(('mobile','pc')):
                cur_array = rssi_array[array_idx]
                cur_record = record[device]
                for id_idx,bssid in enumerate(bssid_set):
                    cur_array[id_idx] = cur_record.get(bssid,-100)
        self.union_rssi = union_rssi
        self.inter_rssi = inter_rssi


    def jaccard_distance(self):
        return 1 - len(self.inter_bssid)/len(self.union_bssid)

    def euclidean_distance(self):
        rssi_set = self.union_rssi
        return euclidean(rssi_set[0],rssi_set[1])

    def euclidean_distance2(self):
        rssi_set = self.inter_rssi
        if rssi_set.shape[1] == 0:
            return -100
        return euclidean(rssi_set[0],rssi_set[1])/(rssi_set.shape[1])


    def hamming_distance(self):
        rssi_set = self.union_rssi
        bssid_set = self.union_bssid
        return np.sum(np.abs(rssi_set[0]-rssi_set[1]))/len(bssid_set)

    def hamming_distance2(self):
        rssi_set = self.inter_rssi
        bssid_set = self.inter_bssid
        if len(bssid_set) == 0:
            return 100
        return np.sum(np.abs(rssi_set[0]-rssi_set[1]))/len(bssid_set)

    def cosine_distance(self):
        rssi_set = self.union_rssi
        return cosine(rssi_set[0],rssi_set[1])

    def cosine_distance2(self):
        rssi_set = self.inter_rssi
        if rssi_set.shape[1] == 0:
            return 1
        return cosine(rssi_set[0],rssi_set[1])

    def mean_exp_difference2(self):
        rssi_set = self.inter_rssi
        bssid_set = self.inter_bssid
        if len(bssid_set) == 0:
            return np.exp(np.abs(np.array([100])))
        return np.sum(np.exp(np.abs(rssi_set[0],rssi_set[1])))/len(bssid_set)

    def mean_exp_difference(self):
        rssi_set = self.union_rssi
        bssid_set = self.union_bssid
        return np.sum(np.exp(np.abs(rssi_set[0],rssi_set[1])))/len(bssid_set)



    def squared_ranks(self):
        mobile_bssid_rssi = [(bssid,self.record['mobile'][bssid]) for bssid in self.inter_bssid]
        mobile_bssid_rssi = sorted(mobile_bssid_rssi,key=lambda x:x[1])
        pc_bssid_rssi = [(bssid,self.record['pc'][bssid]) for bssid in self.inter_bssid]
        pc_bssid_rssi = sorted(pc_bssid_rssi,key=lambda x:x[1])

        mobile_bssid_rank = {}
        pc_bssid_rank = {}
        for rank,(bssid,rssi) in enumerate(mobile_bssid_rssi):
            mobile_bssid_rank[bssid] = rank

        for rank,(bssid,rssi) in enumerate(pc_bssid_rssi):
            pc_bssid_rank[bssid] = rank


        squared = 0.0
        for bssid in self.inter_bssid:
            squared += (mobile_bssid_rank[bssid] - pc_bssid_rank[bssid])**2

        return squared

    def extract_feature_from_raw_record(self,raw_record):
        record = self.transform_raw_record(raw_record)
        return self.extract_feature(record)

    def extract_feature(self,record):
        '''
        入口函数
        '''
        self.__do_init()
        self.pre_transform_records(record)
        X = np.zeros((feature_size,))
        X[0] = self.jaccard_distance()
        X[1] = self.euclidean_distance()
        X[2] = self.hamming_distance()
        X[3] = self.cosine_distance()
        X[4] = self.mean_exp_difference()
        X[5] = self.squared_ranks()

        X[6] = self.euclidean_distance2()
        X[7] = self.hamming_distance2()
        X[8] = self.cosine_distance2()
        X[9] = self.mean_exp_difference2()
        return X

if __name__ == '__main__':
    paths = ['data/near2.txt']
    path_labels = [1]
    w = WiFiDataset(paths,path_labels)
    w.run()
