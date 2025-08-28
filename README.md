**UML Diagrams**: class diagrams are attached

## Failure Resilience

**When Kafka Fails**
**Result**: Banking continues working perfectly
- Money transfers complete successfully
- Customers get normal responses
- Only background processing stops (reports, notifications)
- Consumer automatically reconnects when Kafka recovers
- **No data loss**: All transaction data safely stored in database

**When Database Fails**  
**Result**: System fails safely with data integrity
- Transfer attempts fail immediately
- All changes are automatically rolled back
- Customer gets clear "transfer failed" error
- **No corruption**: Either transaction works completely or not at all
- Event processing resumes when database recovers

## System Overview

Modern banking system built with **event-driven architecture** supporting Individual, Business, and VIP customers. The system handles money transfers with full audit trails and asynchronous event processing for regulatory reporting, analytics, and notifications.

### Key Features
- **Multi-tier customers**: Individual, Business, VIP (Gold/Platinum/Diamond)
- **Event-driven processing**: Kafka-based async processing for compliance and analytics

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Run the System
```bash
# Clone and start all services
git clone <repository>
cd bank-system
docker-compose up --build

# API available at http://localhost:8000
```

### Test the API
```bash
# View customers and accounts
curl http://localhost:8000/api/v1/customers/
curl http://localhost:8000/api/v1/accounts/

**Services**:
- **FastAPI Banking API** (port 8000) - Core banking operations
- **MySQL Database** (port 3306) - Customer, account, transaction data
- **Apache Kafka** (port 9092) - Event streaming for async processing
- **Consumer Service** - Processes events for regulatory/analytics/notifications

**Sample Data**: Marvel superheroes (Tony Stark, Steve Rogers, etc.) for easy testing
