# -*- coding: utf-8 -*-
from DataManager import DataManager
from ScheduleCalculator import ScheduleCalculator
from time import time

class ContentManager():
    def __init__(self,cname = None):
        self.course_name = cname

    def course(self, id):
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

        raise ValueError('Undefined content id: {}'.format(id))

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

    def __registration(self):

        return [
            {'chart':'/chart/geography/',
             'text':u'якийсь текст'},]

    def __geography(self):
        content = {'page': u'Географічний розподіл по областям України'}
        with DataManager() as dm:
            content['geography'], content['without_location'] = dm.geography(self.course_name)
        return 'course/geography.html', content

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

    def profile(self,username):
        content = {'page':u'Ваш профіль'}
        with DataManager() as dm:
            content['courses'] = dm.getCoursesResult(username)
            content['name'],content['email'],content['gender'],content['year'],content['education'],content['aim'] = dm.getUserData(username)
        return 'profile.html', content

    def manage_registration(self):
        content = {'page': u'Управління запитами на раєстрацію'}
        data = [{'username':'Ivan', 'email':'ivan1322@gmail.com'},{'username':'Olexandr', 'email':'olexa3232@gmail.com'},{'username':'Evgen', 'email':'evgen5959@gmail.com'}]
        content['data'] = data
        return 'manage_registration.html', content

    def schedule(self,id):
        calculator = ScheduleCalculator(id)
        content = {}
        content['schedule'] = calculator.getSchedule(self.course_name)
        return 'schedule.html',content

    def predict(self,id):
        content = {}
        content['data'] = [[u'',95],[u'',5]]
        content['partition'] = [[u'Завершили курс',1035],[u'В процесі',12654],[u'Тільки зараєструвалися на курс',774],[u'Перший курс для користувача в системі',560]]
        content['count'] = 15023
        content['start_time'] = '2017-02-01'
        content['start_enrollment_time'] = '2016-11-01'
        content['weeks_amount'] = 7
        return 'predict.html', content
