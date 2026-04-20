# AVM Post Deployment Guide

> **📋 Note**: This guide is specifically for post-deployment steps after using the AVM template. For complete deployment from scratch, see the main [Deployment Guide](./DeploymentGuide.md).

---

This document provides guidance on post-deployment steps after deploying the Customer Chatbot Solution Accelerator from the [AVM (Azure Verified Modules) repository](https://github.com/Azure/bicep-registry-modules.git).

## Overview

After deploying the infrastructure using AVM, you'll need to complete the application layer setup, which includes:

- Configuring team agent configurations
- Processing and uploading sample datasets
- Setting up Azure AI Search indexes
- Configuring blob storage containers
- Setting up application authentication

## Prerequisites

Before starting the post-deployment process, ensure you have the following:

### Required Software

1. **[PowerShell](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.4)** <small>(v7.0+ recommended)</small> - Available for Windows, macOS, and Linux

2. **[Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)** <small>(v2.50+)</small> - Command-line tool for managing Azure resources

3. **[Python](https://www.python.org/downloads/)** <small>(v3.9+ recommended)</small> - Required for data processing scripts

4. **[Git](https://git-scm.com/downloads/)** - Version control system for cloning the repository

### Azure Requirements

5. **Azure Access** - One of the following roles on the subscription or resource group:

   - `Contributor`
   - `Owner`

6. **Deployed Infrastructure** - A successful Customer Chatbot deployment from the [AVM repository](https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/sa/customer-chatbot)

#### **Important Note for PowerShell Users**

If you encounter issues running PowerShell scripts due to execution policy restrictions, you can temporarily adjust the `ExecutionPolicy` by running the following command in an elevated PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This will allow the scripts to run for the current session without permanently changing your system's policy.

## Post-Deployment Steps

### Step 1: Clone the Repository

First, clone this repository to access the post-deployment scripts:

```powershell
git clone https://github.com/microsoft/customer-chatbot-solution-accelerator.git
```

```powershell
cd customer-chatbot-solution-accelerator
```

### Step 2: Run the Post-Deployment Script

The post-deployment process is automated through a PowerShell or Bash script that completes the following tasks in approximately 5-10 minutes:

### Initialize Data and Agents

**Step 1: Populate Product Catalogs and Search Indexes**

Run the data setup script to load sample product data
- **For PowerShell (Windows/Linux/macOS):**
    ```shell
    infra\scripts\data_scripts\run_upload_data_scripts.ps1 -resource_group "<your-resource-group-name>"
    ```
- **For Bash (Linux/macOS/WSL):**
     ```bash
     bash ./infra/scripts/data_scripts/run_upload_data_scripts.sh --resource-group "<your-resource-group-name>"
     ```
**If you deployed using `azd up` command:**

- **For PowerShell (Windows/Linux/macOS):**
    ```shell
    infra\scripts\data_scripts\run_upload_data_scripts.ps1
    ```
- **For Bash (Linux/macOS/WSL):**
     ```bash
     bash ./infra/scripts/data_scripts/run_upload_data_scripts.sh
     ```


This script will:
- Upload sample product catalog data to Azure Cosmos DB
- Create and configure Azure AI Search indexes
- Populate search indexes with product and policy documents

**Step 2: Create AI Foundry Agents**
Run the data setup script to load sample product data and create search indexes in Azure AI Search:

- **For PowerShell (Windows/Linux/macOS):**
    ```shell
    infra\scripts\agent_scripts\run_create_agents_scripts.ps1 -resourceGroup "<your-resource-group-name>"
    ```
- **For Bash (Linux/macOS/WSL):**
     ```bash
     bash ./infra/scripts/agent_scripts/run_create_agents_scripts.sh --resource-group "<your-resource-group-name>"
     ```
**If you deployed using `azd up` command:**
     
- **For PowerShell (Windows/Linux/macOS):**
    ```shell
    infra\scripts\agent_scripts\run_create_agents_scripts.ps1
    ```
- **For Bash (Linux/macOS/WSL):**
     ```
     bash ./infra/scripts/agent_scripts/run_create_agents_scripts.sh
     ```    


This script creates:

- Chat Agent
- Product Agent 
- Policy Agent

   > **Note**: Replace `<your-resource-group-name>` with the actual name of the resource group containing your deployed Azure resources.


### Step 3: Provide Required Information

During script execution, you'll be prompted for:

- You'll be prompted to authenticate with Azure if not already logged in
- Select the appropriate Azure subscription

#### Resource Validation

- The script will automatically detect and validate your deployed Azure resources
- Confirmation prompts will appear before making configuration changes

### Step 4: Post Deployment Script Completion

Upon successful completion, you'll see a success message.

**🎉 Congratulations!** Your post-deployment configuration is complete.

### Step 5: Set Up App Authentication (Optional)

Follow the steps in [Set Up Authentication in Azure App Service](AppAuthentication.md) to add app authentication to your web app running on Azure App Service.
