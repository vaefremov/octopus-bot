#!/bin/bash
# Example long-running script that simulates deployment
# This script demonstrates streaming output via the bot

echo "Starting deployment process..."
sleep 1

echo "Step 1: Checking prerequisites..."
sleep 1
echo "  ✓ Git installed"
echo "  ✓ Docker installed"
echo "  ✓ Kubernetes cluster accessible"
sleep 1

echo "Step 2: Pulling latest code..."
sleep 2
echo "  ✓ Code pulled from main branch"
sleep 1

echo "Step 3: Building Docker image..."
for i in {1..5}; do
    echo "  Building layer $i/5..."
    sleep 1
done
echo "  ✓ Docker image built successfully"
sleep 1

echo "Step 4: Pushing to registry..."
sleep 2
echo "  ✓ Image pushed to registry"
sleep 1

echo "Step 5: Deploying to Kubernetes..."
sleep 2
echo "  ✓ Deployment created"
echo "  ✓ Pods are rolling out"
sleep 2

echo "Step 6: Verifying deployment..."
sleep 1
echo "  ✓ All pods are running"
echo "  ✓ Health checks passing"
sleep 1

echo "Deployment completed successfully!"
echo "New version: v1.2.3"
