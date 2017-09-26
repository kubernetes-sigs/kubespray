##lifesene业务

###命令空间
**1. 创建namespace**
```
kubectl create namespace lifesense-qa2
```
**2. 创建LimitRange配置**
```
kubectl apply -f rq-limits.yaml -n lifesense-qa2
kubectl describe limits -n lifesense-qa2
```
**3. 创建Deployment**
```
kubectl apply -f rest-controller.yaml -n lifesense-qa2
kubectl apply -f soa-controller.yaml -n lifesense-qa2
```
**4. 创建Deployment**
```
kubectl apply -f  rest-service.yaml -n lifesense-qa2
```