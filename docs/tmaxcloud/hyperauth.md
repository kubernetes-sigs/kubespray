# Hyperauth

kubespray로 Hyperauth 설치를 위해 inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml에서 설정해야하는 값은 다음과 같다.

```yml
hyperauth_enabled: hyperauth 설치 여부 (true/false)
hyperauth_version: hyperauth 서버 버전
```


### 예시
```yml
hyperauth_enabled: true
hyperauth_version: "latest"
```

### 설치 이후 해줘야 할 사항
* Self-Signed 인증서를 쓸 경우 (실제 인증서를 사용할 경우 생략 가능) (모든 마스터 노드에 대해서 밑의 과정을 진행 해야한다.)
    * os의 ca store에 인증서를 등록
    * sudo cp /etc/kubernetes/addons/hyperauth/ssl/hyperauth.crt /etc/pki/ca-trust/source/anchors/
    * sudo cp /etc/kubernetes/addons/hyperauth/ssl/hypercloud-root-ca.crt /etc/pki/ca-trust/source/anchors/
    * update-ca-trust
   
* https://https://hyperauth.hypercloud.shinhan.com/auth/ 접속 --> administration Console 클릭 --> admin / admin 접속
* Add realm - tmax realm 생성
    * ![image](https://user-images.githubusercontent.com/61040426/132936480-efa26157-a882-4752-840f-02586babbb8e.png)
* Clients 탭 - Create 클릭 - hypercloud5 client 생성
    * ![image](https://user-images.githubusercontent.com/61040426/132936497-0d01b0de-739a-46b1-9588-7128e25631a1.png)
* Users 탭 - Add User 클릭 - hc-admin@tmax.co.kr 유저 생성
    * ![image](https://user-images.githubusercontent.com/61040426/132936532-31682c48-5539-4940-97dd-95dbe3364ca0.png)
* hc-admin@tmax.co.kr 유저 - credentials 탭 - admin으로 비밀번호 초기화
    * ![image](https://user-images.githubusercontent.com/61040426/132936546-4669d2a0-4f9c-4f70-92f6-d6c4e9399672.png)
  
