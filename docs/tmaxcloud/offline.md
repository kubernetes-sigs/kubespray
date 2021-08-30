# offline 환경 설정

offline 환경에서의 kubespray 설치를 위해 inventory/tmaxcloud/group_vars/all/offline.yml 을 수정한다.

```yml
is_this_offline: offline 환경일시 true, online 환경일시 false
registry_host: private registry 주소
files_repo: file repo 경로
```

### 예시

예를 들어 아래와 같이 변수들의 값을 설정한다.

```yml
is_this_offline: true
registry_host: "10.0.10.50:5000"
files_repo: "file:///tmp/files-repo"
```
