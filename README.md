# Azure Emulators Docker Environment

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-v3.8-brightgreen)
![Last Updated](https://img.shields.io/badge/Last_Updated-April_2025-lightgrey)

> 🚀 A complete Docker-based local environment for Azure development, including Cosmos DB Emulator (with multiple APIs: SQL, MongoDB, Cassandra, Gremlin, Table), Azurite (Blob/Queue/Table), and Azure Functions Runtime.

## 📋 Overview

This project provides a complete local development environment for Azure services using Docker containers. It allows you to develop and test Azure-based applications locally without requiring an Azure subscription.

### Services Included

| Service | Description | Port(s) | Status |
|---------|-------------|---------|--------|
| **Azure Cosmos DB Emulator** | Emulates Cosmos DB with multiple APIs (SQL, MongoDB, Cassandra, Gremlin, Table) | 8081, 10255 | ✅ Tested (MongoDB) |
| **Azurite** | Emulates Azure Storage (Blob, Queue, Table) | 10000-10002 | ✅ Tested |
| **Azure Service Bus Emulator** | Local emulator for Azure Service Bus messaging | 9354, 5672 | 🔄 To be tested |
| **Azure Functions Core Tools** | Local environment for Azure Functions | 7071 | 🔄 To be tested |

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- At least 4GB of available RAM (Cosmos DB Emulator requires 3GB)
- Python 3.8+ for running tests
- [Poetry](https://python-poetry.org/docs/#installation) (version 2.0.0+) for dependency management

### Poetry Configuration

Configure Poetry to create the virtual environment in your project directory using Python 3.8:

```bash
# Configure Poetry to create virtual environments in the project directory
poetry config virtualenvs.in-project true

# Specify Python 3.12 for the virtual environment
poetry env use python3.12

# Install dependencies (without the root package)
poetry install --no-root

# Activate the virtual environment (for Poetry 2.0.0+)
poetry env activate
# or
source .venv/bin/activate
```

### Quick Start

```bash
# Clone this repository
git clone https://github.com/yourusername/azure-emulators-docker.git
cd azure-emulators-docker

# Start all services 
docker-compose up -d

# Start specific services only
docker-compose up -d azurite servicebus
```

### Running Tests

```bash
# Run tests using Poetry
poetry run pytest

# Run specific tests
poetry run pytest tests/test_emulators.py
```

## 🔌 Connection Information

> **⚠️ Security Note:** All connection strings and keys shown below are for local development only. They are either publicly known development keys or randomly generated examples. Never use these in production environments.

### Azure Cosmos DB Emulator

- **Portal URL:** https://localhost:8081/_explorer/index.html
- **Connection String:** `mongodb://localhost:10255`
- **Primary Key:** Retrieve from the emulator portal (development use only)

### Azurite (Azure Storage)

- **Endpoints:**
  - Blob: http://localhost:10000
  - Queue: http://localhost:10001
  - Table: http://localhost:10002
- **Connection String:**
```
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;
AccountKey=RandomDevKey123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmn==;
BlobEndpoint=http://localhost:10000/devstoreaccount1;
QueueEndpoint=http://localhost:10001/devstoreaccount1;
TableEndpoint=http://localhost:10002/devstoreaccount1;
```

### Azure Service Bus Emulator

- **Connection String:** `Endpoint=sb://localhost:9354/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=RandomDevSharedKey123456789ABCDEFGHIJKLMNOP=`
- **AMQP Endpoint:** `amqp://localhost:5672`

### Azure Functions

- **URL:** http://localhost:7071
- **Functions Root:** `./functions`

## 📝 Configuration

### Docker Compose Options

The environment can be customized by modifying the `docker-compose.yml` file:

```yaml
# Example: Cosmos DB Emulator configuration
cosmosdb:
  image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
  environment:
    - AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10
    - AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true
  mem_limit: 3G
```

### Data Persistence

Data persists between container restarts via Docker volumes:

| Volume | Purpose |
|--------|---------|
| `cosmosdb_data` | Cosmos DB data files |
| `cosmosdb_cert` | Cosmos DB certificates |
| `azurite_data` | Azurite storage data |

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Memory Errors with Cosmos DB** | Increase the `mem_limit` value in docker-compose.yml |
| **Certificate Errors** | Download certificate from https://localhost:8081/_explorer/emulator.pem |
| **Port Conflicts** | Modify port mappings in docker-compose.yml: `"<new-port>:<container-port>"` |

## 📄 License & Contributing

This project is licensed under the MIT License - see the LICENSE file for details.

Contributions are welcome! Please feel free to submit a Pull Request.