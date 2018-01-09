#!/usr/bin/env python
"""
Usage: deploy.py [-h] -a=<app> -e=<env> -t=<tag> -c=<count>

Options:
  -a app           Set application.
  -e env           Set environment.
  -t tag           Set git tag.
  -c count         Set pod count.
  -h                    Show this screen.
"""
from kubernetes import client, config,watch
import docopt,sys,time

class Deploy(object):
    def __init__(self,_app,_env):
        self._app=_app
        self._env=_env
        self._config=config.load_kube_config('k8sconfig')
        self._k8s= client.CoreV1Api()
        self._name='{}-{}'.format(self._app, self._env)
        self._watch = watch.Watch()
        self._namespace='default'
    def __del__(self):
        self._watch.stop()
    def get_config(self):
        try:
            _cfg = self._k8s.read_namespaced_config_map(name=self._name, namespace=self._namespace).data
        except client.rest.ApiException:
            print 'read config failed,exit !'
            sys.exit(1)
        return _cfg
    def get_template(self,_template_name):
        try:
            _template = self._k8s.read_namespaced_config_map(name='template-'+_template_name, namespace=self._namespace).data[u'health_check']
        except client.rest.ApiException:
            print 'read template failed,exit !'
            sys.exit(1)
        return _template
    def chk_rc_exist(self,_term):
        _resp=None
        _new_term = int(_term) + 1
        _rc_name = self._name + '.gen-' + str(_new_term)
        try:
            _resp=self._k8s.read_namespaced_replication_controller_scale_with_http_info(name=_rc_name,namespace=self._namespace)
        except client.rest.ApiException as e:
            pass
        return _resp
    def create_rc(self,_count,_term,_image,_mem_limits,_cpu_limits,_template={}):
        _new_term=int(_term)+1
        _rc_name=self._name+'.gen-'+str(_new_term)
        _resp=[0,0]
        data={'apiVersion': 'v1', 'metadata': {'name': _rc_name},'kind': 'ReplicationController', 'spec': {'replicas': int(_count), 'template': {'spec': {'containers': [dict({'name': self._name,'image':_image,'env':[{'name':'ENV_NAME','value':self._env},{'name':'APP_NAME','value':self._app},{'name':'CUR_TERM','value':str(_new_term)}],'resources':{'limits':{'memory': _mem_limits,'cpu': float(_cpu_limits)},'requests':{'memory': '128Mi','cpu': 0.1}},},**_template)],"dnsPolicy": 'Default'}, 'metadata': {'labels': {'deploy.app': self._app, 'deploy.env': self._env,'deploy.term':str(_new_term)}, 'name': self._name}}, 'selector': {'deploy.app': self._app, 'deploy.env': self._env}}}
        _resp=self._k8s.create_namespaced_replication_controller_with_http_info(namespace=self._namespace,body=data)
        if _resp[1] !=201:
            print 'create rc failed,exit!'
            sys.exit(1)
        else:
            return _resp[0]
    def wait_term_updated(self,term):
        print 'Waiting for term to be updated......'
        expect_term=int(term)+1
        for configmap in self._watch.stream(self._k8s.list_namespaced_config_map,namespace=self._namespace,_request_timeout=300):
            if configmap[u'object'].metadata.labels=={u'type': 'application', u'system': 'True'}:
                if (configmap[u'object'].data['app']==self._app) and (configmap[u'object'].data['env']==self._env):
                    if expect_term==int(configmap[u'object'].data[u'current_term']):
                        self._watch.stop()
                        return 'Deploy Done!'
    def remove_old_rc(self,term):
        ret=None
        _rc_name = self._name + '.gen-' + term
        delete_opts = client.V1DeleteOptions(grace_period_seconds=60, propagation_policy='Foreground')
        try:
            ret=self._k8s.delete_namespaced_replication_controller_with_http_info(name=_rc_name,namespace=self._namespace,body=delete_opts,_return_http_data_only=True)
        except Exception as e:
            print e, 'ignore error when kill old term failed!'
        return ret


def main():
    opts = docopt.docopt(__doc__, version='0.1')
    app = opts['-a']
    env = opts['-e']
    tag = opts['-t']
    count = opts['-c']
    deploy=Deploy(app,env)
    cfg=deploy.get_config()
    cpu_limit=cfg['cpu']
    template=eval(deploy.get_template(cfg['template']))
    memory_limit=cfg['memory']
    volumes=cfg['volumes']
    term=cfg['current_term']
    IMAGE_BASE='docker.jimubox.com/{}/{}:{}'.format(env,app,tag)
    if deploy.chk_rc_exist(term):
        print 'delete old rc\n',deploy.remove_old_rc(str(int(term)+1))
        while True:
            time.sleep(1)
            if not deploy.chk_rc_exist(term):
                break
    print deploy.create_rc(count,term,IMAGE_BASE,memory_limit,cpu_limit,template)
    print deploy.wait_term_updated(term)
    print deploy.remove_old_rc(term)
if __name__ == '__main__':
    main()
