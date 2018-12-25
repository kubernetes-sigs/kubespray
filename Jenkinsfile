@Library('pipelinex@development')
import com.iguazio.pipelinex.DockerRepo

properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '30', numToKeepStr: '1000')),
    disableConcurrentBuilds()
])


timestamps {
common.notify_slack {
nodes.any_builder_node {
    stage('git clone') {
        deleteDir()
        checkout scm
    }

    def image = stage('build') {
        return docker.build("kubespray:${env.BRANCH_NAME}")
    }

    try {
        dockerx.images_push([image.id], DockerRepo.ARTIFACTORY_IGUAZIO)
    } finally {
        common.shell(['docker', 'rmi', image.id])
    }
}}}
