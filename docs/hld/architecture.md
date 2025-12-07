***TOC:***

- [Ansari WhatsApp Architecture Overview](#ansari-whatsapp-architecture-overview)
  - [System Architecture](#system-architecture)
  - [Deployment Architecture](#deployment-architecture)
  - [Component Overview](#component-overview)
    - [ansari-whatsapp](#ansari-whatsapp)
    - [ansari-backend](#ansari-backend)
  - [Message Flow](#message-flow)
  - [API Endpoints](#api-endpoints)
    - [ansari-whatsapp Endpoints](#ansari-whatsapp-endpoints)
    - [ansari-backend WhatsApp API Endpoints](#ansari-backend-whatsapp-api-endpoints)
  - [Data Model](#data-model)


# Ansari WhatsApp Architecture Overview

This document provides a high-level design overview of the Ansari WhatsApp service and its interaction with the main Ansari backend.

## System Architecture

The Ansari ecosystem has been divided into two main components:

1. **ansari-backend**: The core service that contains the LLM (Large Language Model) integration, business logic, and database operations
2. **ansari-whatsapp**: A dedicated service for handling WhatsApp communication that acts as a client to the ansari-backend

This separation provides several benefits:
- Improved maintainability by isolating WhatsApp-specific logic
- Better scalability as each service can be scaled independently
- Cleaner codebase with clear separation of concerns
- Simplified deployment and updates

```mermaid
graph TD
    subgraph "WhatsApp Business Platform"
        WA[WhatsApp Business API] --> Webhook
    end

    subgraph "ansari-whatsapp"
        Webhook[Webhook Endpoints] --> CM[Conversation Manager]
        CM --> SP[Service Provider]
        SP --> AC[Ansari Client]
        SP --> MS[Meta API Service]
        CM --> WMF[Message Formatter]
    end

    subgraph "ansari-backend"
        API[WhatsApp Router<br/>6 API Endpoints] --> Agent[Ansari Agent]
        Agent --> DB[Database]
    end

    AC -- REST API --> API
    MS -- Graph API --> WA
    DB -- Data --> API
```

## Deployment Architecture

The two services are deployed independently but work together as shown in the following diagram:

```mermaid
graph TD
    subgraph "Internet"
        WU[WhatsApp Users] --- WA
        WA[WhatsApp Business API]
    end
    
    subgraph "Ansari Infrastructure"
        subgraph "ansari-whatsapp Container"
            WS[WhatsApp Service]
        end
        
        subgraph "ansari-backend Container"
            BE[Backend Service]
            DB[(MongoDB)]
        end
        
        WS --- BE
        BE --- DB
    end
    
    WA --- WS
```

## Component Overview

### ansari-whatsapp

The WhatsApp service is built as a FastAPI application with the following key components:

- **app/main.py**: Entry point for the FastAPI application that handles webhook events from the WhatsApp Business API
- **services/whatsapp_conversation_manager.py**: Orchestrates user registration, thread management, and message processing workflows
- **presenters/whatsapp_message_formatter.py**: Formats AI responses for WhatsApp (4K limit, markdown conversion, RTL support)
- **services/ansari_client_{base,real,mock}.py**: Client library that communicates with the ansari-backend API endpoints (with mock support for testing)
- **services/meta_api_service_{base,real,mock}.py**: WhatsApp Business API client for sending messages and typing indicators
- **services/service_provider.py**: Dependency injection container for service selection (real vs mock)
- **utils/config.py**: Configuration management using Pydantic and environment variables
- **utils/whatsapp_webhook_parser.py**: Extracts message details from webhook JSON payloads
- **utils/whatsapp_message_splitter.py**: Splits long messages at WhatsApp's 4K character boundaries
- **utils/language_utils.py**: Utilities for language detection and text direction determination (RTL support)
- **utils/app_logger.py**: Enhanced logging functionality with sensitive data masking

### ansari-backend

The backend service exposes dedicated API endpoints for the WhatsApp service:

- **routers/whatsapp_router.py**: Provides 6 API endpoints specifically for WhatsApp service integration
- **Database Integration**: Handles storage and retrieval of WhatsApp messages, threads, and user data
- **Ansari Agent**: Processes messages using LLM and generates streaming responses

## Message Flow

The following diagram illustrates the flow of a user message from WhatsApp to the backend and back:

```mermaid
sequenceDiagram
    participant User as WhatsApp User
    participant WhatsApp as WhatsApp Business API
    participant WA_Service as ansari-whatsapp
    participant Backend as ansari-backend

    User->>WhatsApp: Sends a message
    WhatsApp->>WA_Service: POST /whatsapp/v2 (webhook)
    Note over WA_Service: Parse webhook JSON<br/>(whatsapp_webhook_parser)

    alt New User
        WA_Service->>Backend: POST /whatsapp/v2/users/register
        Backend->>WA_Service: User registration result
    end

    alt New Thread or Expired Thread (>24h)
        WA_Service->>Backend: POST /whatsapp/v2/threads
        Backend->>WA_Service: Thread creation result
    end

    WA_Service->>WhatsApp: Send typing indicator "..."
    WA_Service->>Backend: POST /whatsapp/v2/messages/process

    Backend->>Backend: Run message through Ansari Agent
    Backend->>WA_Service: Streaming response

    Note over WA_Service: Format & split at 4K<br/>(whatsapp_message_formatter)
    WA_Service->>WhatsApp: Send formatted messages
    WhatsApp->>User: Deliver response
```

## API Endpoints

### ansari-whatsapp Endpoints

- **GET /whatsapp/v2**: WhatsApp webhook verification endpoint
- **POST /whatsapp/v2**: Main webhook endpoint for receiving WhatsApp messages

### ansari-backend WhatsApp API Endpoints

- **POST /whatsapp/v2/users/register**: Register a new WhatsApp user
- **GET /whatsapp/v2/users/exists**: Check if a WhatsApp user exists
- **POST /whatsapp/v2/threads**: Create a new message thread
- **GET /whatsapp/v2/threads/last**: Get information about the last active thread
- **GET /whatsapp/v2/threads/{thread_id}/history**: Get thread message history
- **POST /whatsapp/v2/messages/process**: Process a message and generate a streaming response

## Data Model

```mermaid
erDiagram
    USERS ||--o{ THREADS : has
    THREADS ||--o{ MESSAGES : contains
    
    USERS {
        string user_id
        string phone_num
        string preferred_language
        datetime created_at
        datetime updated_at
    }
    
    THREADS {
        string thread_id
        string user_id
        string name
        datetime created_at
        datetime updated_at
    }
    
    MESSAGES {
        string message_id
        string thread_id
        string role
        string content
        datetime created_at
    }
```