import os
import uuid
import time
import pytest
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from azure.storage.table import TableServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage


class TestCosmosDBEmulator:
    def setup_method(self):
        # CosmosDB MongoDB API connection
        url = "https://localhost:8081"
        key = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="  # Default emulator key
        self.client = CosmosClient(url, credential=key, connection_verify=False)
        
        # Create or get database
        self.db_name = f"testdb_{uuid.uuid4().hex[:8]}"
        self.database = self.client.create_database_if_not_exists(id=self.db_name)
        
        # Create or get container
        self.container_name = "test_container"
        self.container = self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )

    def teardown_method(self):
        # Clean up
        try:
            self.client.delete_database(self.db_name)
        except:
            pass

    def test_cosmos_crud_operations(self):
        # Create
        test_item = {
            'id': f'item_{uuid.uuid4().hex[:8]}',
            'name': 'Test Item',
            'description': 'This is a test item',
            'created_at': datetime.utcnow().isoformat()
        }
        created_item = self.container.create_item(test_item)
        assert created_item['id'] == test_item['id']
        
        # Read
        read_item = self.container.read_item(
            item=test_item['id'],
            partition_key=test_item['id']
        )
        assert read_item['name'] == 'Test Item'
        
        # Update
        test_item['name'] = 'Updated Test Item'
        updated_item = self.container.replace_item(
            item=test_item['id'],
            body=test_item
        )
        assert updated_item['name'] == 'Updated Test Item'
        
        # Delete
        self.container.delete_item(
            item=test_item['id'],
            partition_key=test_item['id']
        )
        
        # Verify deletion
        with pytest.raises(Exception):
            self.container.read_item(
                item=test_item['id'],
                partition_key=test_item['id']
            )


class TestAzuriteEmulator:
    def setup_method(self):
        # Connection string for Azurite
        connection_string = (
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
            "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;" 
            "BlobEndpoint=http://localhost:10000/devstoreaccount1;"
            "QueueEndpoint=http://localhost:10001/devstoreaccount1;"
            "TableEndpoint=http://localhost:10002/devstoreaccount1;"
        )
        
        # Initialize clients
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.queue_service_client = QueueServiceClient.from_connection_string(connection_string)
        self.table_service_client = TableServiceClient.from_connection_string(connection_string)
        
        # Create test containers
        self.container_name = f"testcontainer{uuid.uuid4().hex[:8]}"
        self.container_client = self.blob_service_client.create_container(self.container_name)
        
        self.queue_name = f"testqueue{uuid.uuid4().hex[:8]}"
        self.queue_client = self.queue_service_client.create_queue(self.queue_name)
        
        self.table_name = f"testtable{uuid.uuid4().hex[:8]}"
        self.table_client = self.table_service_client.create_table(table_name=self.table_name)

    def teardown_method(self):
        # Clean up
        try:
            self.blob_service_client.delete_container(self.container_name)
            self.queue_service_client.delete_queue(self.queue_name)
            self.table_service_client.delete_table(self.table_name)
        except:
            pass

    def test_blob_crud_operations(self):
        # Create blob
        blob_name = f"testblob{uuid.uuid4().hex[:8]}"
        blob_client = self.container_client.get_blob_client(blob_name)
        
        test_data = b"This is a test blob content"
        blob_client.upload_blob(test_data)
        
        # Read blob
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        assert content == test_data
        
        # Update blob
        updated_data = b"This is updated blob content"
        blob_client.upload_blob(updated_data, overwrite=True)
        
        # Verify update
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        assert content == updated_data
        
        # Delete blob
        blob_client.delete_blob()
        
        # Verify deletion
        with pytest.raises(Exception):
            blob_client.download_blob()

    def test_queue_operations(self):
        # Send message
        test_message = "Test queue message"
        self.queue_client.send_message(test_message)
        
        # Receive message
        messages = self.queue_client.receive_messages(max_messages=1)
        for message in messages:
            assert message.content == test_message
            self.queue_client.delete_message(message)

    def test_table_crud_operations(self):
        # Create entity
        entity = {
            'PartitionKey': 'test-partition',
            'RowKey': f'test-row-{uuid.uuid4().hex[:8]}',
            'TestProperty': 'TestValue'
        }
        
        self.table_client.create_entity(entity)
        
        # Read entity
        retrieved_entity = self.table_client.get_entity(
            partition_key=entity['PartitionKey'],
            row_key=entity['RowKey']
        )
        assert retrieved_entity['TestProperty'] == 'TestValue'
        
        # Update entity
        entity['TestProperty'] = 'UpdatedValue'
        self.table_client.update_entity(entity)
        
        # Verify update
        updated_entity = self.table_client.get_entity(
            partition_key=entity['PartitionKey'],
            row_key=entity['RowKey']
        )
        assert updated_entity['TestProperty'] == 'UpdatedValue'
        
        # Delete entity
        self.table_client.delete_entity(
            partition_key=entity['PartitionKey'],
            row_key=entity['RowKey']
        )
        
        # Verify deletion
        with pytest.raises(Exception):
            self.table_client.get_entity(
                partition_key=entity['PartitionKey'],
                row_key=entity['RowKey']
            )


class TestServiceBusEmulator:
    def setup_method(self):
        # Connection string for Service Bus Emulator
        self.connection_string = (
            "Endpoint=sb://localhost:9354/;SharedAccessKeyName=RootManageSharedAccessKey;"
            "SharedAccessKey=12345678901234567890123456789012"
        )
        
        # Create queue
        self.queue_name = f"testqueue{uuid.uuid4().hex[:8]}"
        self.servicebus_client = ServiceBusClient.from_connection_string(
            conn_str=self.connection_string
        )

    def teardown_method(self):
        # Close client
        if hasattr(self, 'servicebus_client'):
            self.servicebus_client.close()

    def test_servicebus_send_receive(self):
        # Create a sender and a receiver
        sender = self.servicebus_client.get_queue_sender(queue_name=self.queue_name)
        receiver = self.servicebus_client.get_queue_receiver(queue_name=self.queue_name)
        
        try:
            # Send a message
            test_message = f"Test message {uuid.uuid4()}"
            message = ServiceBusMessage(test_message)
            sender.send_messages(message)
            
            # Receive the message
            received_msgs = receiver.receive_messages(max_message_count=1, max_wait_time=5)
            for msg in received_msgs:
                assert msg.body.decode() == test_message
                receiver.complete_message(msg)
        finally:
            sender.close()
            receiver.close()


if __name__ == "__main__":
    # Create a README.md with test execution instructions
    readme_content = """
# Azure Emulator Tests

This directory contains tests for verifying the functionality of the Azure emulators in your local Docker environment.

## Prerequisites

Install the required Python packages:

```bash
pip install -r requirements.txt