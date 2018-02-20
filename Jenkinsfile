pipeline {
  agent any
  stages {
    stage('error') {
      steps {
        validateDeclarativePipeline 'Jenkinsfile\''
      }
    }
    stage('deploy') {
      steps {
        validateDeclarativePipeline 'Jenkinsfile'
      }
    }
  }
}