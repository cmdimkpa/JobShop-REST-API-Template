# JobShop-REST-API-Template
A Production-ready REST API Framework. 

## Blood, Sweat and Tears
I built this REST API framework with my BST...but its my gift to the world. My pain for your joy :)

## So what is this thing?
If you have a Python REST API project using Python 2.7 / Flask / Apache2 / LibApache2ModWsgi / Linux(Ubuntu), then this code is all you'll ever need for your __init__.py (wsgi) file. Its as production-ready as they come. You literally have to copy and paste. Ah, but note these requirements:

- In addition to Flask, you'll need some Flask extensions: CORS (Cross-Origin Resource Sharing) and Flask RESTful, of course.
- I've added support for JSON Web Tokens, but this may be optional for you.

## About the Code (template)
So the code is a template that shows you how to setup your own API using this framework. Currently, you will see one endpoint '/api/v1/get_token' that implements the 'FetchToken' resource over GET and POST verbs. While this was functional at the time of writing, it is a template only. Please replace these directives with your own project code to utilize the framework.

# Production-Ready Features

## Multi-processing model: Parallel & Asynchronous

![image](https://user-images.githubusercontent.com/26833356/35189572-582d91e0-fe4d-11e7-8f84-9d32f58879da.png)

We use the Python multiprocessing library to create parallel, asynchronous job requests. API response is fast and reliable, even under heavy load. Scale easily for more demanding projects by increasing the value of the THREADS_PER_TRANSACTION variable (ensure you have matching server resources in terms of RAM).

## Queues, Producers & Consumers

![image](https://user-images.githubusercontent.com/26833356/35189693-f65859d8-fe50-11e7-882c-072e73c8bed7.png)

The diagram above illustrates how the Framework functions:

1. When your API gets a request, two actors are created (spawned) simultaneously on a new 'thread': the producer and the consumer. 

2. The role of the producer is to package the request into a job with standard features: JobID, JobCaller, JobRequest, etc., and then load this job into the RequestQueue (a place for pending jobs).

3. The consumer then processes the job by popping it out of the RequestQueue and feeding it into a JobProcessor. The JobProcessor determines the type of job and does the required processing, after which it adds the response component of the job to the RESPONSE_CACHE dictionary using the JOB_ID as key and RESPONSE as value (providing a unique mapping of each job to its response). The intermediary JobProcessor then releases the processed job to the waiting consumer, who then places the job in the ResponseQueue and makes an asynchronous Callback to a 'State Preservation Area' called CHECK_AND_UPDATE_STATE. 

4. This is where we check that the rules of the system are not being violated (and report if they are). We also update all transactional entities here: RequestQueue, ResponseQueue, Stamps, MaxHistReqQ, ResponseCache, TransactionNumber. Additional failover support for adding processed job responses to ResponseCache is also provided here. The 'System Integrity Rule' is simply:

<code>(len(Stamps) - len(RequestQueue)) == len(ResponseQueue) == len(ResponseCache)</code>

Jobs are stamped by producers at the time they are created, and their timestamps are noted. Now, by counting the number of stamps we have the number of all jobs ever created in the system. If we subtract the number of pending jobs, this should give us the number of processed jobs, which should also equal the number of unique entries in the ResponseCache dictionary.

That's the long and short of the System Integrity Rule.

5. Once producer and consumer are done with their tasks, the 'Main thread' then calls ResponseCache by the JobId assigned to this request when it entered the system. The result is the processed response of the request, which is then returned to the caller.

## Memory Management

The Framework is big on memory management, and does the following to keep your API from breaking:

1. Regularly free up system memory by sending a shell 'cleanup' command ('echo 3 > /proc/sys/vm/drop_caches') BEFORE each new request is processed.

2. Restricting object storage in memory to a user-defined limit. By default, this is just 50KB of RAM. The Framework will force shedding of targeted object memory once this limit is reached. This helps protect the API from fracturing when memory levels are critically low. 

Something like this:

![image](https://user-images.githubusercontent.com/26833356/35190144-f7dc4a58-fe5a-11e7-8c89-a187ff7c6e5a.png)

## Performance: Speed and Quality of Service (Reliability)

The framework is generally very fast because it makes use of Python's multi-processing capabilities. By analyzing log dumps of its output, such as the one below, I came to the following conclusions about its performance with regards to speed and QoS:

![image](https://user-images.githubusercontent.com/26833356/35190174-cd27a7b6-fe5b-11e7-82c3-a8be4ed9edb3.png)

1. Speed: the average time between state updates on my sample application is 789.6 ms. A state update happens after a consumer has finished processing a job. This is still less than 1 second, and of course also depends on your network connection (can be much better). But overall, acceptable for normal-latency applications, I should think.

2. 
