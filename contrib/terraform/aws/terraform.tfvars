deploymentName="test-kube-deploy"

numControllers="2"
numEtcd="3"
numNodes="2"

volSizeController="20"
volSizeEtcd="20"
volSizeNodes="20"

awsRegion="us-west-2"
subnet="subnet-xxxxx"
ami="ami-32a85152"
securityGroups="sg-xxxxx"
SSHUser="core"
SSHKey="my-key"

master_instance_type="m3.xlarge"
etcd_instance_type="m3.xlarge"
node_instance_type="m3.xlarge"

terminate_protect="false"
