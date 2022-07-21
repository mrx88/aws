# Migrate AWS S3 buckets


## Introduction

Program that migrates files from one S3 bucket to another. In our case, we needed to migrate image files with old  /image path from old S3 bucket to the new one with new /avatar path. In addition, paths in the Postgres database will be updated accordingly as well.

Components:

- `proddatabase` PostgreSQL database
- `production-s3` AWS S3 bucket
- `legacy-s3` AWS S3 bucket

In our example we used PostgreSQL database deployed to Kubernetes cluster using Helm (bitnami/postgresql chart).

Terraform was used to deploy example AWS S3 buckets.

## Usage

```
 ~/devel/myplayground/  develop !1  python migrate.py --help 
Usage: migrate.py [OPTIONS]

  Tool to migrate legacy image objects from old S3 bucket  to new S3 bucket.

  Args:     dbconn (string): Database connection string

Options:
  --dbconn TEXT                Database connection string  [required]
  --old_bucket TEXT            Old S3 bucket name
  --modern_bucket TEXT         New S3 bucket name
  --delete_old_images BOOLEAN  If True delete files from old S3 bucket
  --help                       Show this message and exit.

  python migrate.py --dbconn postgres://postgres:<pw>@127.0.0.1/proddatabase --old_bucket legacy-s3 --modern_bucket production-s3

  To remove old files from legacy S3 bucket as well:

  python migrate.py --dbconn postgres://postgres:<password>@127.0.0.1/proddatabase --old_bucket legacy-s3 --modern_bucket production-s3 --delete_old_images True
  ```

  Or run as Docker container:

  ```
  docker build --pull --rm -f "Dockerfile" -t migrates3buckets:latest "." 
  docker run migrates3buckets --help
  ```

## Prerequisites

* AWS CLI installed and configured to interact with boto3 python lib
```
aws --version
aws-cli/2.5.8 Python/3.9.11 Linux/5.10.16.3-microsoft-standard-WSL2 exe/x86_64.debian.11 prompt/off

cat ~/.aws/credentials
[default]
aws_access_key_id = <your access key id>
aws_secret_access_key = <your access key>
```

**Set up development environment**

* Using python 3.10.0 and pyenv:
 ```
~/devel/myplayground/  develop ?2   echo "3.10.0" > .python-version     
~/devel/myplayground/  develop ?2   python --version 
Python 3.10.0
```

* Set up Python virtual env using pipenv

```
~/devel/myplayground/ develop ?2  pipenv --python 3.10.0 
Creating a virtualenv for this project...

pipenv shell

Install deps:
pipenv install psycopg2
pipenv install boto3
pipenv install click
pipenv install botocore

Install linters for development:
pipenv install flake8 --dev
pipenv install pycodestyle --dev
pipenv install autopep8 --dev

# If needed, generate pip requirements.txt
pipenv run pip freeze > requirements.txt
```
Note: When using Debian 11, "sudo apt install libpq-dev" might be needed for "psycopg2" python library.


* Set up AWS S3 buckets, using IaC and Terraform

```
  ~/devel/myplayground/  develop +1  cd terraform  
 
 Initialize Terraform AWS provider:   
  ~/devel/myplayground/terraform  develop +1  terraform init  

  ~/d/myplayground/terraform  develop +1 !2 ?4  terraform validate                                                                               
Success! The configuration is valid.


* Create buckets:
 ~/devel/myplayground/terraform  develop +1 !2 ?4  terraform apply 
...
aws_s3_bucket_acl.bucket2: Creation complete after 0s [id=legacy-s3,private]
aws_s3_bucket_acl.bucket1: Creation complete after 0s [id=production-s3,private]
```

* Set up local K8s cluster for development using Kind

```
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-linux-amd64
chmod +x kind
sudo mv kind /usr/local/bin/
kind create cluster
kubectl config use-context kind-kind
```

* Install postgresql to k8s cluster using Helm

```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install postgresql-ha bitnami/postgresql-ha

or if Helm chart is downloaded locally:

cd helm/postgresql-ha/
helm install -f values.yaml postgresql-ha .

```


* Connect to database and install provided schema

```
Get password for postgres:
kubectl get secret --namespace payments postgresql-ha-postgresql -o jsonpath="{.data.postgresql-password}" | base64 -d

Port forward k8s postgres to localhost:
kubectl port-forward --namespace payments svc/postgresql-ha-pgpool 5432:5432

Connect:
pgcli -h 127.0.0.1 -p 5432 -U postgres -d postgres 

Create new db / tables:
                                                   
postgres@127:postgres> CREATE DATABASE proddatabase;
\c proddatabase
 CREATE TABLE IF NOT EXISTS avatars (
   id SERIAL PRIMARY KEY,
   path VARCHAR
 );
CREATE DATABASE
CREATE TABLE

```

