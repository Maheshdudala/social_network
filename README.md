# Social Network Application

This project is a Django-based social network application with several user management features,
including friend requests, 
blocking/unblocking users, and rate limiting. It includes caching using Redis, database management with PostgreSQL, 
and security implementations like JWT for authentication.

# Features

### Friend Request Management:
* Send, accept, and reject friend requests.
* Users can send a maximum of 3 friend requests per minute (rate limiting to prevent spam).
* If a user rejects a friend request, the sender cannot resend it for 24 hours (configurable).
* Users can block/unblock others, preventing friend requests and profile views.

### **Friends List:**

* View a list of accepted friends.
* Pending requests can be listed.
* Optimized queries for handling large friend lists.
* Implement caching for frequently queried data.

### User Functionalities:

**User Search:** Search users by name or email.

### User Activity & Notifications:

* Log user activities like friend requests sent or accepted.
* Send notifications when a profile view occurs or when a friend request is sent or accepted.

### Data Privacy & Security:

* **Data Encryption:** Sensitive data like passwords are encrypted using Django's cryptography tools.
* JWT Tokens: JSON Web Tokens are used for secure user authentication.
* **Rate Limiting:** Prevents brute-force attacks on login and spamming of friend requests.
* **Role-Based Access Control:** Assign different roles to users with varying permissions (e.g., admin, regular user).

### Performance Optimization

* **Redis Caching:** Redis is used to cache frequently accessed data like sessions and friend lists to reduce database load.
* **Optimized Queries:** Django’s select_related and prefetch_related methods are used to minimize database queries, 
 especially when fetching related data such as friend lists.

## Installation Guide

### Prerequisites

* **Install Docker:** Ensure Docker is installed on your system.

* **Git**

### Project Setup

### 1.Clone the repository:

`git clone https://github.com/Maheshdudala/social_network.git`

`cd social_network`

### 2.Update environment variables:
Modify your docker-compose.yml files with your PostgreSQL  credentials.

### 3.Build and start Docker containers:

`docker-compose up --build`

### 4.Run migrations:

`docker-compose exec web python manage.py migrate`

### 5.Create a superuser (admin account):

`docker-compose exec web python manage.py createsuperuser`

### 6.Access the application:

Open your browser and go to http://localhost:8000/register/

## Services

* **Web:** Django app served with Gunicorn.
* 
* **Database:** PostgreSQL container for storing user data and friend relationships.
* 
* **Redis:** Redis container for caching.

## API Documentation

### 1.Authentication

####  User Registration
**Register:** **POST**   http://localhost:8000/register/

**Body Parameters:**

                {
                    "name":"test1",
                  "email": "test1@gmail.com",
                  "password": "user1234"
                }

#### Response:

* **201 Created:** User successfully registered.
* **400 Bad Request:** Missing or invalid fields.

#### User Login
**Login:** **POST**   http://localhost:8000/login/

**Body Parameters:**

                {
                  "email": "test1@gmail.com",
                  "password": "user1234"
                }
#### Response:

* 201 Created: User logged in successfully.
* 400 Bad Request: Missing or invalid fields.



### 2.User Search

**User Search:** **GET**   http://localhost:8000/search/?q=pharse

#### Response:

* 200 ok: User will get all users who is registered.

### 3.ProfileUpdate
**ProfileUpdate:** **PUT**   http://localhost:8000/profile/update/

**Body Parameters:**

                {
                  "email": "test1@gmail.com",
                  "password": "user1234"
                }
#### Response:

* 200 ok : User description gets updated.




### 4.Friend Request Management


**Sending Request:** **POST**   http://localhost:8000/friend-request/

**Body Parameters:**

                   {
                    "user_id": 2
                    }
#### Response:

* 200 ok: Friend request sent succesfully.
* 400 Bad Request: Missing or invalid fields.

**Accepting Request:** **POST**   'http://localhost:8000/friend-request/<int:request_id/manage/>

**Body Parameters:**

    {                                {
    "user_id" : "13",
    "action": "accept"
    }
    {
    "user_id" : "13",
    "action": "reject"
    }
     {
    "user_id" : "13",
    "action": "block"
    }
     {
    "user_id" : "13",
    "action": "unblock"
    }
#### Response:

* **200 ok:** Friend request accepted/rejected/blocked/unblocked.
* **400 Bad Request:** Missing or invalid fields.

**View Pending Request:** **GET**   'http://localhost:8000/pending-requests/

#### Response:

* **200 ok:** User will get his Pending friend- Requests.


### 5.Friends List
**View Friends List:** **GET**   'http://localhost:8000/friends/

#### Response:

* **200 OK :** User will get his friends list.



### 6.ProfileView
**ProfileView:** **GET**   'http://localhost:8000/profile/<int:user_id>/

#### Response:

* **200 ok:**  user able to view profile .
* **404 Not found:**"No User matches the given query."

### 7.Activities
**User Activities:** **GET**   'http://localhost:8000/activities/

#### Response:

* **200 ok:** User will get His activities.

## Design Choices

* **Database:** We chose PostgreSQL for its robustness in handling relational data, ensuring scalability and reliability for managing friend relationships.

* **Caching:** Redis is used for caching frequently accessed data to improve performance, ensuring quick response times even under heavy load.

* **Rate Limiting:** Django's rate-limiting feature is used to prevent spammy friend requests and brute-force attacks on authentication endpoints.

* **JWT Authentication:** JWT is used for stateless authentication, providing secure, scalable user sessions.

* **Atomic Transactions:** We use transaction.atomic() in friend request handling to ensure race conditions don’t lead to inconsistent data.