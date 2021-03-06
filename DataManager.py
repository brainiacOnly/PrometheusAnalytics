# -*- coding: utf-8 -*-
import os
from django.conf import settings
from time import time
import pandas as pd
import datetime
import numpy as np
import MySQLdb
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import itertools
from Credential import Credential
from xml.dom import minidom
from django.contrib.auth.models import User

class DataManager():
    def __enter__(self):
        settings = Credential.GetSQLSettings()
        self.__connection = MySQLdb.connect(host=settings.Address, port=settings.Port, user=settings.Username, passwd=settings.Password,
                                            db=settings.DatabaseName, charset=settings.Encoding)
        return self

    def __exit__(self, type, value, traceback):
        if self.__connection:
            self.__connection.close()

    def studentmodule(self,course_id, module_type, columns = None):
        if columns == None:
            columns = ['module_id', 'student_id as user_id', 'grade', 'max_grade', 'course_id', 'created', 'modified']
        columnsRequest = ','.join(columns)
        sql = "SELECT {2} from courseware_studentmodule where course_id = '{0}' and module_type = '{1}'".format(course_id, module_type,columnsRequest)
        print sql
        result = pd.read_sql(sql,con=self.__connection)
        return result

    def users(self):
        sql = "SELECT user_id, gender, year_of_birth, level_of_education from auth_userprofile"
        result = pd.read_sql(sql, con=self.__connection)
        return result

    def problems(self, course_id):
        credentials = Credential.GetMongoSettings()
        client = MongoClient(credentials.Address, credentials.Port)
        modules = client.edxapp.modulestore
        org, course, period = course_id.split('/')
        problems = []
        for problem in modules.find({"_id.course": course, "_id.org": org, "_id.category": "problem"}):
            name = problem['_id']['name']
            xml = minidom.parseString(problem['definition']['data']['data'].encode('utf-8'))
            vertical = modules.find_one({"_id.course": course, "_id.org": org, "_id.category": "vertical",
                                         'definition.children': {'$elemMatch': {'$regex': ".*{0}.*".format(name)}}})
            display_name = vertical['metadata']['display_name']
            structure = []
            for node in xml.documentElement.getElementsByTagName('checkboxgroup'):
                #task = node.getAttribute('label')[:80] + '...'
                task = node.getAttribute('label')
                options = [{'correct': i.getAttribute('correct') == 'true', 'text': i.firstChild.nodeValue[:80] + ('...' if len(i.firstChild.nodeValue) > 80 else '')} for i in node.getElementsByTagName('choice')]
                structure.append({'task': task, 'options': options})
            problems.append(
                {'org': org, 'course': course, 'name': name, 'display_name': display_name, 'structure': structure})
        return problems

    def certificates(self, course_id = "", status = "", user_id_as_index = False, columns=['user_id', 'grade', 'course_id', 'status']):
        whereClauses = []
        whereStatement = ""
        if course_id != "":
            whereClauses.append("course_id = '%s'" % course_id)
        if status != "":
            whereClauses.append("status = '%s'" % status)
        if len(whereClauses) > 0:
            whereStatement = " WHERE " + " AND ".join(whereClauses)

        columndRequest = ",".join(columns)
        sql = "SELECT {0} FROM certificates_generatedcertificate".format(columndRequest) + whereStatement
        print sql
        if user_id_as_index:
            result = pd.read_sql(sql, index_col='user_id', con=self.__connection)
        else:
            result = pd.read_sql(sql, con=self.__connection)
        return result

    def main(self,course_name):
        cur = self.__connection.cursor()
        cur.execute("select count(*) from certificates_generatedcertificate where status = 'downloadable' and course_id = '%s'" % course_name)
        downloadable = cur.fetchone()[0]
        cur.execute("select count(*) from certificates_generatedcertificate where status != 'downloadable' and course_id = '%s'" % course_name)
        notPassed = cur.fetchone()[0]

        return [[u'Пройшли',downloadable],[u'Не пройшли',notPassed]]

    def age(self, course_name):
        reristeredYears = pd.read_sql("select u.year_of_birth FROM auth_userprofile u JOIN student_courseenrollment c on u.user_id = c.user_id WHERE c.course_id = '{0}'".format(course_name), con=self.__connection)
        certifiedYears = pd.read_sql("select u.year_of_birth FROM auth_userprofile u JOIN certificates_generatedcertificate c on u.user_id = c.user_id WHERE c.status =  'downloadable' AND c.course_id = '{0}'".format(course_name), con=self.__connection)

        registeredGroups = pd.Series(len(reristeredYears[reristeredYears.year_of_birth.isnull()]), index=[u'Вік не вказано'])
        certifiedGroups = pd.Series(len(certifiedYears[certifiedYears.year_of_birth.isnull()]), index=[u'Вік не вказано'])
        currentYear = datetime.datetime.now().year
        registeredGroups.set_value(u'До 20', len(reristeredYears[ currentYear - reristeredYears.year_of_birth < 20]))
        certifiedGroups.set_value(u'До 20', len(certifiedYears[currentYear - certifiedYears.year_of_birth < 20]))

        for i in range(0,6):
            begin, end = 20+i*5, 20+(i+1)*5
            registeredGroups.set_value(str(begin) + '-' + str(end - 1), len(reristeredYears[(
                                                                                            currentYear - reristeredYears.year_of_birth >= begin) & (
                                                                                            currentYear - reristeredYears.year_of_birth < end)]))
            certifiedGroups.set_value(str(begin) + '-' + str(end - 1), len(certifiedYears[(
                                                                                            currentYear - certifiedYears.year_of_birth >= begin) & (
                                                                                            currentYear - certifiedYears.year_of_birth < end)]))

        registeredGroups.set_value(u'50 і більше', len(reristeredYears[currentYear - reristeredYears.year_of_birth >= 50]))
        certifiedGroups.set_value(u'50 і більше', len(certifiedYears[currentYear - certifiedYears.year_of_birth >= 50]))

        plot_data = pd.concat([pd.DataFrame(registeredGroups.index,index=registeredGroups.index),registeredGroups,certifiedGroups],axis=1,keys=['name','registered','passed'])
        percent_plot_data = pd.concat([pd.Series(registeredGroups.index,index=registeredGroups.index), (certifiedGroups / registeredGroups * 100)],axis=1,keys=['index','percent'])
        percent_plot_data.percent = percent_plot_data.percent.apply(lambda x: int(round(x)))

        return plot_data.values,percent_plot_data.values

    def education(self, course_name):
        registeredCroups = pd.read_sql("SELECT IF(u.level_of_education = '' OR u.level_of_education is null, 'other', u.level_of_education) as name, COUNT( * ) as count FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' group by name" % course_name,con=self.__connection)
        certifiedCroups = pd.read_sql("SELECT IF(u.level_of_education = '' OR u.level_of_education is null, 'other', u.level_of_education) as name, COUNT( * ) as count FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' and c.status = 'downloadable' group by name" % course_name,con=self.__connection)
        certifiedCroups = self.ConsolidateNames(registeredCroups, certifiedCroups)

        plot_data = pd.merge(registeredCroups, certifiedCroups, on=['name'])
        plot_data.columns = ['name', 'registered','passed']
        plot_data.passed = plot_data.passed.apply(lambda x: int(round(x)))
        plot_data.name = plot_data.name.apply(self.map_educaiton)
        percent_plot_data = pd.concat([plot_data.name, (plot_data.passed.astype(float) / plot_data.registered * 100)],axis=1,keys=['name','percent']).fillna(0)
        percent_plot_data.percent = percent_plot_data.percent.apply(lambda x: int(round(x)))
        percent_plot_data.name = percent_plot_data.name.apply(self.map_educaiton)
        return plot_data.values, percent_plot_data.values

    def ConsolidateNames(self, registered, certified):
        if len(registered) == len(certified):
            return certified
        certifiedNames = certified['name'].values.tolist()
        registeredNames = registered['name'].values.tolist()
        lostNames = map(lambda x: [x,0],filter(lambda x: x not in certifiedNames,registeredNames))
        return certified.append(pd.DataFrame(lostNames, columns=certified.columns), ignore_index=True)

    def gender(self,course_name):
        registeredCroups = pd.read_sql("SELECT gender as name, COUNT( * ) as registered FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' group by u.gender" % course_name,con=self.__connection)
        certifiedCroups = pd.read_sql("SELECT gender as name, COUNT( * ) as passed FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' and c.status = 'downloadable' group by u.gender" % course_name,con=self.__connection)
        registeredCroups = registeredCroups[registeredCroups.name.isin(['f','m','o'])]
        certifiedCroups = certifiedCroups[certifiedCroups.name.isin(['f','m','o'])]
        plot_data = pd.merge(registeredCroups,certifiedCroups,how='inner',on='name')
        plot_data = plot_data.fillna(0)
        plot_data.passed = plot_data.passed.apply(lambda x: int(round(x)))
        plot_data.name = plot_data.name.apply(self.map_gender)

        return plot_data.values,plot_data[['name','registered']].values.tolist(),plot_data[['name','passed']].values

    def finish(self,course_name):
        plot_data = pd.read_sql("SELECT module_id, count(*) as amount, min(created) as created_date from courseware_studentmodule where course_id = '{0}' and module_type = 'problem' group by module_id order by created_date".format(course_name), con=self.__connection)
        return plot_data.values.tolist()

    def tests(self,course_name):
        plot_data = pd.read_sql("select module_id, ROUND(AVG(grade/max_grade*100),2) as avg_pass_percent, min(created) as created_date  from courseware_studentmodule where course_id = '{0}' and module_type = 'problem' and grade is not null group by module_id order by created_date".format(course_name), con=self.__connection)
        return plot_data.values.tolist()

    def prolmem_info(self, course_id, problem_id):
        data = pd.read_sql(
            "select state  from courseware_studentmodule where course_id = '{0}' and grade is not null and module_id like '%{1}'".format(
                course_id, problem_id), con=self.__connection)
        return data.values.tolist()

    def geography(self, course_name):
        cur = self.__connection.cursor()
        cur.execute("select count(*) from auth_userprofile au join student_courseenrollment ce on au.user_id = ce.user_id where ce.course_id = '{0}' and au.region_code is null".format(course_name))
        noLocation = cur.fetchone()[0]
        cur.close()
        plot_data = pd.read_sql(
            "select region_code, count(*) as count from auth_userprofile au join student_courseenrollment ce on au.user_id = ce.user_id where ce.course_id = '{0}' and au.region_code is not null group by region_code".format(course_name),
            con=self.__connection)
        regions = pd.read_csv('static\\data\\regions.csv', encoding='utf8')
        plot_data = pd.merge(plot_data, regions, on='region_code')[['region_code', 'region_name', 'count']]
        return plot_data.values.tolist(), noLocation

    def registration(self, course_id):
        plot_data = pd.read_sql(
            "select DATE(created) as created_date, count(*) as amount from student_courseenrollment where course_id = '{0}' group by created_date order by created_date".format(course_id),
            con=self.__connection).values.tolist()
        return plot_data

    def age_all(self):
        sql = "select 'Вік не вказано',  count(*) from auth_userprofile where year_of_birth is NULL " + \
                "union " + \
                "select 'До 20',  count(*) from auth_userprofile where year(curdate()) - year_of_birth < 20 ";
        for i in range(0, 6):
            begin, end = 20 + i * 5, 20 + (i + 1) * 5
            sql += "union " + \
                   "select '{0}-{1}', count(*) from auth_userprofile WHERE YEAR( CURDATE( ) ) - year_of_birth >= {0} and YEAR( CURDATE( ) ) - year_of_birth < {1} ".format(begin, end)

        sql += "union " + \
                "select '50 і більше',  count(*) from auth_userprofile where year(curdate()) - year_of_birth >= 50"
        plot_data = pd.read_sql(sql, con=self.__connection)
        return plot_data.values.tolist()

    def education_all(self):
        plot_data = pd.read_sql("select level_of_education, count(*) from auth_userprofile group by level_of_education",con=self.__connection)
        plot_data.level_of_education = plot_data.level_of_education.apply(self.map_educaiton)
        return plot_data.values.tolist()

    def gender_all(self):
        plot_data = pd.read_sql("select IF(au.gender = '' OR au.gender is null, 'o', au.gender) as person_gender, count(*) from auth_userprofile au group by person_gender",con=self.__connection)
        plot_data.person_gender = plot_data.person_gender.apply(self.map_gender)
        return plot_data.values.tolist()

    def geography_all(self):
        cur = self.__connection.cursor()
        cur.execute("select count(*) from auth_userprofile where region_code is null")
        noLocation = cur.fetchone()[0]
        cur.close()
        plot_data = pd.read_sql("select region_code, count(*) as count from auth_userprofile where region_code is not null group by region_code",con=self.__connection)
        regions = pd.read_csv('static\\data\\regions.csv', encoding='utf8')
        plot_data = pd.merge(plot_data, regions, on = 'region_code')[['region_code','region_name','count']]
        return plot_data.values.tolist(), noLocation

    def registration_all(self):
        plot_data = pd.read_sql(
            "select date(date_joined) as date_registration, count(*) from auth_user group by date_registration order by date_registration",
            con=self.__connection).values.tolist()
        return plot_data

    def courses_popularity(self):
        plot_data = pd.read_sql(
            "select course_id, count(*) as amount from student_courseenrollment group by course_id order by amount desc",
            con=self.__connection).values.tolist()
        courses = pd.read_csv('static\\data\\courses.csv', encoding='utf8').values.tolist()
        courses = {item[0]: item[1:] for item in courses}
        plot_data = [[courses[i[0]][0], i[1]] for i in plot_data if i[0] in courses.keys()]
        #for i in plot_data:
        #    print i[0][0]
        return plot_data

    def __getChildren(self,id,modules):
        ids = id.split('/')
        name = ids[5]
        module = modules.find_one({"_id.name":name})
        if 'definition' in module and 'children' in module['definition']:
            return module['definition']['children']
        return []

    def __getSequentialNameById(self,id,modules,isVideo):
        ids = id.split('/')
        name = ids[5]
        module = modules.find_one({"_id.name":name})
        if not isVideo and 'graded' in module['metadata'] and module['metadata']['graded']:
            return {'name':module['metadata']['display_name'], 'id': id}
        elif isVideo and 'graded' not in module['metadata']:
            return {'name':module['metadata']['display_name'], 'id': id}
        else:
            return None

    def getCourseStructure(self,course_id):
        credentials = Credential.GetMongoSettings()
        client = MongoClient(credentials.Address, credentials.Port)
        modules = client.edxapp.modulestore

        org, course, period = course_id.split('/')
        weeks = []
        for chapter in modules.find({"_id.course":course,"_id.org":org,"_id.category":"chapter"}):
            weeks.append({'name':chapter['metadata']['display_name'],'children':chapter['definition']['children']})

        for week in weeks:
            #newchilds = []
            week['videos'] = []
            week['problems'] = []
            for child in week['children']:
                week['videos'].append(self.__getSequentialNameById(child,modules,True))
                week['problems'].append(self.__getSequentialNameById(child,modules,False))
            #del(week['children'])
            week['videos'] = filter(lambda x: x != None, week['videos'])
            week['problems'] = filter(lambda x: x != None, week['problems'])
            #week['children'] = list(itertools.chain.from_iterable(newchilds))

        for week in weeks:
            for video in week['videos']:
                verticals = self.__getChildren(video['id'],modules)
                content = [self.__getChildren(i,modules) for i in verticals]
                content = list(itertools.chain.from_iterable(content))
                video['children'] = filter(lambda x: 'video' in x,content)
            for problem in week['problems']:
                verticals = self.__getChildren(problem['id'],modules)
                content = [self.__getChildren(i,modules) for i in verticals]
                content = list(itertools.chain.from_iterable(content))
                problem['children'] = filter(lambda x: 'problem' in x,content)

        return weeks

    def checkEnrolment(self,user_id,course_id):
        cursor = self.__connection.cursor()
        cursor.execute("SELECT count( * ) FROM courseware_studentmodule WHERE student_id = {0} AND course_id = '{1}' AND  (module_type = 'video' or module_type = 'problem')".format(user_id,course_id))
        number_of_rows = cursor.fetchone()[0]
        return False
        """
        if number_of_rows > 0:
            return True
        else:
            return False
        """

    def get_password(self,name):
        cur = self.__connection.cursor()
        cur.execute("SELECT PASSWORD FROM  auth_user WHERE username =  '%s'" % name)
        answer = cur.fetchone()[0]
        return answer

    def isTeacher(self,name):
        cur = self.__connection.cursor()
        cur.execute("SELECT * FROM auth_user u LEFT JOIN student_courseaccessrole r ON u.id = r.user_id WHERE u.username =  '%s' AND r.role IS NOT NULL " % name)
        answer = cur.fetchone()
        if answer:
            return True
        else:
            return False

    def map_educaiton(self,id):
        if id == "p":
            return u'кандидатський чи докторський ступінь'
        elif id == "m":
            return u'магістр'
        elif id == "b":
            return u'бакалавр'
        elif id == "a":
            return u'незакінчена вища освіта'
        elif id == "hs":
            return u'середня освіта'
        elif id == "jhs":
            return u'професійно-технічна освіта'
        elif id == "el":
            return u'початкова освіта'
        elif id == "none":
            return u'немає'
        elif id == "other":
            return u'інше'
        else:
            return id

    def map_gender(self,id):
        if id == 'm':
            return u'Чоловік'
        elif id == 'f':
            return u'Жінка'
        elif id == 'o' or id == None or len(id) == 0:
            return u'Інше / Не вказано'
        else:
            return id

    def getUserData(self,username):
        cur = self.__connection.cursor()
        cur.execute("select * from auth_user where username = '%s'" % username)
        auth_user = cur.fetchone()
        if auth_user is not None:
            id = auth_user[0]
            email = auth_user[4]
            cur.execute("select * from auth_userprofile where user_id = '%d'" % id)
            auth_userprofile = cur.fetchone()
            name = auth_userprofile[2]
            gender = self.map_gender(auth_userprofile[7])
            year = auth_userprofile[9]
            education = self.map_educaiton(auth_userprofile[10])
            aim = auth_userprofile[11]
            return name,email,gender,year,education,aim
        else:
            localUser = User.objects.get(username=username)
            return username, localUser.email, u'Невідомо', u'Невідомо', u'Невідомо', u'Невідомо'

    def getAllCourseNames(self):
        credentials = Credential.GetMongoSettings()
        client = MongoClient(credentials.Address, credentials.Port)
        modules = client.edxapp.modulestore
        result = modules.find({"_id.category": "course"},{"_id":1,"metadata.display_name":1})
        return {'{0}/{1}/{2}'.format(i['_id']['org'],i['_id']['course'],i['_id']['name']) : i['metadata']['display_name'] for i in result}

    def getCourseName(self,course_id):
        credentials = Credential.GetMongoSettings()
        client = MongoClient(credentials.Address, credentials.Port)
        modules = client.edxapp.modulestore
        org, course, name = course_id.split('/')
        result = modules.find_one({"$and":[{"_id.category":"course"},{"_id.org":org},{"_id.course":course},{"_id.name":name}]})
        return result['metadata']['display_name']

    def getCoursesResult(self,username):
        sql = "select ce.course_id, gc.grade from auth_user au " + \
		                        "join student_courseenrollment ce " + \
			                        "on au.id = ce.user_id and au.username = '{0}' ".format(username) + \
		                        "left join certificates_generatedcertificate gc " + \
			                        "on ce.course_id = gc.course_id and ce.user_id = gc.user_id"
        courses = pd.read_sql(sql,con = self.__connection).fillna(0)
        courses.grade = courses.grade.apply(lambda x: int(float(str(x)) * 100))
        allCourses = self.getAllCourseNames()
        courses.course_id = courses.course_id.apply(lambda x: allCourses[x])
        return courses[['course_id','grade']].values

    def getUserStatuses(self, course_id):
        sql = "select 'Завершили курс', count(*) from certificates_generatedcertificate where course_id = '{0}' and status = 'downloadable' ".format(course_id) + \
              "union " + \
              "select 'Почали проходити курс', count(*) from student_courseenrollment ce where ce.course_id = '{0}' and not exists(select user_id from certificates_generatedcertificate c where course_id = '{0}' and status = 'downloadable' and ce.user_id = c.user_id) and exists(select student_id from courseware_studentmodule sm where sm.course_id = '{0}' and ce.user_id = sm.student_id) ".format(course_id) + \
              "union " + \
              "select 'Тільки зареєструвалися на курс', count(*) from student_courseenrollment ce where ce.course_id = '{0}' and not exists(select user_id from certificates_generatedcertificate c where course_id = '{0}' and status = 'downloadable' and ce.user_id = c.user_id) and not exists(select student_id from courseware_studentmodule sm where sm.course_id = '{0}' and ce.user_id = sm.student_id)".format(course_id)
        statuses = pd.read_sql(sql,con = self.__connection)
        return statuses.values.tolist()

    def countFirstCourse(self, course_id):
        sql = "select count(*) from student_courseenrollment ce where ce.course_id = '{0}' and not exists(select * from student_courseenrollment sce where sce.user_id = ce.user_id and sce.id != ce.id)".format(course_id)
        cur = self.__connection.cursor()
        cur.execute(sql)
        answer = cur.fetchone()
        cur.close()
        return answer[0]

    def getCourseInfo(self, course_id):
        credentials = Credential.GetMongoSettings()
        client = MongoClient(credentials.Address, credentials.Port)
        modules = client.edxapp.modulestore
        org, course, name = course_id.split('/')
        result = modules.find_one({"_id.category": "course", "_id.org": org, "_id.course": course, "_id.name": name})
        return result

    def getStatusForActiveOnCourseUsers(self, course_id):
        sql = "select au.id as user_id, au.email, IF(c.status = 'downloadable','passed', 'in progress') as status from auth_user au join student_courseenrollment ce on au.id = ce.user_id left join certificates_generatedcertificate c on c.user_id = au.id and ce.course_id = c.course_id where ce.course_id = '{0}'".format(course_id)
        return pd.read_sql(sql, con=self.__connection, index_col='user_id')

    def getStatusForInactiveOnCourseUsers(self, course_id):
        sql = "select ce.user_id, au.email, 'just started' as status, 0 as prediction from student_courseenrollment ce join auth_user au on ce.user_id = au.id where  course_id = '{0}' and ce.user_id not in (select student_id from courseware_studentmodule where module_type = 'problem' and course_id = '{0}')".format(course_id)
        return pd.read_sql(sql, con=self.__connection, index_col='user_id')

    def getPendingUsers(self):
        users = User.objects.filter(last_name='Pending')
        return map(lambda x: {'username':x.username, 'email':x.email},users)