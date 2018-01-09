#!/usr/bin/env python
#coding=utf-8
"""
Usage: gen_upstream.py [-h] -d=<dir> -c=<cmd>

Options:
  -d dir           Set generated upstream directory.
  -c cmd           Set nginx hooks scrpit.
  -h                    Show this screen.
"""
from kubernetes import client, config, watch
import sys,docopt,os
from datetime import datetime

class Upstream(object):
    def __init__(self):
        self._config=config.load_kube_config('k8sconfig')
        self._watch=watch.Watch()
        self._client=client
        self._client.configuration.connection_pool_maxsize=50
        self._k8s= self._client.CoreV1Api()
        self._namespace = 'default'
    def __del__(self):
        self._watch.stop()
    def get_config(self,app,env):
        self._app=app
        self._env=env
        self._name = '{}-{}'.format(app, env)
        try:
            _cfg = self._k8s.read_namespaced_config_map(name=self._name, namespace=self._namespace).data
        except client.rest.ApiException as e:
            print 'read config failed,exit !',e
            return None
        return _cfg
    def get_event(self):
        for _event in self._watch.stream(self._k8s.list_namespaced_endpoints,namespace=self._namespace):
            yield _event
    def generate_upstream(self,dir_path,iplist,term):
        if iplist:
            '''处理endpoint 可服务IP地址为空'''
            _servers=''
            for ip in iplist:
                _servers+='server {}:8080;\n'.format(ip)
            if not dir_path.endswith('/'):
                dir_path+='/'
            file_name=dir_path+'upstream_auto.{}.{}.conf'.format(self._app,self._env)
            content='''# Generated at {}
# app = {}
# env = {}
# term = {}
# port = 8080

upstream auto.{}.{} '''.format(datetime.now(),self._app,self._env,str(term),self._app,self._env)+'{\n'+_servers+'}\n'
            with open(file_name,'w') as upstream_file:
                upstream_file.write(content)
            return upstream_file.name
    def update_term(self,newterm):
        data={'data':{'current_term': str(newterm)}}
        _ret=self._k8s.patch_namespaced_config_map(name=self._name,namespace=self._namespace,body=data)
        if _ret:
            return True
    def nginx_hooks(self,cmd):
        _ret=os.system(cmd)
        if not _ret==0:
            return 'nginx hook scripts error'
            sys.exit(1)
        else:
            return 'nginx hook scrpts successful'


def main():
    opts = docopt.docopt(__doc__, version='0.1')
    gen_dir= opts['-d']
    cmd=opts['-c']
    upstream=Upstream()
    count=0
    for event in upstream.get_event():
        upstream = Upstream()
        newterm_iplist, term_iplist = [], []
        count +=1
        print 'count',count
        if event[u'object'].metadata.name == 'kubernetes':
            continue
        if event[u'type']==u'ADDED':
            continue
        if not event[u'object'].subsets:
            continue
        app,env=event[u'object'].metadata.name.split('-----')
        cfg=upstream.get_config(app,env)
        if not cfg:
            continue
        old_term= int(cfg['current_term']) -1
        new_term = int(cfg['current_term']) + 1
        old_pod_name='{}-{}.gen-{}'.format(app,env,old_term)
        pod_name='{}-{}.gen-{}'.format(app,env,cfg['current_term'])
        new_pod_name = '{}-{}.gen-{}'.format(app,env,str(new_term))
        if event[u'object'].subsets[0].not_ready_addresses == None:
            print event
            for pod in event[u'object'].subsets[0].addresses:
                if new_pod_name in pod.target_ref.name:
                    newterm_iplist.append(pod.ip)
                    print 'newterm_iplist',newterm_iplist
                elif pod_name in pod.target_ref.name:
                    term_iplist.append(pod.ip)
                    print 'term_iplist', term_iplist
                elif old_pod_name in pod.target_ref.name:
                    '忽略删除老的rc时引起的异常'
                    pass
                else:
                    print 'error,there is a unknow pod name\nexpect {}&{}&{}\t current_pod_name:{}'.format(new_pod_name,pod_name,pod.target_ref.name)
                    sys.exit(1)
            if (term_iplist!=None) and (newterm_iplist==None):
                print 'self heal upstream to {}'.format(upstream.generate_upstream(gen_dir, term_iplist, cfg['current_term']))
            elif (term_iplist ==None) and (newterm_iplist==None) :
                print 'this is a new endpoints without any pod!'
            else:
                print 'ready to update upstream!'
                upstream_path=upstream.generate_upstream(gen_dir,newterm_iplist,new_term)
                if upstream_path:
                    print 'write upstream to {}'.format(upstream_path)
                    print upstream.nginx_hooks(cmd)
                    upstream.update_term(new_term)
if __name__ == '__main__':
    main()
