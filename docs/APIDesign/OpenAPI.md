# ObserveLens Web API List

```
/api/v1
├── auth
├── conversations
├── messages
├── runs
├── incidents
├── inspections
├── entities
├── knowledge
├── models
├── notifications
└── system
```

---

## 1. Auth

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
POST   /api/v1/auth/refresh
```

## 2. Conversations

```
GET    /api/v1/conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{conversation_id}
PATCH  /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}
```

## 3. Messages

```
GET    /api/v1/conversations/{conversation_id}/messages
POST   /api/v1/conversations/{conversation_id}/messages
GET    /api/v1/messages/{message_id}
DELETE /api/v1/messages/{message_id}
```

## 4. Runs

```
GET    /api/v1/runs/{run_id}
GET    /api/v1/runs/{run_id}/steps
GET    /api/v1/runs/{run_id}/events
GET    /api/v1/runs/{run_id}/artifacts
GET    /api/v1/runs/{run_id}/rca
POST   /api/v1/runs/{run_id}/cancel
```

## 5. Observations

```
GET    /api/v1/observations/{observation_id}
```

## 6. Incidents

```
GET    /api/v1/incidents
POST   /api/v1/incidents
GET    /api/v1/incidents/{incident_id}
PATCH  /api/v1/incidents/{incident_id}
DELETE /api/v1/incidents/{incident_id}

POST   /api/v1/incidents/{incident_id}/archive
POST   /api/v1/incidents/{incident_id}/open-conversation

GET    /api/v1/incidents/severities
GET    /api/v1/incidents/statuses
GET    /api/v1/incidents/sources
```

## 7. Incident Integrations

```
GET    /api/v1/incidents/integrations
POST   /api/v1/incidents/integrations
GET    /api/v1/incidents/integrations/{integration_id}
PATCH  /api/v1/incidents/integrations/{integration_id}
DELETE /api/v1/incidents/integrations/{integration_id}
```

## 8. Inspections

```
GET    /api/v1/inspections
POST   /api/v1/inspections
GET    /api/v1/inspections/{inspection_id}
PATCH  /api/v1/inspections/{inspection_id}
DELETE /api/v1/inspections/{inspection_id}

POST   /api/v1/inspections/{inspection_id}/execute
POST   /api/v1/inspections/{inspection_id}/enable
POST   /api/v1/inspections/{inspection_id}/disable

GET    /api/v1/inspections/statuses
GET    /api/v1/inspections/schedules
```

## 9. Entities

```
GET /api/v1/entities/types

GET    /api/v1/entities/search
GET    /api/v1/entities/{entity_id}
GET    /api/v1/entities/{entity_id}/topology
GET    /api/v1/entities/{entity_id}/relations
POST   /api/v1/entities/{entity_id}/open-conversation
```

## 10. Knowledge

```
GET    /api/v1/knowledge/files
POST   /api/v1/knowledge/files
GET    /api/v1/knowledge/files/{file_id}
DELETE /api/v1/knowledge/files/{file_id}

POST   /api/v1/knowledge/files/{file_id}/reindex
GET    /api/v1/knowledge/files/{file_id}/status

GET    /api/v1/knowledge/file-types
GET    /api/v1/knowledge/index-statuses
```

## 11. Models

```
GET    /api/v1/models
POST   /api/v1/models
GET    /api/v1/models/{model_id}
PATCH  /api/v1/models/{model_id}
DELETE /api/v1/models/{model_id}

POST   /api/v1/models/{model_id}/test
POST   /api/v1/models/{model_id}/set-default

GET    /api/v1/models/providers
GET    /api/v1/models/statuses
```

## 12. Notifications

```
GET    /api/v1/notifications
POST   /api/v1/notifications
GET    /api/v1/notifications/{notification_id}
PATCH  /api/v1/notifications/{notification_id}
DELETE /api/v1/notifications/{notification_id}

POST   /api/v1/notifications/{notification_id}/test

GET    /api/v1/notifications/types
GET    /api/v1/notifications/statuses
```

## 13. System

```
GET /api/v1/system/info
GET /api/v1/system/version
GET /api/v1/system/health
```
