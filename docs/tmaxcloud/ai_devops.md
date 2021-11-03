# ai_devops prerequisites

ai_devops를 설치하기 위해서는 먼저 다음과 같은 모듈들이 설치되어야한다.

1. Storage class
    * 아래 명령어를 통해 storage class가 설치되어 있는지 확인한다.
        ```bash
        $ kubectl get storageclass
        ```
    * 만약 storage class가 없다면 storage class를 설치해준다.
    * Storage class는 있지만 default로 설정된 것이 없다면 아래 명령어를 실행한다.(storage class로 rook-ceph이 설치되어 있을 경우에만 해당)
        ```bash
        $ kubectl patch storageclass csi-cephfs-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
        ```
    * csi-cephfs-sc는 rook-ceph를 설치했을 때 생성되는 storage class이며 다른 storage class를 default로 사용해도 무관하다.
2. Istio
    * v1.5.1       
    * kubeflow-istio-resource들을 배포하기 위해 필요하다.
3. Cert-manager
    * ai-devops에서 사용하는 certificate와 cluster-issuer와 같은 CR 관리를 위해 필요하다.            
4. Hypercloud Console    
    * notebook과 관련하여 ConsoleYAMlSample을 적용하기 위해 필요하다.
5. (Optional) GPU plug-in
    * Kubernetes cluster 내 node에 GPU가 탑재되어 있으며 AI DevOps 기능을 사용할 때 GPU가 요구될 경우에 필요하다.
     
# ai-devops 설정

kubespray로 ai-devops 설치를 위해 roles/kubernetes-apps/ai_devops/defaults/main.yml에서 설정해야하는 값은 다음과 같다.
예시들은 기본 설정 값들이다.

# ai_devops 모듈 설치 namespace

ai_devops의 모듈들이 설치되는 namespace

```yml
ai_devops_namespace: "kubeflow"
istio_namespace: "istio-system"
knative_namespace: "knative-serving"
```

# 1. cluster-local-gateway parameters

istio proxy 이미지/tag

```yml
istio_proxyv_image_repo: "{{ docker_image_repo }}/istio/proxyv2"
istio_proxyv_image_tag: "1.3.1"
```

# 2. kubeflow-istio-resources parameters

gatewayselector 설정

```yml
gatewaySelector: ingressgateway
```

# 3. application parameters

'application' crd를 관리하는 controller image/tag

```yml
application_controller_image_repo: "{{ gcr_image_repo }}/kubeflow-images-public/kubernetes-sigs/application"
application_controller_image_tag: "1.0-beta"
```

# 4. kubeflow-apps parameters

ai-devops를 위한 namespace를 관리하는 profiles 이미지/tag

```yml
profiles_deployment_image_repo: "{{ gcr_image_repo }}/kubeflow-images-public/profile-controller"
profiles_deployment_image_tag: "vmaster-ga49f658f"
profiles_deployment_image_2_repo: "{{ gcr_image_repo }}/kubeflow-images-public/kfam"
profiles_deployment_image_2_tag: "vmaster-g9f3bfd00"
```

# 5. katib parameters

Controller(crd 관리), UI, DB, DB-manager로 구성된 katib 모듈 관련 이미지/tag

