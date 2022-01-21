# TwitterSpy
App for Cloud Computing 2021 classes


run shell scripts in order to deploy

 1-create-bucket.sh - creates an s3 bucket on your account for artifact storage (needed during deployment) creates a file bucket-name.txt, needed during next stage
 don't run if bucket already exists and the file is present to avoid crating multiple buckets
 
 2-deploy.sh - deploys the stack (creates or updates if already exists). If bucket was already created you need to run only this (eg. when updating the stack)

3-initialize-topics.sh - create initial topics and registers them in database. Run only if topics do not exist yet
