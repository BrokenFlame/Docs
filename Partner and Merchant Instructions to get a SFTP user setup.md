# Instruction to Obtain Access to the company SFTP Service

## Background

SFTP, stands for Secure File Transfer Protocol.  It is a network protocol that provides a secure way to transfer files between systems over a network. It is an extension of the File Transfer Protocol (FTP) that incorporates the security features of Secure Shell (SSH).  SFTP uses encryption and authentication mechanisms to protect the confidentiality and integrity of data during transit.  Unlike FTP, SFTP establishes a secure connection between the client and the server, ensuring that sensitive information remains private and safe from unauthorized access.  

## Introduction

The company provides an SFTP service for merchants and partners to transfer data securly to and from the company.  The company's SFTP service is built on top of AWS File Transfer service, ensuring that the service is highly avilalbe, and secure. 

To gain access to the company's SFTP service, you are required to contact the company providing the following information:

1. Your company or organisation name.
2. The reason or purpose to access the SFTP service.
3. The fullname of all of the users who you wish to access the SFTP service.
4. If any automated services will be used to access the SFTP service.
5. The public SSH Keys assoicated with the private SSH keys for each user or service account to is to access the SFTP site.

If you have a public SSH key already, you may simply send the public key to your company contact, along with the details above.  Your account will then be configured and you will be able to access the SFTP at sftp.<company_name>.com using your username and private ssh key. It is recommended that you use an SFTP client such as CyberDuck, Filezilla, or CuteFTP, however more advance command line alternatives are avilable. 



## Instructions

1. Open a terminal (*command prompt on Windows 11*) on your chosen computer. 

2. Set the working directory to the ssh folder:

**Linux and MacOS**
```sh
cd  ~/.ssh
```

**Windows**
```cmd
IF NOT EXIST %HOMEDRIVE%%HOMEPATH%/.ssh ( MKDIR %HOMEDRIVE%%HOMEPATH%/.ssh )
cd %HOMEDRIVE%%HOMEPATH%/.ssh
```



3. To create a new SSH Keypair on Windows 11, MacOS or Linux you may use the following command in a terminal windows, remembering to replace **myemail@address.here** with the email address of the user or service account.  If you wish to add a passphrase to the SSH Key, please add the passphrase between the double quotation marks at the end of the command.

```sh
ssh-keygen -t rsa -b 2048 -C myemail@ddress.here -f <company-name>-sftp -q -N ""
```

4. Now navigate to the location where the ssh keys have been stored.

**MacOS**
```sh
open ~/.ssh
```

**Linux terminal**
```sh 
ls ~/.ssh
```

**Windows**
```cmd
explorer %HOMEDRIVE%%HOMEPATH%/.ssh
```

On Windows 11 and MacOS a folder with the SSH keys should now appear.  Find the file named  **"dekopay-sftp.pub"**, and send this to your Dekopay representitive via email along with the details found in the introduction.

On Linux, you will simply see a list of files, ensure that the file **"dekopay-sftp.pub"** is present and email this file to your Deko representative along with the details listed in the introduction.
