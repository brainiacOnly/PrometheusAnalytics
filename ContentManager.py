# -*- coding: utf-8 -*-
from DataManager import DataManager
from ScheduleCalculator import ScheduleCalculator
from Predictor import Predictor
from time import time
import copy
import random
import json
import pandas as pd

class ContentManager():
    def __init__(self,cname = None):
        self.course_name = cname

    def course(self, id, args, request):
        if id == 'main':
            return self.__main()
        if id == 'age':
            return self.__age()
        if id == 'education':
            return self.__education()
        if id == 'gender':
            return self.__gender()
        if id == 'geography':
            return self.__geography()
        if id == 'registration':
            return self.__registration()
        if id == 'finish':
            return self.__finish()
        if id == 'tests':
            return self.__tests()
        if id == 'questions':
            self.__fillProblemNames(args, request)
            return self.__questions(args['problem_id'], args['problems'])

        raise ValueError('Undefined content id: {}'.format(id))

    def __fillProblemNames(self, args, request):
        course_id = args['course']
        with DataManager() as dm:
            args['problems'] = dm.problems(course_id)
        if 'problem_id' not in args or args['problem_id'] not in map(lambda x: x['name'],args['problems']):
            args['problem_id'] = args['problems'][0]['name']
        request.session['problem_id'] = args['problem_id']

    def __main(self):
        with DataManager() as dm:
            data = dm.main(self.course_name)
        content = {'data': data, 'page': u'Сертифікати'}
        return 'course/main.html',content

    def __age(self):
        content = {'page':u'Віковий розподіл'}
        with DataManager() as dm:
            content['age'], content['age_percent'] = dm.age(self.course_name)
        return 'course/age.html',content

    def __education(self):
        content = {'page':u'Розподіл за освітою'}
        with DataManager() as dm:
            content['education'], content['education_percent'] = dm.education(self.course_name)
        return 'course/education.html',content

    def __gender(self):
        content = {'page':u'Гендерний розподіл'}
        with DataManager() as dm:
            content['gender'], content['gender_percent'], content['gender_percent_pass'] = dm.gender(self.course_name)
        return 'course/gender.html',content

    def __finish(self):
        content = {'page':u'Завершення етапів курсу'}
        with DataManager() as dm:
            content['data'] = dm.finish(self.course_name)
        return 'course/finish.html',content

    def __tests(self):
        content = {'page':u'Успішність студентів на тестів'}
        with DataManager() as dm:
            content['data'] = dm.tests(self.course_name)
        return 'course/tests.html', content

    def __registration(self):
        content = {'page': u'Графік реєстрації'}
        with DataManager() as dm:
            content['registration'] = dm.registration(self.course_name)
        return 'course/registration.html', content

    def __geography(self):
        content = {'page': u'Географічний розподіл по областям України'}
        with DataManager() as dm:
            content['geography'], content['without_location'] = dm.geography(self.course_name)
        return 'course/geography.html', content

    def __questions(self, problem_id, problems):
        content = {'page': u'Характер відповідей на питання'}
        with DataManager() as dm:
            problem_info = dm.prolmem_info(self.course_name, problem_id)

        mask = self.__get_answers_mask(problem_info)
        display_info = copy.deepcopy((i for i in problems if i['name'] == problem_id).next())
        j_counter = 0
        for j in display_info['structure']:
            k_counter = 0
            for k in j['options']:
                k['amount'] = mask[j_counter][k_counter]
                k_counter += 1
            j_counter += 1

        print display_info
        content['questions'] = display_info
        return 'course/questions.html', content

    #some magic from parsing edecational json
    def __get_answers_mask(self, values):
        result = {}
        for i in values:
            answer_info = json.loads(i[0])
            for answer, options in answer_info['student_answers'].iteritems():
                for option in options:
                    name = u'{0}_{1}'.format(answer, option)
                    if name in result:
                        result[name] += 1
                    else:
                        result[name] = 1

        def GetNumber(key):
            i = key.index(u'_') + 1
            newkey = key[i:]
            i = newkey.index(u'_')
            return int(newkey[:i])

        question_keys = {}
        ids = list(set(map(GetNumber, result)))
        for i, j in enumerate(ids):
            question_keys[j] = i

        result2 = {}
        for i, j in result.iteritems():
            testNumber = GetNumber(i)
            back_index = i[::-1].index('_')
            choise_number = int(i[len(i) - back_index:])
            testName = question_keys[testNumber]
            if testName not in result2:
                result2[testName] = {choise_number: j}
            else:
                result2[testName][choise_number] = j
        return result2
    def prometheus(self, id):
        if id == 'age':
            return self.__prometheus_age()
        elif id == 'education':
            return self.__prometheus_education()
        elif id == 'gender':
            return self.__prometheus_gender()
        elif id == 'geography':
            return self.__prometheus_geography()
        elif id == 'registration':
            return self.__prometheus_registration()
        elif id == 'popularity':
            return self.__prometheus_popularity()
        else:
            return None

    def __prometheus_age(self):
        content = {'page':u'Віковий розподіл'}
        with DataManager() as dm:
            content['age'] = dm.age_all()
        return 'platform/age.html',content

    def __prometheus_education(self):
        content = {'page':u'Розподіл за освітою'}
        with DataManager() as dm:
            content['education'] = dm.education_all()
        return 'platform/education.html',content

    def __prometheus_gender(self):
        content = {'page':u'Гендерний розподіл'}
        with DataManager() as dm:
            content['gender'] = dm.gender_all()
        return 'platform/gender.html',content

    def __prometheus_registration(self):
        content = {'page': u'Графік реєстрації'}
        with DataManager() as dm:
            content['registration'] = dm.registration_all()
        return 'platform/registration.html', content

    def __prometheus_geography(self):
        content = {'page': u'Розподіл користувачів Prometheus по областям України'}
        with DataManager() as dm:
            content['geography'], content['without_location'] = dm.geography_all()
        return 'platform/geography.html', content

    def __prometheus_popularity(self):
        content = {'page': u'Популярність курсів'}
        with DataManager() as dm:
            content['popularity'] = dm.courses_popularity()
        return 'platform/popularity.html', content

    def profile(self,username):
        content = {'page':u'Ваш профіль'}
        with DataManager() as dm:
            content['courses'] = dm.getCoursesResult(username)
            content['name'],content['email'],content['gender'],content['year'],content['education'],content['aim'] = dm.getUserData(username)
        return 'profile.html', content

    def manage_registration(self):
        content = {'page': u'Управління запитами на раєстрацію'}
        with DataManager() as dm:
            content['data'] = dm.getPendingUsers()
        return 'manage_registration.html', content

    def schedule(self,id):
        calculator = ScheduleCalculator(id)
        content = {}
        content['schedule'] = calculator.getSchedule(self.course_name)
        return 'schedule.html',content

    def predict(self):
        content = {}
        # content['partition'] = [[u'Завершили курс', 1035], [u'В процесі', 12654],
        #                        [u'Тільки зараєструвалися на курс', 774],
        #                        [u'Перший курс для користувача в системі', 560]]
        # content['count'] = 15023
        #content['start_time'] = '2017-02-01'
        #content['start_enrollment_time'] = '2016-11-01'
        #content['weeks_amount'] = 7
        with DataManager() as dm:
            content['partition'] = dm.getUserStatuses(self.course_name)
            content['count'] = sum(map(lambda x: x[1],content['partition']))
            content['first_course'] = dm.countFirstCourse(self.course_name)
            course_info = dm.getCourseInfo(self.course_name)
            content['start_time'] = course_info['metadata']['start']
            content['start_enrollment_time'] = course_info['metadata']['enrollment_start']
            content['weeks_amount'] = len(course_info['definition']['children'])
            studentmodule = dm.studentmodule(self.course_name,'problem',columns=['student_id as user_id', 'module_id', 'grade', 'created'])
            certificates = dm.certificates(self.course_name,'downloadable', True, ['user_id', '1 as status'])
            classifier = Predictor()
            score = classifier.fit(studentmodule, certificates)
            content['accuracy'] = [[u'', score * 100], [u'', (1 - score) * 100]]
            result = classifier.predictAll()
            statusForActive = dm.getStatusForActiveOnCourseUsers(self.course_name)
            statusForInactive = dm.getStatusForInactiveOnCourseUsers(self.course_name)
            result = pd.merge(result, statusForActive, how='left', left_index=True, right_index=True)
            result = pd.concat([result, statusForInactive])
            content['predict_csv'] = result[['email','status','prediction']].values.tolist()

        return 'predict.html', content