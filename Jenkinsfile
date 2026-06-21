pipeline {
    agent { docker { image 'python:3.11' } }

    stages {
        stage('Lint') {
            steps {
                sh 'pip install -e ".[dev]"'
                sh 'ruff check cpe_ta tests'
            }
        }
        stage('Typecheck') {
            steps {
                sh 'mypy --strict cpe_ta/core cpe_ta/hal/base.py'
            }
        }
        stage('Unit Tests') {
            steps {
                sh 'pytest -m "not hardware" -n auto --junitxml=test-results.xml --cov=cpe_ta --cov-report=term'
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
        stage('Generate Report') {
            steps {
                sh 'cpe-ta report --input test-results.xml --output report.html || true'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report.html', allowEmptyArchive: true
                }
            }
        }
    }

    triggers {
        cron('H 2 * * *')  // Nightly regression
    }

    post {
        always {
            cleanWs()
        }
    }
}
