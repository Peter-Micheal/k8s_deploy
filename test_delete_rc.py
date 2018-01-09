import yaml
from kubernetes import client, config

def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config('k8sconfig')
    k8s = client.CoreV1Api()
    data=client.V1DeleteOptions(grace_period_seconds=60,propagation_policy='Foreground')
    print data
    resp=k8s.delete_namespaced_replication_controller(body=data, namespace="default",name='jmbx-in-qa-01.gen-48')
    print resp

if __name__ == '__main__':
    main()