import yaml
from kubernetes import client, config

def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config('k8sconfig')

    with open("test.yaml") as f:
        dep = yaml.load(f)
        print dep
#        k8s = client.CoreV1Api()
#        resp = k8s.create_namespaced_replication_controller(body=dep, namespace="default")
#        print resp


if __name__ == '__main__':
    main()