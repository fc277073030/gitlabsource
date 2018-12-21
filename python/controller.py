#!/usr/bin/env python
"""A controller """

import json
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import logging
import os
import time
import http.client
import string
import base64
import random
import gitlab
import gitlab.exceptions as gitlabexceptions

GROUP = "sources.eventing.triggermesh.io"
VERSION = "v1alpha1"
PLURAL = "gitlabsources"

apps_beta1 = client.AppsV1beta1Api()
crds = client.CustomObjectsApi()
v1=client.CoreV1Api()

class GitLabSource(object):
    def __init__(self, obj, namespace='default'):
        self._obj = obj
        self._apiversion = obj["apiVersion"]
        self._kind = obj["kind"]
        self._metadata = obj["metadata"]
        self._namespace = namespace
        self._spec = obj["spec"]
        self._eventtype = self._spec["eventTypes"]
        self._ownerandrepo = self._spec["ownerAndRepository"]
        self._sink = self._spec["sink"]
        
    def crd_name(self):
        return self._metadata["name"]
            
    def any_versions(self):
        return "name=" + self.crd_name()

    def service(self, owner_refs):
	    name = self.crd_name() + "-" + random_generator()
	    return {
                "apiVersion": "serving.knative.dev/v1alpha1",
                "kind": "Service",
                "metadata": {
                    "name": name,
                    "ownerReferences": owner_refs,
                    "labels": {
                        "name": name,
                    }
                },
                "spec": {
                    "runLatest": {
                        "configuration": {
                            "revisionTemplate": {
                                "spec": {
                                    "container": {
                                        "image": "gcr.io/triggermesh/gitlabreceiver",
                                        "env": [
                                             {
                                                 "name": "CHANNEL",
                                                 "value": "test"
                                             },
                                             {
                                                 "name": "NAMESPACE",
                                                 "value": "default"
                                             }
                                        ],
                                    },
                                },
                            },
                        },
                    },
                },	
        }
     
def create_gitlab_webhook(source, service_name):
    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=get_gitlab_personal_token())

    project = gl.projects.get(source._ownerandrepo) 
    hook = {}
    hook["url"] = 'http://' + service_name + '.' + source._namespace + '.dev.triggermesh.io'
    
    for events in source._eventtype:
        hook[events] = 'true'
	
    try:
        hook = project.hooks.create(hook)
    except gitlabexceptions as e:
        logging.error("Could not create the gitlab webhook: %s, got error %e" % (service_name, e))   

def get_gitlab_personal_token():
	# look in other namespaces as well
    config.load_kube_config()
    v1=client.CoreV1Api()
    for secrets in v1.list_namespaced_secret("default").items:
        if secrets.metadata.name == 'gitlabsecret':
            return base64.b64decode(secrets.data['accessToken'])

def random_generator(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def create_meta(source):
    crds = client.CustomObjectsApi()
    controller_ref = {
        "apiVersion": source._apiversion.rstrip("/v1"),
        "blockOwnerDeletion": True,
        "kind": source._kind,
        "name": source.crd_name(),
        "uid": source._metadata["uid"],
    }
    logging.warning("Owner's reference: %s", json.dumps(controller_ref))

    try:
        bob = crds.create_namespaced_custom_object(namespace=source._namespace, group="serving.knative.dev", \
                                                   version="v1alpha1", plural="services", \
                                                   body=source.service([controller_ref]), pretty="true")
        logging.warning("Created Knative Service: %s", bob["metadata"]["name"])
    except ApiException as e:
	    print("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)

    create_gitlab_webhook(source, bob["metadata"]["name"])
        
def update_meta(gl):
    try:
        create_meta(gl)
    except ApiException as e:
        if e.status != http.client.CONFLICT:
            raise e
        
def process_meta(t, gl, obj):
    if t == "DELETED":
        logging.warning("Deleted CRD, check garbage collection")
    elif t in ["MODIFIED", "ADDED"]:
        update_meta(gl)
    else:
        logging.error("Unrecognized type: %s", t)

def main():
    #config.load_incluster_config()
    config.load_kube_config()

    resource_version = ""
    apps_beta1 = client.AppsV1beta1Api()
    crds = client.CustomObjectsApi()

    ns = os.getenv('MY_NAMESPACE', 'sebgoa')

    while True:
        stream = watch.Watch().stream(crds.list_namespaced_custom_object,
                                      GROUP, VERSION, ns, PLURAL, 
                                      resource_version=resource_version)
        for event in stream:
            try:
                t = event["type"]
                obj = event["object"]
                gl = GitLabSource(obj, ns)
                logging.warning("GitLabSource %s, %s" % (gl.crd_name(),t))  
                process_meta(t, gl, obj)

                # Configure where to resume streaming.
                metadata = obj.get("metadata")
                if metadata:
                    resource_version = metadata["resourceVersion"]
            except:
                logging.exception("Error handling event")

if __name__ == "__main__":
    main()
