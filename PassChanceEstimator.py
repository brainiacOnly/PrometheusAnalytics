import numpy as np
import pandas as pd
from sklearn import linear_model
from sklearn.cross_validation import cross_val_predict
from sklearn.naive_bayes import GaussianNB

class PassChanceEstimator():
    def __init__(self):
        self.__model = None
        self.__u_features = None
        self.__res_features = None

    #get features
    def __getProblemResultFeatures(self,sm):
        #sm = sm[sm.module_type == 'problem']
        modules = sm.module_id.unique().tolist()
        result = []
        for module in modules:
            first = sm[sm.module_id == module].created.min()
            result.append({'name':module,'date':first})
        labels = map(lambda x: x['name'],sorted(result,key=lambda x: x['date']))
        rebased = sm.pivot(index='user_id',columns='module_id',values='grade')
        rebased = rebased[labels].fillna(0)
        return rebased

    def __getUserDataFeatures(self,users,cert):
        u = pd.DataFrame(users[['gender','year_of_birth','level_of_education']],index=users.user_id)
        c = cert.set_index(cert.user_id)[['grade','status']]
        c['status'] = c.apply(lambda x: 1 if x.status == 'downloadable' else 0,1)
        return c.join(u)

    def __lastPassedTest(self,user_id):
        features = self.__res_features.ix[user_id].tolist()
        index = len(features)
        for i in reversed(features):
            if i != 0:
                break
            index -= 1
        if index == 0:
            index = len(self.__res_features.columns)
        return index

    def fit(self,data,users,cert,user_id):
        print 'start fitting model'
        self.__res_features = self.__getProblemResultFeatures(data)
        self.__u_features = self.__getUserDataFeatures(users,cert)

        last = self.__lastPassedTest(user_id)
        cols = self.__res_features.columns[:last].tolist()
        dataset = self.__u_features.join(self.__res_features)
        data = dataset[cols].fillna(0)
        Y = dataset.status

        self.__model = GaussianNB()
        predicted = cross_val_predict(self.__model, data, Y)
        score = float(np.sum(predicted == Y))/len(data)
        self.__model.fit(data,Y)
        print 'fitting model finished'
        return score

    def predict(self,user_id):
        print 'predicting...'
        last = self.__lastPassedTest(user_id)
        cols = self.__res_features.columns.tolist()[:last]
        return self.__model.predict(self.__res_features[cols].ix[user_id].tolist())
