# -*- coding: utf-8 -*-
import datetime
import numpy as np
from DataManager import DataManager
import time
import copy
from PassChanceEstimator import PassChanceEstimator

class ScheduleCalculator():
    def __init__(self,id):
        self.user_id = id

    def __checkEnrolment(self,course_id):
        with DataManager() as dm:
            answer = dm.checkEnrolment(self.user_id,course_id)
        return answer

    def __getPersonalizedSchedule(self,course_id):
        start_time = time.time()
        with DataManager() as dm:
            s = time.time()
            sm = dm.studentmodule(course_id, 'problem')
            print "ELAPCED for studentmodule reading - {0}".format(time.time() - s)
            users = dm.users()
            cert = dm.certificates(course_id)
            courseStructure = dm.getCourseStructure(course_id)
        data_retrieving_time = time.time() - start_time
        print 'ELAPCED(data retrieving for __getPersonalizedSchedule) - ' + str(data_retrieving_time)

        registered = cert.user_id.unique()
        users = users[users.user_id.isin(registered)]

        classifier = PassChanceEstimator()
        fit_start_time = time.time()
        score = classifier.fit(sm,users,cert,self.user_id)
        fit_time = time.time() - fit_start_time
        predict_start_time = time.time()
        answer = classifier.predict(self.user_id)
        predict_time = time.time() - predict_start_time
        print 'score %f' % score
        print 'answer %d' % answer

        if score > 0.9 and answer == 0:
            print 'make best practices schedule'
            schedule = self.__makeBestPracticesSchedule(courseStructure,sm,cert)
        else:
            print 'aproximate schedule'
            schedule = self.__aproximateSchedule(courseStructure, sm[sm.user_id == self.user_id])

        elapced_time = time.time() - start_time
        print 'ELAPCED(__getPersonalizedSchedule) - ' + str(elapced_time)
        print 'ELAPCED#STAT(__getPersonalizedSchedule) {0}% for data retrieving'.format(data_retrieving_time / elapced_time * 100)
        print 'ELAPCED#STAT(__getPersonalizedSchedule) {0}% for fit execution'.format(fit_time / elapced_time * 100)
        print 'ELAPCED#STAT(__getPersonalizedSchedule) {0}% for predict execution'.format(predict_time / elapced_time * 100)

        return schedule

    def __makeBestPracticesSchedule(self,weeks,sm,cert):
        start_time = time.time()
        weeks = self.__fillPassedModules(weeks,sm[sm.user_id == self.user_id])

        #v_interval, v_delay = self.__searchAverageGoodPattern(sm,cert,'video')
        #p_interval, p_delay = self.__searchAverageGoodPattern(sm,cert,'problem')
        v_interval, v_delay = datetime.timedelta(days=5),datetime.timedelta(days=2)
        p_interval, p_delay = datetime.timedelta(days=7),datetime.timedelta(days=2)

        weeks = self.__aproximate(weeks,v_interval,v_delay,p_interval,p_delay)
        print 'ELAPCED(__makeBestPracticesSchedule) - ' + str(time.time() - start_time)

        return weeks

    def __searchAverageGoodPattern(self,data,cert,module):
        success = cert[cert.status == 1].user_id
        data = data[data.user_id.isin(success)]


    def __calculatePersonalIntervalDelay(self,schedule,data,module):
        weeks = copy.deepcopy(schedule)
        print 'weeks 1'
        print map(lambda x: len(x[module]),weeks)
        for week in weeks:
            week[module] = filter(lambda x: x['begin'] is None, week[module])
        print 'weeks 2'
        print map(lambda x: len(x[module]), weeks)
        print 'intervals preview'
        print [map(lambda x: x['begin'],week[module]) for week in weeks if len(week[module]) > 0]
        intervals = [max(map(lambda x: x['end'],week[module])) - min(map(lambda x: x['begin'],week[module])) for week in weeks if len(week[module]) > 0]
        delays=[min(map(lambda x: x['begin'],week[module])) for week in weeks if len(week[module])>0]
        delays = [delays[i] - delays[i-1] for i in range(1,len(delays))]

        return sum(intervals, datetime.timedelta(0)) / len(intervals),sum(delays, datetime.timedelta(0)) / len(delays)

    def __aproximateSchedule(self, weeks, data):
        start_time = time.time()
        print 'before filling passed modules'
        #print #[map(lambda x: x['begin'],week['videos']) for week in weeks if len(week['videos']) > 0]
        weeks = self.__fillPassedModules(weeks,data)

        video_interval, video_delay = self.__calculatePersonalIntervalDelay(weeks,data,'videos')
        problem_interval, problem_delay = self.__calculatePersonalIntervalDelay(weeks,data,'problems')

        weeks = self.__aproximate(weeks,video_interval,video_delay,problem_interval,problem_delay)
        print 'ELAPCED(__aproximateSchedule) - ' + str(time.time() - start_time)

        return weeks

    def __aproximate(self,weeks,v_interval, v_delay, p_interval, p_delay):
        v_current = datetime.datetime.now()
        p_current = v_current
        for week in weeks:
            n = len(week['videos'])
            for i in range(n):
                if week['videos'][i]['begin'] is None:
                    week['videos'][i]['begin'] = v_current + (v_interval/n)*i
                    week['videos'][i]['end'] = v_current + (v_interval/n)*(i+1)
            p_current = v_current + v_interval
            for problem in week['problems']:
                if problem['begin'] is None:
                    problem['begin'] = p_current
                    problem['end'] = p_current + p_interval
            p_current += p_delay
            v_current += v_delay

        return weeks

    def __fillPassedModules(self,weeks,data):
        data.to_csv('problem_data.csv')
        import json
        with open('weeks.json', 'w') as outfile:
            json.dump(weeks, outfile, ensure_ascii=True)
        for week in weeks:
            for video in week['videos']:
                if len(np.intersect1d(video['children'], data.module_id)) > 0:
                    min_date = data[data.module_id.isin(video['children'])].created.min()
                    max_date = data[data.module_id.isin(video['children'])].modified.max()
                    video['begin'] = min_date
                    video['end'] = max_date
                else:
                    video['begin'] = None
                    video['end'] = None
            for problem in week['problems']:
                if len(np.intersect1d(problem['children'], data.module_id)) > 0:
                    min_date = data[data.module_id.isin(problem['children'])].created.min()
                    max_date = data[data.module_id.isin(problem['children'])].modified.max()
                    problem['begin'] = min_date
                    problem['end'] = max_date
                else:
                    problem['begin'] = None
                    problem['end'] = None

        return weeks

    def getSchedule(self,course_id):
        start_time = time.time()
        schedule = []
        if self.__checkEnrolment(course_id):
            print 'I am going to calculate personalized schedule...'
            schedule = self.__getPersonalizedSchedule(course_id)
        else:
            print 'I am going to calculate default schedule...'
            schedule =self.__getDefaultSchedule(course_id)
        print 'schedule has been calculated. Filling the timeline...'
        schedule = self.__fillTimeline(schedule)
        print 'ELAPCED(getSchedule) - ' + str(time.time() - start_time)

        return schedule

    def __getTimelineRow(self,position,name,begin,end):
        return {'position':position,'name': name,'begin':[begin.year,begin.month,begin.day],'end':[end.year,end.month,end.day]}

    def __getDefaultSchedule(self,course_id):
        start_time = time.time()
        with DataManager() as dm:
            weeks = dm.getCourseStructure(course_id)

        print '{0} weeks were retreived from mongoDb for default schedule'.format(len(weeks))
        video_interval = datetime.timedelta(days=5)
        problem_interval = datetime.timedelta(days=2)
        problem_deadline = datetime.timedelta(days=7)
        current = datetime.datetime.now()

        for week in weeks:
            for video in week['videos']:
                video['begin'] = current
                video['end'] = current + video_interval/len(week['videos'])
                current = video['end']

            for problem in week['problems']:
                problem['begin'] = current
                problem['end'] = current + problem_deadline
            current += problem_interval

        print 'ELAPCED(__getDefaultSchedule) - ' + str(time.time() - start_time)
        return weeks

    def __fillTimeline(self, weeks):
        timeline = []
        print 'start filling timeline for {0}'.format(len(weeks))
        for week in weeks:
            for video in week['videos']:
                begin = video['begin']
                end = video['end']
                name = video['name']
                timeline.append(self.__getTimelineRow(week['name'],name,begin,end))

            for problem in week['problems']:
                begin = problem['begin']
                end = problem['end']
                name = problem['name']
                timeline.append(self.__getTimelineRow(week['name'],name,begin,end))

        return timeline
