from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader
from c2g.models import Course, Video
from django.template import RequestContext

from c2g.models import Course, Video, VideoActivity
from courses.common_page_data import get_common_page_data
import datetime
from courses.videos.forms import VideoUploadForm
import gdata.youtube
import gdata.youtube.service

def list(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404

    section_structures = []
    if request.user.is_authenticated():
        sections = common_page_data['course'].contentsection_set.all().order_by('index')
        videos = Video.objects.filter(course=common_page_data['course']).order_by('section', 'index')
        video_recs = request.user.videoactivity_set.filter(course=common_page_data['course'])
        
        index = 0
        for section in sections:
            section_dict = {'section':section, 'video_video_recs':[]}
            
            for video in videos:
                if video.section_id == section.id and (common_page_data['course_mode'] == 'staging' or (video.live_datetime and common_page_data['current_datetime'] > video.live_datetime)):
                    current_video_rec = None
                    for video_rec in video_recs:
                        if video_rec.video_id == video.id:
                            current_video_rec = video_rec
                            break
                    live_status = ''
                    if common_page_data['course_mode'] == 'staging':
                        prod_video = video.image
                        if not prod_video.live_datetime:
                            live_status = "<span style='color:red;'>Not live</span>"
                        else:
                            if prod_video.live_datetime > datetime.datetime.now():
                                year = prod_video.live_datetime.year
                                month = prod_video.live_datetime.month
                                day = prod_video.live_datetime.day
                                hour = prod_video.live_datetime.hour
                                minute = prod_video.live_datetime.minute
                                live_status = "<span style='color:red;'>Goes live on %02d-%02d-%04d at %02d:%02d</span>" % (month,day,year,hour,minute)
                            else:
                                live_status = "<span style='color:green;'>Live</span>"
                                
                    section_dict['video_video_recs'].append({'video':video, 'video_rec':current_video_rec, 'live_status':live_status})
            
            if common_page_data['course_mode'] == 'staging' or len(section_dict['video_video_recs']) > 0:
                section_structures.append(section_dict)
                index += 1
    
    if common_page_data['course_mode'] == 'staging':
        template = 'videos/staging/list.html'
    else:
        template = 'videos/production/list.html'
    return render_to_response(template, {'common_page_data':common_page_data, 'section_structures':section_structures}, context_instance=RequestContext(request))
    
def view(request, course_prefix, course_suffix, slug):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404
    
    video = None
    video_rec = None
    if request.user.is_authenticated():
        video = Video.objects.get(course=common_page_data['production_course'], slug=slug)
        #video_rec = request.user.videoactivity_set.filter(video=video)
        video_rec = request.user.videoactivity_set.get(video=video)

    return render_to_response('videos/view.html', {'common_page_data': common_page_data, 'video': video, 'video_rec':video_rec}, context_instance=RequestContext(request))
    
def edit(request, course_prefix, course_suffix, video_id):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404
        
    return render_to_response('videos/edit.html', 
            {'request': request,
             'course_prefix': course_prefix,
             'course_suffix': course_suffix,
             'course': course,
             'video_id': video_id,
             },
            context_instance=RequestContext(request))

def GetAuthSubUrl(request):
    next = "http://localhost:8000" + request.path
    scope = 'http://gdata.youtube.com'
    secure = False
    session = True

    yt_service = gdata.youtube.service.YouTubeService()
    return yt_service.GenerateAuthSubURL(next, scope, secure, session)

def upload(request, course_prefix, course_suffix):
    try:
        common_page_data = get_common_page_data(request, course_prefix, course_suffix)
    except:
        raise Http404

    data = {'common_page_data': common_page_data}

    #if 'id' in request.GET:
        #process Video model instance with this youtube id
        #and other stuff

    if 'token' in request.GET:
        token = request.GET['token']
        data['token'] = token

        yt_service = gdata.youtube.service.YouTubeService()
        #yt_service.developer_key = 'AI39si5GlWcy9S4eVFtajbVZk-DjFEhlM4Zt7CYzJG3f2bwIpsBSaGd8SCWts6V5lbqBHJYXAn73-8emsZg5zWt4EUlJJ4rpQA'
        #yt_service.SetAuthSubToken(token)
        #yt_service.UpgradeToSessionToken()

        yt_logged_in = True
        form = VideoUploadForm(sections = common_page_data['course'].contentsection_set.all().order_by('index'))
        data['form'] = form
    else:
        # user is not logged into google account for youtube
        yt_logged_in = False
        authSubUrl = GetAuthSubUrl(request)
        data['authSubUrl'] = authSubUrl

    data['yt_logged_in'] = yt_logged_in
    return render_to_response('videos/upload.html',
                              data,
                              context_instance=RequestContext(request))
