#!/bin/bash

# Start the Docker containers and build them as necessary
docker-compose up -d --build

# Wait for the server to start
echo "Waiting for the server to start..."
sleep 3

# Open the default web browser at http://127.0.0.1:5000/
xdg-open http://127.0.0.1:5000/
