**As a** customer service representative  
**I need** the ability to read, update, delete, and list account records through the Account REST API  
**So that** I can manage customer account information accurately throughout its lifecycle

### Details and Assumptions

- The service already supports creating accounts
- The remaining REST operations to implement are READ, UPDATE, DELETE, and LIST
- Account records contain: id, name, email, address, phone_number, and date_joined
- All endpoints should accept and return JSON where appropriate
- The service should return proper HTTP status codes for success and error conditions
- Test coverage must remain at or above 95%

### Acceptance Criteria

```gherkin
Given the Account service is running
When a client requests the list of accounts
Then the service returns a 200 OK response and a JSON array of accounts

Given an account exists
When a client requests that account by id
Then the service returns a 200 OK response and the account data as JSON

Given an account exists
When a client sends updated account data to that account's endpoint
Then the service updates the account and returns a 200 OK response with the updated account

Given an account exists
When a client sends a delete request for that account
Then the service deletes the account and returns a 204 NO CONTENT response

Given an account does not exist
When a client requests, updates, or deletes that account by id
Then the service returns a 404 NOT FOUND response

Given a client sends invalid account data
When the service attempts to process the request
Then the service returns a 400 BAD REQUEST response
```
