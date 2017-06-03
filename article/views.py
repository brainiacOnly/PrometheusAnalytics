# -*- coding: utf-8 -*-
from sets import Set
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, Http404
from django.template.loader import get_template
from django.template import *
from django.shortcuts import render_to_response, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.context_processors import csrf
from django.contrib import auth
from time import time
from article.models import Article, Comments
from forms import CommentForm
from ContentManager import ContentManager
import pandas as pd

# Create your views here.
def basic_one(request):
    view = 'basic_one'
    html = '<html><body>This is %s view</body></html>' % view
    return HttpResponse(html)

def template_two(request):
    view = 'template_two'
    t = get_template('myview.html')
    html = t.render(Context({'name':view}))
    return HttpResponse(html)

def template_three_simple(request):
    view = 'template_three'
    return render_to_response('myview.html',{'name':view})

def article(request, article_id):
    comment_form = CommentForm
    args = {}
    args.update(csrf(request))
    args['article'] = Article.objects.get(id=article_id)
    args['comments'] = Comments.objects.filter(comments_article_id=article_id)
    args['form'] = comment_form
    args['username'] = auth.get_user(request).username
    return render_to_response('article.html',args)

def addlike(request, article_id):
    try:
        if article_id in request.COOKIES:
            article = Article.objects.get(id=article_id)
            article.article_likes -= 1
            article.save()
            responce = redirect('/')
            responce.delete_cookie(article_id)
            return responce
        else:
            article = Article.objects.get(id=article_id)
            article.article_likes += 1
            article.save()
            responce = redirect('/')
            responce.set_cookie(article_id,'test')
            return responce
    except ObjectDoesNotExist:
        raise Http404
    return redirect('/')

def addcomment(request,article_id):
    if request.POST and ('pause' not in request.session):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.comments_article = Article.objects.get(id = article_id)
            form.save()
            request.session['pause'] = True
    return redirect('/articles/get/%s/' % article_id)

def face(request):
    args = {}
    args.update(getUserData(request))

    return render_to_response('face.html',args)

def about(request):
    args = {}
    args.update(getUserData(request))
    return render_to_response('about.html',args)

def getUserData(request):
    args = {}
    user = auth.get_user(request)
    args['username'] = user.username
    args['is_teacher'] = user.is_active
    args['is_staff'] = user.is_staff
    return args

@login_required(login_url='/auth/login/')
def profile(request):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    content = ContentManager()
    view_name, args['content'] = content.profile(args['username'])
    args['banner'] = {'tilte':u'Ваш профіль','links':[['/',u'Головна'],['#',u'Профіль']]}
    return render_to_response(view_name,args,context_instance=RequestContext(request))

@login_required(login_url='/auth/login/')
def manage_registration(request):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    content = ContentManager()
    view_name, args['content'] = content.manage_registration()
    print args['content']
    args['banner'] = {'tilte': u'Управління запитами на реєстрацію', 'links': [['/', u'Головна'], ['#', u'Реєстрації']]}
    return render_to_response(view_name, args, context_instance=RequestContext(request))

@login_required(login_url='/auth/login/')
def course(request, id = 'main'):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    courses = pd.read_csv('static\\data\\courses.csv', encoding='utf8')
    #args['course_names'] = ['KPI/Algorithms101/2015_Spring','KPI/Programming101/2015_T1','KNU/101/2014_T2','NAUKMA/101/2014_T2']
    args['course_names'] = courses.values.tolist()
    if request.session.get('course',None) is None:
        request.session['course'] = args['course_names'][0]
    args['course'] = request.session['course']
    args['path'] = request.path
    content = ContentManager(request.session['course'][0])
    view_name, args['content'] = content.course(id)
    args['banner'] = {'tilte':u'Виберіть курс та тип візуалізації','links':[['/',u'Головна'],['/course/main/',u'Візуалізація'],['/course/main/',u'Курс'],['#',args['content']['page']]]}
    return render_to_response(view_name,args,context_instance=RequestContext(request))

def platform(request, id = 'age'):
    args = {}
    args.update(csrf(request))
    args.update(getUserData(request))
    content = ContentManager()
    view_name, args['content'] = content.prometheus(id)
    args['banner'] = {'tilte':u'Виберіть тип візуалізації','links':[['/',u'Головна'],['/course/platform/',u'Візуалізація'],['/course/platform/','Prometheus'],['#',args['content']['page']]]}

    return render_to_response(view_name,args,context_instance=RequestContext(request))

def set_course(request):
    args = {}
    args.update(csrf(request))
    request.session['course'] = request.POST['course_name']
    return redirect(request.POST['path'])