```yml
default_trial_template_image_repo: "{{ docker_image_repo }}/kubeflowkatib/mxnet-mnist"
default_trial_template_image_tag: "v1beta1-45c5727"
default_trial_template_image_2_repo: "{{ docker_image_repo }}/kubeflowkatib/enas-cnn-cifar10-cpu"
default_trial_template_image_2_tag: "v1beta1-45c5727"
default_trial_template_image_3_repo: "{{ docker_image_repo }}/kubeflowkatib/pytorch-mnist"
default_trial_template_image_3_tag: "v1beta1-45c5727"
katib_controller_image_repo: "{{ docker_image_repo }}/kubeflowkatib/katib-controller"
katib_controller_image_tag: "v0.11.0"
katib_db_manager_image_repo: "{{ docker_image_repo }}/kubeflowkatib/katib-db-manager"
katib_db_manager_image_tag: "v0.11.0"
mysql_deploy_image_repo: "{{ mysql_image_repo }}"
mysql_deploy_image_tag: "8.0.27"
katib_ui_image_repo: "{{ docker_image_repo }}/kubeflowkatib/katib-ui"
katib_ui_image_tag: "v0.11.0"
katib_cert_generator_image_repo: "{{ docker_image_repo }}/kubeflowkatib/cert-generator"
katib_cert_generator_image_tag: "v0.11.0"
katib_early_stopping_image_repo: "{{ docker_image_repo }}/kubeflowkatib/earlystopping-medianstop"
katib_early_stopping_image_tag: "latest"
katib_metrics_collector_image_repo: "{{ docker_image_repo }}/kubeflowkatib/file-metrics-collector"
katib_metrics_collector_image_tag: "latest"
katib_tfevent_collector_image_repo: "{{ docker_image_repo }}/kubeflowkatib/tfevent-metrics-collector"
katib_tfevent_collector_image_tag: "latest"
katib_suggestion_image_repo_1: "{{ docker_image_repo }}/kubeflowkatib/suggestion-hyperopt"
katib_suggestion_image_tag_1: "latest"
katib_suggestion_image_repo_2: "{{ docker_image_repo }}/kubeflowkatib/suggestion-chocolate"
katib_suggestion_image_tag_2: "latest"
katib_suggestion_image_repo_3: "{{ docker_image_repo }}/kubeflowkatib/suggestion-hyperband"
katib_suggestion_image_tag_3: "latest"
katib_suggestion_image_repo_4: "{{ docker_image_repo }}/kubeflowkatib/suggestion-skopt"
katib_suggestion_image_tag_4: "latest"
katib_suggestion_image_repo_5: "{{ docker_image_repo }}/kubeflowkatib/suggestion-goptuna"
katib_suggestion_image_tag_5: "latest"
katib_suggestion_image_repo_6: "{{ docker_image_repo }}/kubeflowkatib/suggestion-enas"
katib_suggestion_image_tag_6: "latest"
katib_suggestion_image_repo_7: "{{ docker_image_repo }}/kubeflowkatib/suggestion-darts"
katib_suggestion_image_tag_7: "latest"
```

# 6. argo parameters

argo 모듈 관련 Controller, executor, server 이미지/tag

```yml
executor_image_repo: "{{ docker_image_repo }}/argoproj/argoexec"
executor_image_tag: "v2.12.10"
argo_server_image_repo: "{{ docker_image_repo }}/argoproj/argocli"
argo_server_image_tag: "v2.12.10"
workflow_controller_image_repo: "{{ docker_image_repo }}argoproj/workflow-controller"
workflow_controller_image_repo: "v2.12.10"
```

# 7. minio parameters

minio storage server 이미지/tag

```yml
minio_image_repo: "{{ gcr_image_repo }}/ml-pipeline/minio"
minio_image_tag: "RELEASE.2019-08-14T20-37-41Z-license-compliance"
```

# 8. notebook parameters

notebook controller 이미지/tag, consoleyamlsample 관련 이미지/tag

```yml
notebook_controller_image_repo: "{{ docker_image_repo }}/tmaxcloudck/notebook-controller-go"
notebook_controller_image_tag: "b0.1.0"
jupyter_lab_kale_image_repo: "{{ docker_image_repo }}/tmaxcloudck/jupyterlab-kale"
jupyter_lab_kale_image_tag: "b1.0.1"
```

# 9. pytorchjob parameters

pytorch operator 이미지/tag

```yml
pytorch_operator_image_repo: "{{ gcr_image_repo }}/kubeflow-images-public/pytorch-operator"
pytorch_operator_image_tag: "vmaster-g518f9c76"
```

# 10. tfjob parameters

