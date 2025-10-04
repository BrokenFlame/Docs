# Application Deployment Requirements

## Description
Please provide a description of the application.
1. The Application Name: 
2. A description of what the application does: 
3. A link to the source code repository:
4. A list of the third-parties that will use the application:

## Application Architecture and Specification
Please complete the following to provide key information regarding the application:

1. Is the application multithreaded?
2. How much RAM does the application utilise at startup?
3. How much RAM is the application expected to use underload?
4. What is the maximum amount of RAM the application should use?
5. Is the application a server, client or P2P application?
6. Is it expected that the application will have more than one instance running at a time?
7. Is it expected one and only one instance will run on each kubernetes nodes, as a DeamonSet?
8. Does the application need to share a key or session state with other instances of itself _(this is usually required for stateful applications)_?
9. What is the best way to scale the applications performance (Virtical or horizontal scaling)?

_Please note that the application will be terminated and restarted if it exceeds the upper RAM limited specified above._

#### Application Health
1. Does the application have a health check endpoint, and if so please state the enpoint?
2. How often should the health check endpoint be called (interval in seconds between health check calls)?
3. How many failed health check calls should initalise the termination of the application container?

### Network Connectivity 

#### Internet connected application

1. What services/urls will the service connect to?
2. If there are any inbound connections are the client addresses known? If so please provide the IP Addresses.
3. Do any of these connections inbound or outbound require mTLS encryption?

** Please note that it will be assumed that all inbound internet connectivity will be over HTTPS on port 443. To use GRPC or TCP please contact the Platform Engineering team to discuss your requirements**

#### Internal Connectivity
1. Does the application require a connection to other company applications?
2. Does the application require a connection to the Parent organisation's applications?
3. Is the application expected to accept connections from other company applications?
4. Is the application expected to accept connections from the parent organisation's applications?

##### Database connectivity
1. Does the application have a Database backend?
2. If the application has a Database backend, which database engine does it use?

**Please note that all database connections are encrypted in transport, your application must support TLS encryption for the database connections**

##### Storage
1. Does the application require file or block storage?
2. If the application requires file or block storage, how much storage will be required for the first year of operation?
3. Is there autoamatic storage usage management built into the application?
4. Is there a requirement for the storage to be persistent? 
5. Is there a requirement to share the storage between mutiple instances of the application?


## Application Configuration
The following section describes the application's configuration. Please complete it to the best of your abilities. Please do not provide secretes in this form.

### Environment Variables
Please complete the table below for the 

| No. | Key   | Exmaple Value   | Value Type | Description                |
| --- | ----- | --------------- | ---------- | -------------------------- |
| 0.  | URL   | app.company.com | sting      | The Url of the application |

### Secrets
Please list the secrets that you intend to use with the application and how the application will access said secrets:

| No. | Secret            | Secret Type                      | Description                  |
| --- | ----------------  | -------------------------------- | ---------------------------- |  
| 0.  | Database Password | Kubernetes Secret via File Mount | Custom CA Certificat for RDS |


### Mounted Files
If there are any files that need mounting to the pod. Please provide a description in the table below. An example is given in row zero.

| No. | File           | Mount Point     | Description                  |
| --- | -------------- | --------------- | ---------------------------- |  
| 0.  | CA Certificate | /etc/ssl/ca.pem | Custom CA Certificat for RDS |


## Authentication
Does the application require integration with a 3rd party authenication services via SAML or OAuth2?

## 3rd Party Services

### AWS Services
Please list all of the AWS Services that the applcation requires. Typically this will be SQS Queues, SNS Topics, and SES to send emails. Please consult the organisations Data Classification documentation to assatain the correct data classification.


| No. | Service   | Data Classification   |  Description                |
| --- | --------- | -------------------   |  -------------------------- |
| 0.  | SQS       | PII                   |  An SQS queue is required to storage a list of email reciepients to be sent by the noticiation service |

### Other 3rd Party Services
Please list any other third party services required by the application. 


<p>

---

> This should be checked into the main branch of your code repo and kept up todate to help your operation teams.
