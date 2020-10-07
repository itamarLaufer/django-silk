import json as json_module
import traceback

from django.utils import timezone

from silk.collector import DataCollector


def wrapped_request(self, method, url,
                    params=None, data=None, headers=None, cookies=None, files=None,
                    auth=None, timeout=None, allow_redirects=True, proxies=None,
                    hooks=None, stream=None, verify=None, cert=None, json=None):
    tb = ''.join(reversed(traceback.format_stack()))
    api_call_dict = {'method': method, 'url': url, 'query_params': json_module.dumps({'param': params, 'json': json}),
                     'traceback': tb, 'start_time': timezone.now()}
    sql_query = {'method': method, 'url': url, 'query_params': json_module.dumps({'param': params, 'json': json})}
    query_dict = {
        'query': str(sql_query),
        'start_time': timezone.now(),
        'traceback': tb
    }
    try:
        return self._request(method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                             proxies, hooks, stream, verify, cert, json)
    finally:
        api_call_dict['end_time'] = timezone.now()
        query_dict['end_time'] = timezone.now()
        request = DataCollector().request
        if request:
            api_call_dict['request'] = request
            query_dict['request'] = request
        DataCollector().register_api_call(api_call_dict)
        DataCollector().register_query(query_dict)
        return self._request(method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                             proxies, hooks, stream, verify, cert, json)