tfjob operator 이미지/tag

```yml
tf_job_operator_image_repo: "{{ gcr_image_repo }}/kubeflow-images-public/tf_operator"
tf_job_operator_image_tag: "vmaster-gda226016"
```

# 11. knative parameters

knative 모듈 관련 이미지/tag

```yml
queue_sidecar_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/serving/cmd/queue"
queue_sidecar_image_tag: "v0.14.3"
activator_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/serving/cmd/activator"
activator_image_tag: "v0.14.3"
autoscaler_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/serving/cmd/autoscaler"
autoscaler_image_tag: "v0.14.3"
controller_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/serving/cmd/controller"
controller_image_tag: "v0.14.3"
istio_webhook_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/net-istio/cmd/webhook"
istio_webhook_image_tag: "v0.14.1"
networking_istio_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/net-istio/cmd/controller"
networking_istio_image_tag: "v0.14.1"
webhook_image_repo: "{{ gcr_image_repo }}/knative-releases/knative.dev/serving/cmd/webhook"
webhook_image_tag: "v0.14.3"
```

# 12. kfserving parameters

kfserving 모듈 관련 이미지/tag

```yml
kfserving_controller_image_repo: "{{ gcr_image_repo }}/kfserving/kfserving-controller"
kfserving_controller_image_tag: "v0.5.1"
kube_rbac_proxy_image_repo: "{{ gcr_image_repo }}/kubebuilder/kube-rbac-proxy"
kube_rbac_proxy_image_tag: "v0.4.0"
kfserving_agent_image_repo: "{{ docker_image_repo }}/kfserving/agent"
kfserving_agent_image_tag: "v0.5.1"
alibi_explainer_image_repo: "{{ docker_image_repo }}/kfserving/alibi-explainer"
alibi_explainer_image_tag: "v0.5.1"
aix_explainer_image_repo: "{{ docker_image_repo }}/kfserving/aix-explainer"
aix_explainer_image_tag: "v0.5.1"
art_explainer_image_repo: "{{ docker_image_repo }}/kfserving/art-explainer"
art_explainer_image_tag: "v0.5.1"
tensorflow_image_repo: "{{ docker_image_repo }}/tensorflow/serving"
tensorflow_image_tag: "1.14.0"
tensorflow_image_gpu_tag: "1.14.0-gpu"
onnx_image_repo: "{{ mcr_image_repo }}/onnxruntime/server"
onnx_image_tag: "v1.0.0"
sklearn_image_repo: "{{ gcr_image_repo }}/kfserving/sklearnserver"
sklearn_image_tag: "v0.5.1"
mlserver_image_repo: "{{ docker_image_repo }}/seldonio/mlserver"
mlserver_image_tag: "0.2.1"
xgboost_image_repo: "{{ gcr_image_repo }}/kfserving/xgbserver"
xgboost_image_tag: "v0.5.1"
pytorch_server_image_repo: "{{ gcr_image_repo }}/kfserving/pytorchserver"
pytorch_server_image_tag: "v0.5.1"
pytorch_server_image_gpu_tag: "v0.5.1-gpu"
torchserve_kfs_image_repo: "{{ docker_image_repo }}/kfserving/torchserve-kfs"
torchserve_kfs_image_tag: "0.3.0"
torchserve_kfs_image_gpu_tag: "0.3.0-gpu"
triton_image_repo: "{{ nvcr_image_repo }}/nvidia/tritonserver"
triton_image_tag: "20.08-py3"
pmml_image_repo: "{{ docker_image_repo }}/kfserving/pmmlserver"
pmml_image_tag: "v0.5.1"
lgb_image_repo: "{{ docker_image_repo }}/kfserving/lgbserver"
lgb_image_tag: "v0.5.1"
storage_initializer_image_repo: "{{ gcr_image_repo }}/kfserving/storage-initializer"
storage_initializer_image_tag: "v0.5.1"
```



 
                          
 
                          


