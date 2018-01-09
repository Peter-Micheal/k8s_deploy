* 这是一个基于k8s的自定义发布脚本，创建rc，生产nginx upstream并重载nginx
* deploy.py用于创建rc并监听service term变化返回给rundeck
* gen_upstream.py监听service endpoint 并将变化更新生产新的nginx upstream，并重载nginx
