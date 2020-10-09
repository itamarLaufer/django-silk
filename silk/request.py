import json as json_module
import traceback

from django.utils import timezone

from silk.collector import DataCollector


def wrapped_request(self, method, url,
                    params=None, data=None, headers=None, cookies=None, files=None,
                    auth=None, timeout=None, allow_redirects=True, proxies=None,
                    hooks=None, stream=None, verify=None, cert=None, json=None):
    tb = ''.join(reversed(traceback.format_stack()))
    api_call_dict = {'method': method.upper(), 'url': url, 'traceback': tb, 'start_time': timezone.now(),
                     'json_data': None if json is None else json_module.dumps(json)}

    response = None
    try:
        response = self._request(method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                                 proxies, hooks, stream, verify, cert, json)
        return response
    finally:
        api_call_dict['end_time'] = timezone.now()
        request = DataCollector().request
        if request:
            api_call_dict['request'] = request
        if response is not None:
            api_call_dict['status_code'] = response.status_code
        DataCollector().register_api_call(api_call_dict)
