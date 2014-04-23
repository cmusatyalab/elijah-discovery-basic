#!/usr/bin/env python 
from urlparse import urlparse
import httplib
import json

def get(url, json_string):
    print("Posting to %s" % (url))
    end_point = urlparse("%s" % (url))

    params = json.dumps(json_string)
    headers = {"Content-type": "application/json"}

    conn = httplib.HTTPConnection(end_point.hostname, end_point.port)
    conn.request("GET", "%s" % end_point[2], params, headers)
    data = conn.getresponse().read()
    dd = json.loads(data)
    conn.close()
    return dd


if __name__ == "__main__":
    json_str = {
            'application': {
                'id': '123123',
                'name': 'moped',
                'files': [
                    'moped/kitchen/a',
                    'moped/kitchen/b',
                    ],
                }
            }
    ret_dict = get("http://127.0.0.1:8022/api/v1/resource/", json_str)
    import pprint
    pprint.pprint(ret_dict)


