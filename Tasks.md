TASK 1: Models to build:

1. document model

- id (primary key)
- document_name
- document_type
- document_size
- description
- user_id (foreign key)
- document_created_at
- document_updated_at

2. user

- id
- user_name
- user_email
- user_password
- user_role (admin, user) ## THIS SHOULD BE ENUM
- user_created_at
- user_updated_at

3. n8n_chat_history

- id
- session_id
- message

4. List down all the migrations commands and you don't need to run them.

TASK 2: Connect the S3 bucket to the application

- I want to connect the S3 bucket to the application to store the documents in the docs and PDF files.
- Create API's to upload the documents to the S3 bucket.
- Create API's to download with presigned URL the documents from the S3 bucket.
- Create API's to delete the documents from the S3 bucket.
- Create API's to list the documents from the S3 bucket.

TASK 3: Add the authentication in the swagger and all the API's should protected.

THIS IS THE ENV CONTENT :-

APP_NAME=Meat-AI-Assistant
AWS_ACCESS_KEY_ID=AKIAUS2DI4X4A
AWS_SECRET_ACCESS_KEY=fOuE1FnagDC3QtIv8sQv
AWS_REGION=ap-south-1
AWS_S3_BUCKET=ai-meat-assistant-documents-v1

## ONCE COMPLETE THE TASK CREATE A NEW FILE WITH THE NAME project-progress.md AND ADD THE PROGRESS OF THE TASK IN THE FILE.
