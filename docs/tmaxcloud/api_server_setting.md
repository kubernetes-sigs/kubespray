
# Kube-API server 설정 변경 
    
- oidc 변경

    `inventory/tmaxcloud/group_vars/k8s_cluster/k8s_cluster.yml` 에서
    `kube_oidc_auth`을 true로 변경 후, 원하는 OIDC 변수 값을 변경한다.

    사용하지 않는 변수는 주석 처리한다. 


    ```bash
    ## It is possible to activate / deactivate selected authentication methods (oidc, static token auth)
    kube_oidc_auth: false
    # kube_token_auth: false


    ## Variables for OpenID Connect Configuration https://kubernetes.io/docs/admin/authentication/
    ## To use OpenID you have to deploy additional an OpenID Provider (e.g Dex, Keycloak, ...)

    # kube_oidc_url: https://hyperauth.{{ custom_domain_name }}/auth/realms/tmax
    # kube_oidc_client_id: hypercloud5
    ## Optional settings for OIDC
    # kube_oidc_ca_file: "{{ kube_cert_dir }}/ca.pem"
    # kube_oidc_username_claim: preferred_username
    # kube_oidc_username_prefix: '-'
    # kube_oidc_groups_claim: group
    # kube_oidc_groups_prefix: 'oidc:'
    ```

    <br/>    

    예시)

    ``` bash
    ## It is possible to activate / deactivate selected authentication methods (oidc, static token auth)
    kube_oidc_auth: true
    # kube_token_auth: false


    ## Variables for OpenID Connect Configuration https://kubernetes.io/docs/admin/authentication/
    ## To use OpenID you have to deploy additional an OpenID Provider (e.g Dex, Keycloak, ...)

    kube_oidc_url: https://hyperauth.{{ custom_domain_name }}/auth/realms/tmax
    kube_oidc_client_id: hypercloud5
    ## Optional settings for OIDC
    # kube_oidc_ca_file: "{{ kube_cert_dir }}/ca.pem"
    kube_oidc_username_claim: preferred_username
    kube_oidc_username_prefix: '-'
    kube_oidc_groups_claim: group
    # kube_oidc_groups_prefix: 'oidc:'

    ```


<br/>    


- audit 변경
        
    `inventory/tmaxcloud/group_vars/k8s_cluster/k8s_cluster.yml` 에서

    `kubernetes_audit`와 `kubernetes_audit_webhook`을 모두 true로 변경 후, 원하는 변수 값을 변경한다.

    사용하지 않는 값은 주석 처리한다. 

    ```bash
    # audit log for kubernetes
    kubernetes_audit: false
    # audit_policy_file: "{{ kube_config_dir }}[AUDIT_POLICY_FILE]"

    # audit webhook for kubernetes
    kubernetes_audit_webhook: false
    # audit_webhook_config_file: "{{ kube_config_dir }}[AUDIT_WEBHOOK_CONFIG_FILE]"
    # audit_webhook_mode: [AUDIT_WEBHOOK_MODE]
    ```

    <br/>

    예시)

    ``` bash

    # audit log for kubernetes
    kubernetes_audit: true
    audit_policy_file: "{{ kube_config_dir }}/pki/audit-policy.yaml"

    # audit webhook for kubernetes
    kubernetes_audit_webhook: true
    audit_webhook_config_file: "{{ kube_config_dir }}/pki/audit-webhook-config"
    audit_webhook_mode: batch

    ```