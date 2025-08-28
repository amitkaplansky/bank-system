from aiokafka import AIOKafkaProducer
import json
import logging
import os
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)

class KafkaProducer:
    """Kafka producer for sending transaction events"""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    
    async def start(self):
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: str(x).encode('utf-8') if x else None,
                acks='all',  # Wait for all replicas to acknowledge
                enable_idempotence=True,  # Prevent duplicate messages
                retry_backoff_ms=1000,
                request_timeout_ms=30000
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.warning(f"Failed to start Kafka producer: {e}")
            logger.warning("API will run without Kafka integration")
            self.producer = None
            # Don't raise exception - allow API to start without Kafka
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def send_transaction_event(self, topic: str, transaction_data: dict, transaction_id: int):
        """Send transaction event to Kafka topic"""
        try:
            if not self.producer:
                logger.warning("Kafka producer not started, skipping message")
                return
            
            # Send message with transaction_id as key for partitioning
            await self.producer.send_and_wait(
                topic=topic,
                key=transaction_id,
                value=transaction_data
            )
            
            logger.info(f"Sent transaction event to {topic}: transaction_id={transaction_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
    
    async def health_check(self) -> bool:
        """Check if Kafka producer is healthy"""
        try:
            if not self.producer:
                return False
            
            metadata = await self.producer.client.fetch_metadata()
            return len(metadata.topics) >= 0
            
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False

# Global Kafka producer instance
kafka_producer = KafkaProducer()

class KafkaTopics:
    PENDING_TRANSACTIONS = "pendingTransactions"
    COMPLETED_TRANSACTIONS = "completedTransactions"
    FAILED_TRANSACTIONS = "failedTransactions"