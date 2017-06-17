import numpy as np
import pandas as pd
from sklearn import linear_model
from sklearn.cross_validation import cross_val_score
from sklearn.naive_bayes import GaussianNB
from imblearn.under_sampling import RandomUnderSampler
from imblearn.under_sampling import NeighbourhoodCleaningRule

class Predictor():
    def __init__(self):
        self.n_jobs = 10
        self.cv = 10
        self.classifier = GaussianNB()
        self.samplers = [NeighbourhoodCleaningRule(n_jobs=self.n_jobs),RandomUnderSampler()]
        self.features = None

    def fit(self, studentmodule, certificates):
        self.features = self.transformFeatures(studentmodule, certificates)
        X = self.features[self.features.columns[:-1]]
        y = self.features.status
        if len(self.features) > 50000:
            sampler = self.samplers[1]
        else:
            sampler = self.samplers[0]
        X, y = sampler.fit_sample(X, y)
        score = cross_val_score(self.classifier, X, y, cv=self.cv, n_jobs=self.n_jobs)
        self.classifier.fit(X, y)
        return np.mean(score)

    def transformFeatures(self, studentmodule, certificates):
        print 'certificates {0}'.format(len(certificates))
        modules = studentmodule.module_id.unique().tolist()
        print 'tatal users with problems {0}'.format(len(studentmodule.user_id.unique()))
        result = []
        for module in modules:
            first = studentmodule[studentmodule.module_id == module].created.min()
            result.append({'name': module, 'date': first})
        labels = map(lambda x: x['name'], sorted(result, key=lambda x: x['date']))
        rebased = studentmodule.pivot(index='user_id', columns='module_id', values='grade')
        rebased = rebased[labels]
        print 'rebased {0}'.format(len(rebased))
        features = pd.merge(rebased, certificates, how='left', left_index=True, right_index=True).fillna(0)
        print 'features {0}'.format(len(features))
        return features

    def predictAll(self):
        X = self.features[self.features.columns[:-1]]
        result = self.classifier.predict(X)
        return pd.DataFrame(index=X.index,data=result, columns=['prediction'])

    def predict(self, user_id):
        raise NameError('not implemented')