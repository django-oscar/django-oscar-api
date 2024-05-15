#!/usr/bin/env groovy

pipeline {
    agent { label 'GEITENPETRA' }
    options { disableConcurrentBuilds() }

    stages {
        stage('Build') {
            steps {
                withPythonEnv('System-CPython-3.10') {
                    withEnv(['PIP_INDEX_URL=https://pypi.uwkm.nl/voxyan/oscar/+simple/']) {
                        pysh "make install"
                    }
                }
            }
        }
        stage('Lint') {
            steps {
                withPythonEnv('System-CPython-3.10') {
                    pysh "make lint"
                }
            }
        }
        stage('Test') {
            steps {
                withPythonEnv('System-CPython-3.10') {
                    pysh "make coverage"
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: '**/nosetests.xml'
                }
                success {
                    step([
                        $class: 'CoberturaPublisher',
                        coberturaReportFile: '**/coverage.xml',
                    ])
                }
            }
        }
    }
    post {
        always {
            echo 'This will always run'
        }
        success {
            echo 'This will run only if successful'
            withPythonEnv('System-CPython-3.10') {
                echo 'This will run only if successful'
                pysh "version --plugin=wheel -B${env.BUILD_NUMBER} --skip-build"
                sh "which git"
                sh "git push --tags"
            }
        }
        failure {
            emailext subject: "JENKINS-NOTIFICATION: ${currentBuild.currentResult}: Job '${env.JOB_NAME} #${env.BUILD_NUMBER}'",
                    body: '${SCRIPT, template="groovy-text.template"}',
                    recipientProviders: [culprits(), brokenBuildSuspects(), brokenTestsSuspects()]

        }
        unstable {
            echo 'This will run only if the run was marked as unstable'
        }
        changed {
            echo 'This will run only if the state of the Pipeline has changed'
            echo 'For example, if the Pipeline was previously failing but is now successful'
        }
    }
}