* Set up 5 legacy avatars (images with old path) to S3 bucket and PostgreSQL table:

```
Created 5 legacy avatars:

postgres@127:proddatabase> select * from avatars;
+----+--------------------+
| id | path               |
|----+--------------------|
| 1  | image/avatar-0.png |
| 2  | image/avatar-1.png |
| 3  | image/avatar-2.png |
| 4  | image/avatar-3.png |
| 5  | image/avatar-4.png |
+----+--------------------+
SELECT 5

 ~/devel/myplayground/  develop !3 ?1  aws s3 ls legacy-s3/image/    
2022-07-13 15:23:13       1676 avatar-0.png
2022-07-13 15:23:13       1676 avatar-1.png
2022-07-13 15:23:13       1676 avatar-2.png
2022-07-13 15:23:13       1676 avatar-3.png
2022-07-13 15:23:13       1676 avatar-4.png


Added more dummy data to simulate the new "modern" path (avatar/*):

postgres@127:proddatabase> INSERT INTO avatars (path) VALUES ('avatar/avatar-32426.png')
INSERT 0 1
Time: 0.005s
postgres@127:proddatabase> select * from avatars;
+----+-------------------------+
| id | path                    |
|----+-------------------------|
| 1  | image/avatar-0.png      |
| 2  | image/avatar-1.png      |
| 3  | image/avatar-2.png      |
| 4  | image/avatar-3.png      |
| 5  | image/avatar-4.png      |
| 6  | avatar/avatar-32426.png |
```

## Demo

Checking avatar table current state:
```
postgres@127:proddatabase> select * from avatars;
+----+-------------------------+
| id | path                    |
|----+-------------------------|
| 1  | avatar/avatar-0.png     |
| 2  | image/avatar-1.png      |
| 3  | image/avatar-2.png      |
| 4  | image/avatar-3.png      |
| 5  | image/avatar-4.png      |
| 6  | avatar/avatar-32426.png |
+----+-------------------------+
SELECT 7
Time: 0.008s
```
Executing migrate.py:

