# -*- coding: utf-8 -*-
from DataManager import DataManager
from ScheduleCalculator import ScheduleCalculator

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
        content = {'data':data,'page':u'Сертифікати'}
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
        print 'education done!'
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
        return [
            {'chart':'/chart/geography/',
             'text':u'якийсь текст'},]

    def prometheus(self, id):
        return {
            'age':self.__prometheus_age(),
            'education':self.__prometheus_education(),
            'gender':self.__prometheus_gender(),
            'geography':self.__prometheus_geography(),
            'registration':self.__prometheus_registration(),
            }[id]

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
        return None
    def __prometheus_geography(self):
        return None

    def schedule(self,id):
        calculator = ScheduleCalculator(id)
        content = {}
        content['schedule'] = calculator.getSchedule(self.course_name)
        return 'schedule.html',content

    def profile(self,username):
        content = {'page':u'Ваш профіль'}
        with DataManager() as dm:
            content['courses'] = dm.getCoursesResult(username)
            content['name'],content['email'],content['gender'],content['year'],content['education'],content['aim'] = dm.getUserData(username)
        return 'profile.html', content