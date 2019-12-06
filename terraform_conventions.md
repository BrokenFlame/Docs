# Terraform Conventions

## Introduction

Below are some simple terraform conventions to follow when writing terraform for &lt;&lt;Company name&gt;&gt;. 

## Basic Terraform Structure

When creating a basic terraform structure. At a minimum the following files are expected as part of your main Terraform folder:
- provider.tf (Contains the list of terraform providers, and the location of the state file)
- main.tf
- variables.tf
- output.tf 

Optionally a "templates" directory maybe included for scripts and declarative configuration files. 

Should the main.tf become overwhelmingly large, the main.tf file maybe split into multiples file.  However, each file should have a clear purpose, reflected in both its name and content.

## Module Structure
Each module must contain the following files: 
- main.tf
- variables.tf
- outputs.tf

Optional files include: 
- datasources.tf

If required a "templates" folder may be added to the module.  This is often useful for storage of policy documents and scripts. 

## Module versioning
Modules should be version on check-in, by tagging the branch appropriately.  It is customary to use a simple versioning schema of v&lt;Major&gt;.&lt;Minor&gt;, i.e v1.1.  <em> For ease of use, Terraform modules must be checked-into their own repositories along with a readme.me informing users how the module functions (you may use terraform-docs to help you generate the documentation). </em>

## Basic Terraform Usage
All Terraform executes against the corporate Cloud accounts (AWS/Azure), must use appropriate cloud storage to ensure that the Terraform State file (tfstate) is 

Terraform can be executed either locally or as part of the CI/CD pipeline.  However, it is recommended that the Terraform is executed as part of the CI/CD Pipeline. 
