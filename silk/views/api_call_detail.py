import re
from django.core.exceptions import PermissionDenied

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import View

from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request, Profile, APICall
from silk.views.code import _code


class APICallDetailView(View):
    def _urlify(self, str):
        files = []
        r = re.compile('"(?P<src>.*\.py)", line (?P<num>[0-9]+).*')
        m = r.search(str)
        n = 1
        while m:
            group = m.groupdict()
            src = group['src']
            files.append(src)
            num = group['num']
            start = m.start('src')
            end = m.end('src')
            rep = '<a name={name} href="?pos={pos}&file_path={src}&line_num={num}#{name}">{src}</a>'.format(pos=n,
                                                                                                            src=src,
                                                                                                            num=num,
                                                                                                            name='c%d' % n)
            str = str[:start] + rep + str[end:]
            m = r.search(str)
            n += 1
        return str, files

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, *_, **kwargs):
        api_call_id = kwargs.get('api_call_id', None)
        request_id = kwargs.get('request_id', None)
        profile_id = kwargs.get('profile_id', None)
        api_call = APICall.objects.get(pk=api_call_id)
        pos = int(request.GET.get('pos', 0))
        file_path = request.GET.get('file_path', '')
        line_num = int(request.GET.get('line_num', 0))
        tb = api_call.traceback_ln_only
        str, files = self._urlify(tb)
        if file_path and file_path not in files:
            raise PermissionDenied
        tb = [mark_safe(x) for x in str.split('\n')]
        context = {
            'api_call': api_call,
            'traceback': tb,
            'pos': pos,
            'line_num': line_num,
            'file_path': file_path
        }
        if request_id:
            context['silk_request'] = Request.objects.get(pk=request_id)
        if profile_id:
            context['profile'] = Profile.objects.get(pk=int(profile_id))
        if pos and file_path and line_num:
            actual_line, code = _code(file_path, line_num)
            context['code'] = code
            context['actual_line'] = actual_line
        return render(request, 'silk/api_call_detail.html', context)
