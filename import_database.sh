#!/bin/bash

echo "📦 Importing Navis database into Docker..."

# Make sure containers are running
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 5

# Import the dump
cat navis_database_backup.sql | docker-compose exec -T postgres psql -U navis -d navis

echo "✅ Database imported successfully!"