```
 ~/devel/myplayground/  develop !2  python migrate.py --dbconn postgres://postgres:<password>@127.0.0.1/proddatabase --old_bucket legacy-s3 --modern_bucket production-s3 --delete_old_images True
2022-07-14 11:44:58,210 - INFO - Legacy images found in DB: ['image/avatar-0.png', 'image/avatar-1.png', 'image/avatar-2.png', 'image/avatar-3.png', 'image/avatar-4.png']
2022-07-14 11:44:58,244 - INFO - Found credentials in environment variables.
2022-07-14 11:44:58,702 - INFO - Image image/avatar-0.png found in legacy bucket legacy-s3
2022-07-14 11:44:58,702 - INFO - Migrating image/avatar-0.png to production-s3
2022-07-14 11:44:59,236 - INFO - Updating path for image/avatar-0.png in database
2022-07-14 11:44:59,264 - INFO - Deleting image/avatar-0.png from legacy-s3
2022-07-14 11:44:59,327 - INFO - Image image/avatar-1.png found in legacy bucket legacy-s3
2022-07-14 11:44:59,327 - INFO - Migrating image/avatar-1.png to production-s3
2022-07-14 11:44:59,928 - INFO - Updating path for image/avatar-1.png in database
2022-07-14 11:44:59,957 - INFO - Deleting image/avatar-1.png from legacy-s3
2022-07-14 11:45:00,020 - INFO - Image image/avatar-2.png found in legacy bucket legacy-s3
2022-07-14 11:45:00,020 - INFO - Migrating image/avatar-2.png to production-s3
2022-07-14 11:45:00,549 - INFO - Updating path for image/avatar-2.png in database
2022-07-14 11:45:00,576 - INFO - Deleting image/avatar-2.png from legacy-s3
2022-07-14 11:45:00,638 - INFO - Image image/avatar-3.png found in legacy bucket legacy-s3
2022-07-14 11:45:00,638 - INFO - Migrating image/avatar-3.png to production-s3
2022-07-14 11:45:01,110 - INFO - Updating path for image/avatar-3.png in database
2022-07-14 11:45:01,141 - INFO - Deleting image/avatar-3.png from legacy-s3
2022-07-14 11:45:01,202 - INFO - Image image/avatar-4.png found in legacy bucket legacy-s3
2022-07-14 11:45:01,202 - INFO - Migrating image/avatar-4.png to production-s3
2022-07-14 11:45:01,739 - INFO - Updating path for image/avatar-4.png in database
2022-07-14 11:45:01,765 - INFO - Deleting image/avatar-4.png from legacy-s3

and we can see that avatars table path column has now new correct path for specific rows:

postgres@127:proddatabase>
Time: 0.000s
postgres@127:proddatabase> select * from avatars;
+----+-------------------------+
| id | path                    |
|----+-------------------------|
| 1  | avatar/avatar-0.png     |
| 2  | avatar/avatar-1.png     |
| 3  | avatar/avatar-2.png     |
| 4  | avatar/avatar-3.png     |
| 5  | avatar/avatar-4.png     |
| 6  | avatar/avatar-32426.png |
+----+-------------------------+


Verify with AWS Cli:


  ~/devel/myplayground/  develop !3  aws s3 ls legacy-s3/image/
  ~/devel/myplayground/  develop !3  

  ~/devel/myplayground/  develop !3  aws s3 ls production-s3/avatar/
2022-07-14 11:45:00       1676 avatar-0.png
2022-07-14 11:45:01       1676 avatar-1.png
2022-07-14 11:45:01       1676 avatar-2.png
2022-07-14 11:45:02       1676 avatar-3.png
2022-07-14 11:45:02       1676 avatar-4.png  



Executing migrate.py again:

  ~/devel/myplayground/  develop !2  python migrate.py --dbconn postgres://postgres:<pw>@127.0.0.1/proddatabase 
2022-07-13 23:36:26,157 - INFO - No rows with legacy image/ path found in database


To keep the old files in the legacy S3 bucket remove "--delete_old_images True" flag (or set to False):

python migrate.py --dbconn postgres://postgres:<password>@127.0.0.1/proddatabase --old_bucket legacy-s3 --modern_bucket production-s3                          
2022-07-14 12:11:46,693 - INFO - Legacy images found in DB: ['image/avatar-0.png', 'image/avatar-1.png', 'image/avatar-2.png', 'image/avatar-3.png', 'image/avatar-4.png']
2022-07-14 12:11:46,718 - INFO - Found credentials in environment variables.
2022-07-14 12:11:46,776 - INFO - Legacy images found in DB: ['image/avatar-0.png', 'image/avatar-1.png', 'image/avatar-2.png', 'image/avatar-3.png', 'image/avatar-4.png']
2022-07-14 12:11:47,086 - INFO - Image image/avatar-0.png found in legacy bucket legacy-s3
2022-07-14 12:11:47,086 - INFO - Migrating image/avatar-0.png to production-s3
2022-07-14 12:11:47,574 - INFO - Updating path for image/avatar-0.png in database
2022-07-14 12:11:47,629 - INFO - Not deleting image/avatar-0.png from legacy-s3
2022-07-14 12:11:47,629 - INFO - Image image/avatar-1.png found in legacy bucket legacy-s3
2022-07-14 12:11:47,629 - INFO - Migrating image/avatar-1.png to production-s3
2022-07-14 12:11:48,131 - INFO - Updating path for image/avatar-1.png in database
2022-07-14 12:11:48,158 - INFO - Not deleting image/avatar-1.png from legacy-s3
2022-07-14 12:11:48,159 - INFO - Image image/avatar-2.png found in legacy bucket legacy-s3
2022-07-14 12:11:48,159 - INFO - Migrating image/avatar-2.png to production-s3
2022-07-14 12:11:48,614 - INFO - Updating path for image/avatar-2.png in database
2022-07-14 12:11:48,638 - INFO - Not deleting image/avatar-2.png from legacy-s3
2022-07-14 12:11:48,638 - INFO - Image image/avatar-3.png found in legacy bucket legacy-s3
2022-07-14 12:11:48,638 - INFO - Migrating image/avatar-3.png to production-s3
2022-07-14 12:11:49,137 - INFO - Updating path for image/avatar-3.png in database
2022-07-14 12:11:49,162 - INFO - Not deleting image/avatar-3.png from legacy-s3
2022-07-14 12:11:49,162 - INFO - Image image/avatar-4.png found in legacy bucket legacy-s3
2022-07-14 12:11:49,162 - INFO - Migrating image/avatar-4.png to production-s3
2022-07-14 12:11:49,626 - INFO - Updating path for image/avatar-4.png in database
2022-07-14 12:11:49,649 - INFO - Not deleting image/avatar-4.png from legacy-s3

```

# Notes / Improvements


We could improve the code to use multiprocessing in Python (multiprocessing library) to run multiple tasks in the background for better performance.

We could implement caching to not overload our database with multiple requests by implementing Redis cache for example.

Some queuing system can be implemented as well for better performance / availability. I.e Kafka Producers / Consumers.

