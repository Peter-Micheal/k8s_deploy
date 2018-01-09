import yaml
from kubernetes import client, config

def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config('k8sconfig')

    with open("configmap.yaml") as f:
        dep = yaml.load(f)
        print dep
        k8s = client.CoreV1Api()
        resp = k8s.create_namespaced_config_map(
            body=dep, namespace="default")
        print resp


if __name__ == '__main__':
    main()

    {'kind': 'ReplicationController', 'spec': {'selector': {'deploy.env': 'qa-01', 'deploy.app': 'jmbx-in'},
                                               'template': {'spec': {'containers': [{'livenessProbe': {
                                                   'initialDelaySeconds': 60,
                                                   'httpGet': {'path': '/Status/Version', 'port': 8080},
                                                   'timeoutSeconds': 3}, 'readiness_probe': {'initialDelaySeconds': 60,
                                                                                             'httpGet': {
                                                                                                 'path': '/Status/Version',
                                                                                                 'port': 8080},
                                                                                             'timeoutSeconds': 3},
                                                                                     'name': 'jmbx-in-qa-01', 'env': [
                                                       {'name': 'ENV_NAME', 'value': 'qa-01'},
                                                       {'name': 'APP_NAME', 'value': 'jmbx-in'},
                                                       {'name': 'CUR_TERM', 'value': '4'}],
                                                                                     'image': 'docker.jimubox.com/qa-01/jmbx-in:latest',
                                                                                     'resources': {
                                                                                         'requests': {'cpu': 0.1,
                                                                                                      'memory': '128Mi'},
                                                                                         'limits': {'cpu': 2.0,
                                                                                                    'memory': '8Gi'}}}]},
                                                            'metadata': {
                                                                'labels': {'deploy.env': 'qa-01', 'deploy.term': '4',
                                                                           'deploy.app': 'jmbx-in'},
                                                                'name': 'jmbx-in-qa-01'}}, 'replicas': 2},
     'apiVersion': 'v1', 'metadata': {'name': 'jmbx-in-qa-01.gen-4'}}