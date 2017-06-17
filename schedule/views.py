# -*- coding: utf-8 -*-

from django.template import *
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from time import time
from ContentManager import ContentManager
from article.views import getUserData
import pandas as pd
import csv
import StringIO

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
    request.session['predict_csv'] = args['content']['predict_csv']
    args['banner'] = {'tilte':u'Прогноз','links':[['/',u'Головна'],['/analysis/predict/',u'Прогноз']]}
    return render_to_response(view_name,args,context_instance=RequestContext(request))

@login_required(login_url='/auth/login/')
def get_csv(request):
    data = request.session.get('predict_csv', None)
    if data is None:
        data = ['None','None','None']
    csvfile = newcsv(data, ['email', 'state', 'prediction'])

    response = HttpResponse(csvfile.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=prediction.csv'
    return response


def newcsv(data, csvheader):
    """
    Create a new csv file that represents generated data.
    """
    csvrow = []
    new_csvfile = StringIO.StringIO()
    wr = csv.writer(new_csvfile)
    wr.writerow(csvheader)
    wr = csv.writer(new_csvfile,delimiter=',',)

    for item in data:
        wr.writerow(item)

    return new_csvfile

