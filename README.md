# JobShop-REST-API-Template
A Production-ready REST API Framework. 

## Blood, Sweat and Tears
I built this REST API framework with my BST...but its my gift to the world. My pain for your joy :)

## So what is this thing?
If you have a Python REST API project using Python 2.7 / Flask / Apache2 / LibApache2ModWsgi / Linux(Ubuntu), then this code is all you'll ever need for your __init__.py (wsgi) file. Its as production-ready as they come. You literally have to copy and paste. Ah, but note these requirements:

- In addition to Flask, you'll need some Flask extensions: CORS (Cross-Origin Resource Sharing) and Flask RESTful, of course.
- I've added support for JSON Web Tokens, but this may be optional for you.

# Production-Ready Features

## Multi-processing model: Parallel & Asynchronous

![image](https://user-images.githubusercontent.com/26833356/35189572-582d91e0-fe4d-11e7-8f84-9d32f58879da.png)

We use the Python multiprocessing library to create parallel, asynchronous job requests. API response is fast and reliable, even under heavy load. Scale easily for more demanding projects by increasing the value of the THREADS_PER_TRANSACTION variable (ensure you have matching server resources in terms of RAM).

## Queues, Producers & Consumers





