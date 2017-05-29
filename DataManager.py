# -*- coding: utf-8 -*-
import os
from django.conf import settings
import time
import pandas as pd
import datetime
import numpy as np
import MySQLdb
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import itertools
from Credential import Credential

class DataManager():
    def __enter__(self):
        settings = Credential.GetSQLSettings()
        self.__connection = MySQLdb.connect(host=settings.Address, port=settings.Port, user=settings.Username, passwd=settings.Password,
                                            db=settings.DatabaseName, charset=settings.Encoding)
        return self

    def __exit__(self, type, value, traceback):
        if self.__connection:
            self.__connection.close()

    def studentmodule(self,course_id, module_type):
        result = pd.read_sql("SELECT module_id, student_id as user_id, grade, max_grade, course_id, created, modified from courseware_studentmodule where course_id = '{0}' and module_type = '{1}'".format(course_id, module_type),con=self.__connection)
        print 'studentmodule was executed. The result contains %d rows' % len(result)
        return result

    def users(self):
        sql = "SELECT user_id, gender, year_of_birth, level_of_education from auth_userprofile"
        print "users execution [%s]" % sql
        result = pd.read_sql(sql, con=self.__connection)
        print 'users(auth_userprofile table) was executed. The result contains %d rows' % len(result)
        return result

    def certificates(self, course_id = "", status = ""):
        whereClauses = []
        whereStatement = ""
        if course_id != "":
            whereClauses.append("course_id = '%s'" % course_id)
        if status != "":
            whereClauses.append("status = '%s'" % status)
        if len(whereClauses) > 0:
            whereStatement = " WHERE " + " AND ".join(whereClauses)
        sql = "SELECT user_id, grade, course_id, status FROM certificates_generatedcertificate" + whereStatement
        print 'certificates sql: [%s]' % sql
        result = pd.read_sql(sql, con=self.__connection)
        print 'certificates(certificates_generatedcertificate table) was executed. The result contains %d rows' % len(result)
        return result

    def main(self,course_name):
        print ' in main db'
        cur = self.__connection.cursor()
        cur.execute("select count(*) from certificates_generatedcertificate where status = 'downloadable' and course_id = '%s'" % course_name)
        downloadable = cur.fetchone()[0]
        cur.execute("select count(*) from certificates_generatedcertificate where status != 'downloadable' and course_id = '%s'" % course_name)
        notPassed = cur.fetchone()[0]

        print '{0} - downloadable, {1} - notPassed'.format(downloadable, notPassed)
        #certificates = self.get_certificates()
        #certificates = certificates[certificates.course_id == course_name]
        #downloadable = len(certificates[certificates.status == 'downloadable'])
        #notPassed = len(certificates[certificates.status != 'downloadable'])
        return [[u'Пройшли',downloadable],[u'Не пройшли',notPassed]]

    def age(self, course_name):
        """
        certificates = self.get_certificates()
        users = self.get_users()
        cert = certificates[['user_id','grade','course_id','status','name','created_date']]
        cert = cert[cert.course_id == course_name]
        users = users[['user_id','name','gender','year_of_birth','level_of_education']]
        registered = pd.merge(cert,users,how='inner',on='user_id')
        registered['create_year'] = registered.created_date.apply(lambda x: time.strptime(x,'%Y-%m-%d %H:%M:%S').tm_year)
        registered = registered.rename(columns = {'year_of_birth':'Age'})
        registered.Age = registered.create_year - registered.Age
        certified = registered[registered.status == 'downloadable']

        notsetAge = registered[registered.Age.isnull()]
        withAge = registered[registered.Age.notnull()]
        certNoAge = certified[certified.Age.isnull()]
        certAge = certified[certified.Age.notnul    l()]

        registeredGroups = pd.Series([len(notsetAge)],index=['without age'])
        certifiedGroups = pd.Series([len(certNoAge)],index=['without age'])
        registeredGroups.set_value('below 20',len(withAge[withAge.Age < 20]))
        certifiedGroups.set_value('below 20',len(certAge[certAge.Age < 20]))

        for i in range(0,6):
            begin, end = 20+i*5, 20+(i+1)*5
            registeredGroups.set_value(str(begin) + '-' + str(end-1),len(withAge.Age[withAge.Age >= begin ][withAge.Age < end]))
            certifiedGroups.set_value(str(begin) + '-' + str(end-1),len(certAge.Age[certAge.Age >= begin ][certAge.Age < end]))


        registeredGroups.set_value('50 and higer',len(withAge[withAge.Age >= 50]))
        certifiedGroups.set_value('50 and higer',len(certAge[certAge.Age >= 50]))
        plot_data = pd.concat([registeredGroups,certifiedGroups],axis=1,keys=['registered','passed'])
        plot_data['name'] = plot_data.index
        plot_data = plot_data[['name','registered','passed']]
        """
        cur = self.__connection.cursor()
        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE year_of_birth is NULL and c.course_id = '%s'" % course_name)
        registeredGroups = pd.Series([cur.fetchone()[0]],index=['without age'])
        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE year_of_birth is NULL AND c.status =  'downloadable' and c.course_id = '%s'" % course_name)
        certifiedGroups = pd.Series([cur.fetchone()[0]],index=['without age'])

        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth < 20 and c.course_id = '%s'" % course_name)
        registeredGroups.set_value(u'До 20',cur.fetchone()[0])
        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth < 20 AND c.status =  'downloadable' and c.course_id = '%s'" % course_name)
        certifiedGroups.set_value(u'До 20',cur.fetchone()[0])

        for i in range(0,6):
            begin, end = 20+i*5, 20+(i+1)*5
            cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth >= {0} and YEAR( CURDATE( ) ) - year_of_birth < {1} and c.course_id = '{2}'".format(begin,end,course_name))
            registeredGroups.set_value(str(begin) + '-' + str(end-1),cur.fetchone()[0])
            cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth >= {0} and YEAR( CURDATE( ) ) - year_of_birth < {1} and c.course_id = '{2}' AND c.status =  'downloadable'".format(begin,end,course_name))
            certifiedGroups.set_value(str(begin) + '-' + str(end-1),cur.fetchone()[0])

        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth >= 50 and c.course_id = '%s'" % course_name)
        registeredGroups.set_value(u'50 і більше',cur.fetchone()[0])
        cur.execute("SELECT COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id WHERE YEAR( CURDATE( ) ) - year_of_birth >= 50 AND c.status =  'downloadable' and c.course_id = '%s'" % course_name)
        certifiedGroups.set_value(u'50 і більше',cur.fetchone()[0])

        plot_data = pd.concat([pd.DataFrame(registeredGroups.index,index=registeredGroups.index),registeredGroups,certifiedGroups],axis=1,keys=['name','registered','passed'])
        percent_plot_data = pd.concat([pd.Series(registeredGroups.index,index=registeredGroups.index), (certifiedGroups / registeredGroups * 100)],axis=1,keys=['index','percent'])
        percent_plot_data.percent = percent_plot_data.percent.apply(lambda x: int(round(x)))
        return plot_data.values,percent_plot_data.values

    def education(self, course_name):
        """
        certificates = self.get_certificates()
        users = self.get_users()
        cert = certificates[['user_id','grade','course_id','status','name','created_date']]
        cert = cert[cert.course_id == course_name]
        users = users[['user_id','name','gender','year_of_birth','level_of_education']]
        registered = pd.merge(cert,users,how='inner',on='user_id').fillna('missed')
        certified = registered[registered.status == 'downloadable']

        registeredGroups =registered.groupby('level_of_education').count().ix[:,0]
        certifiedGroups = certified.groupby('level_of_education').count().ix[:,0].apply(lambda x: int(x))

        plot_data = pd.concat([registeredGroups,certifiedGroups],axis=1,keys=['registered','passed']).fillna(0)
        plot_data['name'] = plot_data.index
        plot_data = plot_data[['name','registered','passed']]
        plot_data.passed = plot_data.passed.apply(lambda x: int(x))

        percent_plot_data = pd.concat([pd.Series(plot_data.index,index=plot_data.index), (plot_data.passed / plot_data.registered * 100).apply(lambda x: int(round(x)))],axis=1,keys=['index','percent'])
        """
        registeredCroups = pd.read_sql("SELECT level_of_education, COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' group by u.level_of_education" % course_name,con=self.__connection)
        certifiedCroups = pd.read_sql("SELECT level_of_education, COUNT( * ) FROM  auth_userprofile u JOIN certificates_generatedcertificate c ON u.user_id = c.user_id and c.course_id = '%s' and c.status = 'downloadable' group by u.level_of_education" % course_name,con=self.__connection)

        plot_data = registeredCroups
        plot_data.columns = ['name','registered']
        plot_data['passed'] = certifiedCroups['COUNT( * )']
        plot_data = plot_data.fillna(0)
        plot_data.passed = plot_data.passed.apply(lambda x: int(round(x)))
        plot_data.name = plot_data.name.apply(self.map_educaiton)
        percent_plot_data = pd.concat([plot_data.name, (plot_data.passed / plot_data.registered * 100)],axis=1,keys=['name','percent']).fillna(0)
        percent_plot_data.percent = percent_plot_data.percent.apply(lambda x: int(round(x)))
        percent_plot_data.name = percent_plot_data.name.apply(self.map_educaiton)

        return plot_data.values, percent_plot_data.values

    def gender(self,course_name):
        """
        certificates = self.get_certificates()
        users = self.get_users()
        cert = certificates[['user_id','grade','course_id','status','name','created_date']]
        cert = cert[cert.course_id == course_name]
        users = users[['user_id','name','gender','year_of_birth','level_of_education']]
        registered = pd.merge(cert,users,how='inner',on='user_id').dropna(subset=['gender'])
        certified = registered[registered.status == 'downloadable']

        registeredGroups =registered.groupby('gender').count().ix[:,0]
        certifiedGroups = certified.groupby('gender').count().ix[:,0]

        plot_data = pd.concat([registeredGroups,certifiedGroups],axis=1,keys=['registered','passed'])
        plot_data['name'] = plot_data.index
        plot_data = plot_data[plot_data.name != 'o']
        plot_data.passed = plot_data.passed.apply(lambda x: int(x))

        plot_data = plot_data[['name','registered','passed']]
        """
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

        #sm = {'KPI/Algorithms101/2015_Spring':self.get_algorithms(),'KPI/Programming101/2015_T1':self.get_programming(),'KNU/101/2014_T2':self.get_history(),'NAUKMA/101/2014_T2':self.get_finman()}[course_name]
        problems = self.studentmodule(course_name, 'problem')
        a = problems.groupby('module_id').count().ix[:,0]
        b = problems.groupby('module_id').apply(lambda x: x.created.min())
        finishers = pd.concat([a,b],axis=1,keys=['num','date']).sort('date').num
        plot_data = pd.concat([pd.DataFrame(finishers.index,index=finishers.index),finishers],axis=1,keys=['name','passed'])

        return plot_data.values.tolist()

    def age_all(self):
        """
        users = self.get_users()
        registered = users[['user_id','name','gender','year_of_birth','level_of_education']]
        registered = registered.rename(columns = {'year_of_birth':'Age'})
        now = datetime.datetime.now().year
        registered.Age = registered.Age.apply(lambda x: now - x)

        notsetAge = registered[registered.Age.isnull()]
        withAge = registered[registered.Age.notnull()]

        registeredGroups = pd.Series([len(notsetAge)],index=['without age'])
        registeredGroups.set_value('below 20',len(withAge[withAge.Age < 20]))
        """
        cur = self.__connection.cursor()
        cur.execute("select count(*) from auth_userprofile where year_of_birth is NULL")
        registeredGroups = pd.Series([cur.fetchone()[0]],index=['without age'])

        cur.execute("select count(*) from auth_userprofile WHERE YEAR( CURDATE( ) ) - year_of_birth < 20")
        registeredGroups.set_value(u'До 20',cur.fetchone()[0])

        for i in range(0,6):
            begin, end = 20+i*5, 20+(i+1)*5
            cur.execute("select count(*) from auth_userprofile WHERE YEAR( CURDATE( ) ) - year_of_birth >= {0} and YEAR( CURDATE( ) ) - year_of_birth < {1}".format(begin,end))
            registeredGroups.set_value(str(begin) + '-' + str(end-1),cur.fetchone()[0])

        cur.execute("select count(*) from auth_userprofile WHERE YEAR( CURDATE( ) ) - year_of_birth >= 50")
        registeredGroups.set_value(u'50 і більше',cur.fetchone()[0])

        plot_data = pd.concat([pd.DataFrame(registeredGroups.index,index=registeredGroups.index),registeredGroups],axis=1,keys=['name','passed'])

        return plot_data.values.tolist()

    def education_all(self):
        """
        users = self.get_users()
        registered = users[['user_id','name','gender','year_of_birth','level_of_education']]

        registeredGroups =registered.groupby('level_of_education').count().ix[:,0]
        plot_data = pd.concat([pd.DataFrame(registeredGroups.index,index=registeredGroups.index),registeredGroups],axis=1,keys=['name','values']).fillna(0)
        """
        plot_data = pd.read_sql("select level_of_education, count(*) from auth_userprofile group by level_of_education",con=self.__connection)
        plot_data.level_of_education = plot_data.level_of_education.apply(self.map_educaiton)
        return plot_data.values.tolist()

    def gender_all(self):
        """
        users = self.get_users()
        registered = users[['user_id','name','gender','year_of_birth','level_of_education']]

        registeredGroups =registered.groupby('gender').count().ix[:,0]

        plot_data = pd.concat([pd.DataFrame(registeredGroups.index,index=registeredGroups.index),registeredGroups],axis=1).fillna(0)
        plot_data.columns = ['name','value']
        plot_data = plot_data[plot_data.name != 'o']
        """
        plot_data = pd.read_sql("select gender, count(*) from auth_userprofile group by gender",con=self.__connection)
        plot_data.gender = plot_data.gender.apply(self.map_gender)

        return plot_data.values.tolist()

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
            newchilds = []
            week['videos'] = []
            week['problems'] = []
            for child in week['children']:
                week['videos'].append(self.__getSequentialNameById(child,modules,True))
                week['problems'].append(self.__getSequentialNameById(child,modules,False))
            del(week['children'])
            week['videos'] = filter(lambda x: x != None, week['videos'])
            week['problems'] = filter(lambda x: x != None, week['problems'])
            week['children'] = list(itertools.chain.from_iterable(newchilds))

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

        print 'getCourseStructure was executed. The result contains %d weeks' % len(weeks)
        return weeks

    def checkEnrolment(self,user_id,course_id):
        cursor = self.__connection.cursor()
        cursor.execute("SELECT count( * ) FROM courseware_studentmodule WHERE student_id = {0} AND course_id = '{1}' AND  (module_type = 'video' or module_type = 'problem')".format(user_id,course_id))
        number_of_rows = cursor.fetchone()[0]

        if number_of_rows > 0:
            return True
        else:
            return False

    def get_password(self,name):
        cur = self.__connection.cursor()
        print 'got a cursor'
        cur.execute("SELECT PASSWORD FROM  auth_user WHERE username =  '%s'" % name)
        print 'cursor executed'
        print cur
        answer = cur.fetchone()[0]
        print 'got the answer'
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
        """
        {"p":u'кандидатський чи докторський ступінь',
         "m":u'магістр',
         "b":u'бакалавр',
         "a":u'незакінчена вища освіта',
         "hs":u'середня освіта',
         "jhs":u'професійно-технічна освіта',
         "el":u'початкова освіта',
         "none":u'немає',
         "other":u'інше'}[id]
        """

    def map_gender(self,id):
        if id == 'm':
            return u'Чоловік'
        elif id == 'f':
            return u'Жінка'
        elif id == 'o':
            return u'Інше'
        else:
            return id

    def getUserData(self,username):
        cur = self.__connection.cursor()
        cur.execute("select * from auth_user where username = '%s'" % username)
        auth_user = cur.fetchone()
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