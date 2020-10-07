import traceback

from django.utils import timezone

from silk.collector import DataCollector
from silk.sql import _should_wrap


def wrapped_request(self, method, url,
                    params=None, data=None, headers=None, cookies=None, files=None,
                    auth=None, timeout=None, allow_redirects=True, proxies=None,
                    hooks=None, stream=None, verify=None, cert=None, json=None):
    tb = ''.join(reversed(traceback.format_stack()))
    sql_query = {'method': method, 'url': url, 'params': params, 'json': json}
    if _should_wrap(sql_query):
        query_dict = {
            'query': str(sql_query),
            'start_time': timezone.now(),
            'traceback': tb
        }
        try:
            return self._request(method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                                 proxies, hooks, stream, verify, cert, json)
        finally:
            query_dict['end_time'] = timezone.now()
            request = DataCollector().request
            if request:
                query_dict['request'] = request
            # if self.query.model.__module__ != 'silk.models':
            DataCollector().register_query(query_dict)
            # else:
            #     DataCollector().register_silk_query(query_dict)
    return self._request(method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                         proxies, hooks, stream, verify, cert, json)
