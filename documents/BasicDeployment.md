# Basic Deployment Guide

This guide explains how to use the basic infrastructure deployment option instead of the default Azure Verified Modules (AVM) deployment.

## When to Use Basic Deployment

- You want simpler, standalone Bicep files without modular dependencies
- You're learning Azure infrastructure and want easier-to-read code
- You need to make quick customizations without understanding AVM patterns

## Setup Steps

Follow these steps to switch to the basic deployment:

1. In the root directory, rename `azure.yaml` to `azure_avm.yaml`
2. Rename `azure_basic.yaml` to `azure.yaml`
3. Navigate to the `infra_basic` folder
4. Rename `main.bicep` to `main_avm.bicep`
5. Rename `main_basic.bicep` to `main.bicep`
6. Run `azd up` to deploy

## Important Notes

- The basic deployment lacks some production-ready patterns included in the AVM deployment
- For production workloads, the default AVM deployment is recommended
- Both deployments create the same Azure resources, just using different Bicep patterns
