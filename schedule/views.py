# -*- coding: utf-8 -*-

from django.template import *
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from time import time
from ContentManager import ContentManager
from article.views import getUserData
import pandas as pd

@login_required(login_url='/auth/login/')
def main(request):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    courses = pd.read_csv('static\\data\\courses.csv', encoding='utf8')
    args['course_names'] = courses.values.tolist()
    if request.session.get('course',None) is None:
        request.session['course'] = args['course_names'][0][0]
    args['course'] = request.session['course']
    args['path'] = request.path
    content = ContentManager(request.session['course'])
    id = 8
    #id = 20426
    id = 355
    start_time = time()
    view_name, args['content'] = content.schedule(id)
    print '#PROFILER schedule took {0}'.format(time()-start_time)
    args['banner'] = {'tilte':u'Ваш розклад навчання','links':[['/',u'Головна'],['/analysis/schedule/',u'План навчання']]}

    return render_to_response(view_name,args,context_instance=RequestContext(request))

@login_required(login_url='/auth/login/')
def predict(request):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    courses = pd.read_csv('static\\data\\courses.csv', encoding='utf8')
    args['course_names'] = courses.values.tolist()
    if request.session.get('course',None) is None:
        request.session['course'] = args['course_names'][0][0]
    args['course'] = request.session['course']
    args['path'] = request.path
    content = ContentManager(request.session['course'])
    view_name, args['content'] = content.predict()
    args['banner'] = {'tilte':u'Прогноз','links':[['/',u'Головна'],['/analysis/predict/',u'Прогноз']]}
    return render_to_response(view_name,args,context_instance=RequestContext(request))
