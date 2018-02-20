pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        sh 'ls -la'
        sh 'pwd'
      }
    }
    stage('test') {
      steps {
        validateDeclarativePipeline 'Jenkinsfile'
      }
    }
    stage('deploy') {
      steps {
        echo 'finish'
      }
    }
  }
}