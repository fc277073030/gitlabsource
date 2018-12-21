#!/usr/bin/env python

import os
import requests
import json

from bottle import route, run, response

from cloudevents.sdk import converters
from cloudevents.sdk import marshaller
from cloudevents.sdk.converters import structured
from cloudevents.sdk.event import v01

channel = os.environ['CHANNEL']
namespace = os.environ['NAMESPACE']

def dispatch(message):
    url = 'http://%s-channel.%s.svc.cluster.local' % (channel, namespace)
    print(url)

    event = (
        v01.Event().
        WithContentType("application/json").
        WithData(message).
        WithEventID("my-id").
        WithSource("from-galaxy-far-far-away").
        WithEventTime("tomorrow").
        WithEventType("cloudevent.greet.you")
    )
    m = marshaller.NewHTTPMarshaller(
        [
            structured.NewJSONHTTPCloudEventConverter(type(event))
        ]
    )

    headers, body = m.ToRequest(event, converters.TypeStructured, lambda x: x)

    requests.post(url, data=body, headers=headers)

@route('/')
def index():
    dispatch(request.json)
    return "OK"

run(host="0.0.0.0", port=8080)


