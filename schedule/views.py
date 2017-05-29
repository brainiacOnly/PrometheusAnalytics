# -*- coding: utf-8 -*-

from django.template import *
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
import  time
from ContentManager import ContentManager
from article.views import getUserData

@login_required(login_url='/auth/login/')
def main(request):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    args['course_names'] = ['KPI/Algorithms101/2015_Spring','KPI/Programming101/2015_T1','KNU/101/2014_T2','NAUKMA/101/2014_T2']
    if request.session.get('course',None) is None:
        request.session['course'] = args['course_names'][0]
    args['course'] = request.session['course']
    args['path'] = request.path
    content = ContentManager(request.session['course'])
    id = 8
    #id = 20426
    id = 355
    view_name, args['content'] = content.schedule(id)
    args['banner'] = {'tilte':u'Ваш розклад навчання','links':[['/',u'Головна'],['/schedule/',u'План навчання']]}

    return render_to_response(view_name,args,context_instance=RequestContext(request))
