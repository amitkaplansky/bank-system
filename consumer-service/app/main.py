import asyncio
import logging
import signal
import sys
from typing import Set
from .config import settings
from .kafka_consumer import TransactionConsumer
from .database import db_manager

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConsumerService:
    """Main consumer service application"""
    
    def __init__(self):
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
        self.consumer = TransactionConsumer()
    
    async def start(self):
        """Start the consumer service"""
        logger.info("Starting Banking Consumer Service...")
        
        try:
            # Initialize database connection
            await db_manager.health_check()
            logger.info("Database connection verified")
            
            # Start consumer
            await self.consumer.start()
            self.running = True
            
            # Start consuming messages
            consume_task = asyncio.create_task(self.consumer.consume_messages())
            self.tasks.add(consume_task)
            
            logger.info("Consumer service started successfully")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Failed to start consumer service: {e}")
            raise
    
    async def stop(self):
        """Stop the consumer service"""
        logger.info("Stopping Banking Consumer Service...")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Stop consumer
        await self.consumer.stop()
        
        # Close database connections
        await db_manager.close()
        
        logger.info("Consumer service stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    service = ConsumerService()
    service.setup_signal_handlers()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Consumer service failed: {e}")
        sys.exit(1)
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())