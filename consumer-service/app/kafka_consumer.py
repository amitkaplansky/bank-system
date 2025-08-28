from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json
import logging
import asyncio
from typing import Optional
from .config import settings
from .processors.transaction_processor import TransactionProcessor

logger = logging.getLogger(__name__)

class TransactionConsumer:
    """Kafka consumer for processing transaction events"""
    
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.processor = TransactionProcessor()
        self.running = False
    
    async def start(self):
        """Start the Kafka consumer and producer"""
        try:
            # Initialize consumer
            self.consumer = AIOKafkaConsumer(
                settings.COMPLETED_TRANSACTIONS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Manual commit for better control
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=settings.CONSUMER_TIMEOUT_MS,
                max_poll_records=settings.CONSUMER_BATCH_SIZE
            )
            
            # Initialize producer for failed/retry messages
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: str(x).encode('utf-8') if x else None,
                acks='all'
            )
            
            await self.consumer.start()
            await self.producer.start()
            
            logger.info("Kafka consumer and producer started successfully")
            
        except Exception as e:
            logger.warning(f"Failed to start Kafka consumer: {e}")
            logger.warning("Consumer service will run without Kafka integration")
            
            # Clean up any partially initialized objects
            if self.consumer:
                try:
                    await self.consumer.stop()
                except:
                    pass
            if self.producer:
                try:
                    await self.producer.stop()
                except:
                    pass
            
            self.consumer = None
            self.producer = None
            # Don't raise exception - allow consumer to start without Kafka
    
    async def stop(self):
        """Stop the Kafka consumer and producer"""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
        
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def consume_messages(self):
        """Main message consumption loop"""
        if not self.consumer:
            logger.warning("Consumer not started - Kafka not available. Service will idle.")
            # Keep the service running but idle
            while self.running:
                await asyncio.sleep(5)
            return
        
        self.running = True
        logger.info("Starting message consumption...")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self._process_message(message)
                    
                    # Commit after successful processing
                    await self.consumer.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Don't commit on error - message will be reprocessed
                    
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
        finally:
            logger.info("Message consumption stopped")
    
    async def _process_message(self, message):
        """Process a single Kafka message"""
        try:
            transaction_data = message.value
            transaction_id = transaction_data.get('transaction_id')
            
            logger.info(f"Processing transaction: {transaction_id}")
            
            # Process the transaction
            success = await self.processor.process_transaction_event(transaction_data)
            
            if success:
                logger.info(f"Successfully processed transaction: {transaction_id}")
            else:
                logger.warning(f"Failed to process transaction: {transaction_id}")
                
                # Send to failed transactions topic
                await self._send_to_failed_topic(transaction_data, "Processing failed")
                
        except Exception as e:
            logger.error(f"Error in message processing: {e}")
            
            # Try to send to failed topic
            try:
                await self._send_to_failed_topic(
                    message.value, 
                    f"Processing exception: {str(e)}"
                )
            except Exception as failed_error:
                logger.error(f"Failed to send to failed topic: {failed_error}")
    
    async def _send_to_failed_topic(self, transaction_data: dict, error_message: str):
        """Send failed transaction to failed topic"""
        if not self.producer:
            logger.warning("Producer not available, cannot send to failed topic")
            return
        
        failed_event = {
            "event_type": "failed_transaction",
            "timestamp": transaction_data.get('timestamp'),
            "transaction_id": transaction_data.get('transaction_id'),
            "error_message": error_message,
            "retry_count": transaction_data.get('retry_count', 0) + 1,
            "original_event": transaction_data
        }
        
        try:
            await self.producer.send_and_wait(
                topic=settings.FAILED_TRANSACTIONS_TOPIC,
                key=transaction_data.get('transaction_id'),
                value=failed_event
            )
            logger.info(f"Sent to failed topic: {transaction_data.get('transaction_id')}")
        except Exception as e:
            logger.error(f"Failed to send to failed topic: {e}")