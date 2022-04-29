from flask import Flask, render_template, request
from kubernetes import client, config, utils
from kubernetes.client.api import core_v1_api
import time
import random
import string
import json

config.load_kube_config() # in pod
# config.load_incluster_config() # in container

app = Flask(__name__)
v1 =  client.CoreV1Api()


def open_pod(pod_name, image,target_port):
    # Create pod manifest
    pod_manifest = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
                'name': pod_name
        },
        'spec': {
            'containers': [{
                'image': image,
                'name': 'container',
                'ports':[
                    {'containerPort' : target_port }
                ]
            }]
        }
    }
    

    api_response = v1.create_namespaced_pod(body=pod_manifest,namespace='default')
    while True:
        api_response = v1.read_namespaced_pod(name=pod_name,namespace='default')
        if api_response.status.phase != 'Pending':
            break
        time.sleep(0.01)
    return api_response.metadata.annotations['cni.projectcalico.org/podIP'][:-3]
    # print(f'Pod {pod_name}  created.')


@app.route("/")
def root():
    return render_template('index.html')

@app.route("/api")
def api():
    event = request.args.get('event')
    if event == 'start':
        image_name = request.args.get('image')
        target_port = 8080
        pod_name = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
        ip_address = open_pod(pod_name,image_name,target_port)
        res = {'pod_name' : pod_name,'ip':ip_address,'port':target_port}
        return json.dumps(res)
    elif event == 'end':
        pod_name = request.args.get("pod_name")
        v1.delete_namespaced_pod(name=pod_name,namespace='default')
        res = {'status' : 'success'} 
        return json.dumps(res)
    return 'error_meow'

if __name__ == '__main__':
    app.debug = True
    app.run("0.0.0.0")

