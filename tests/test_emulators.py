import uuid
import pytest
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from azure.data.tables import TableServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import pymongo


class TestCosmosDBEmulatorMongo:
    def setup_method(self):
        try:
            # Path to the certificate file
            cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    "volumes", "cosmosdb-mongo", "data", "emulatorcert.crt")
            
            # Check if the certificate exists
            if os.path.exists(cert_path):
                print(f"Certificate file found at: {cert_path}")
            else:
                print(f"Certificate file not found at: {cert_path}")
                # Try to export it now
                import subprocess
                try:
                    print("Attempting to export certificate directly...")
                    result = subprocess.run(
                        ["docker", "exec", "linux-emulator", "curl", "--insecure", 
                        "https://localhost:8081/_explorer/emulator.pem", "-o", "/cosmos/data/emulatorcert.crt"],
                        capture_output=True, text=True
                    )
                    print(f"Certificate export result: {result.returncode}")
                    print(f"Output: {result.stdout}")
                    print(f"Error: {result.stderr}")
                    
                    # Check if it worked
                    if os.path.exists(cert_path):
                        print("Certificate successfully exported!")
                    else:
                        print("Certificate export failed.")
                except Exception as export_e:
                    print(f"Failed to export certificate: {str(export_e)}")
            
            # Use the properly formatted connection string
            connection_string = "mongodb://localhost:C2y6yDjf5%2FR%2Bob0N8A7Cgv30VRDJIWEHLM%2B4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw%2FJw%3D%3D@localhost:10255/admin?ssl=true"
            
            # Connection options with certificate
            # conn_options = {
            #     "ssl": True,
            #     "tls": True,
            #     "tlsAllowInvalidCertificates": True,  # Essential for self-signed certs
            #     "serverSelectionTimeoutMS": 30000,    # Longer timeout for initial connection
            #     "socketTimeoutMS": 30000,
            #     "connectTimeoutMS": 30000,
            #     "retryWrites": False,
            #     "directConnection": True,
            # }
            conn_options = {
                "tlsAllowInvalidCertificates": True,  # Essential for self-signed certs
                "retryWrites": False,
                "directConnection": True,
            }
            
            # Try to use the certificate file if it exists
            # if os.path.exists(cert_path):
            #     conn_options["tlsCAFile"] = cert_path
            #     print(f"Using certificate file for TLS: {cert_path}")
            #
            # print(f"Connecting to MongoDB with options: {conn_options}")
            
            # Connect to MongoDB API
            self.mongo_client = pymongo.MongoClient(connection_string, **conn_options)
            
            # Force connection with a simple command
            # Use admin command to verify the connection works
            # admin_db = self.mongo_client.admin
            # result = admin_db.command("ping")
            # print(f"Connection successful: {result}")
            
            # Create unique test database and collection
            self.db_name = f"testdb_{uuid.uuid4().hex[:8]}"
            self.collection_name = "products"
            self.mongo_db = self.mongo_client[self.db_name]
            self.mongo_collection = self.mongo_db[self.collection_name]
            
            # Insert a test document to ensure the collection is created
            self.mongo_collection.insert_one({"_id": "test_init", "value": "test"})
            
        except Exception as e:
            # Check if Cosmos DB container is actually running
            import subprocess
            try:
                # Check container status
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=linux-emulator", "--format", "{{.Status}}"],
                    capture_output=True, text=True, check=True
                )
                if result.stdout.strip():
                    container_status = result.stdout.strip()
                    print(f"Cosmos DB container status: {container_status}")
                    
                    # Check MongoDB endpoint specifically
                    result = subprocess.run(
                        ["docker", "exec", "linux-emulator", "curl", "--insecure", "-s", 
                         "https://localhost:8081/_explorer/datablade/api/emulator-info"],
                        capture_output=True, text=True
                    )
                    print(f"Emulator info: {result.stdout}")
                    
                    # Check if the MongoDB port is listening
                    result = subprocess.run(
                        ["docker", "exec", "linux-emulator", "netstat", "-tuln"],
                        capture_output=True, text=True
                    )
                    print(f"Network ports listening: {result.stdout}")
                else:
                    print("Cosmos DB container not running! Start it with 'docker-compose up -d'")
            except Exception as docker_e:
                print(f"Failed to check Docker container status: {str(docker_e)}")
                    
            # Try to get more diagnostics
            try:
                print("\nAttempting to get diagnostic information...")
                # Check if we can reach the emulator's web interface
                result = subprocess.run(
                    ["curl", "-k", "https://localhost:8081/_explorer/index.html"],
                    capture_output=True, text=True
                )
                print(f"Web interface reachable: {'Yes' if result.returncode == 0 else 'No'}")
            except Exception:
                pass
                
            pytest.skip(f"MongoDB connection failed: {str(e)}")

    def teardown_method(self):
        if hasattr(self, 'mongo_client'):
            try:
                # Clean up test data
                self.mongo_client.drop_database(self.db_name)
            except Exception as e:
                print(f"Error during teardown: {str(e)}")
            finally:
                self.mongo_client.close()

    def test_cosmos_mongodb_crud_operations(self):
        # Test document with unique ID
        document_id = f"prod_{uuid.uuid4().hex[:8]}"
        test_document = {
            "id": document_id,
            "name": "MongoDB Test Product",
            "description": "This is a test product in MongoDB API",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # CREATE: Insert a document
        insert_result = self.mongo_collection.insert_one(test_document)
        assert insert_result.acknowledged
        
        # READ: Retrieve the document
        found_doc = self.mongo_collection.find_one({"id": document_id})
        assert found_doc is not None
        assert found_doc["name"] == "MongoDB Test Product"
        
        # UPDATE: Modify the document
        update_result = self.mongo_collection.update_one(
            {"id": document_id},
            {"$set": {"name": "Updated Product Name"}}
        )
        assert update_result.modified_count == 1
        
        # Verify the update
        updated_doc = self.mongo_collection.find_one({"id": document_id})
        assert updated_doc["name"] == "Updated Product Name"
        
        # DELETE: Remove the document
        delete_result = self.mongo_collection.delete_one({"id": document_id})
        assert delete_result.deleted_count == 1
        
        # Verify the deletion
        assert self.mongo_collection.find_one({"id": document_id}) is None


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