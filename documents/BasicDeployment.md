# Basic Deployment Guide

This guide explains how to use the basic infrastructure deployment option instead of the default Azure Verified Modules (AVM) deployment.

## When to Use Basic Deployment

- You want simpler, standalone Bicep files without modular dependencies
- You're learning Azure infrastructure and want easier-to-read code
- You need to make quick customizations without understanding AVM patterns

## Setup Steps

Follow these steps to switch to the basic deployment:

1. Rename `azure_basic.yaml` to `azure.yaml` (this will replace the default AVM configuration)
2. Run `azd up` to deploy

> **Note:** If you want to keep the original `azure.yaml` for later use, rename it to `azure_avm.yaml` first.

## Important Notes

- The basic deployment lacks some production-ready patterns included in the AVM deployment
- For production workloads, the default AVM deployment is recommended
- Both deployments create the same Azure resources, just using different Bicep patterns
