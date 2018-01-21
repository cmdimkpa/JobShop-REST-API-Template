from __future__ import division
from flask import Flask, request
from flask_restful import Api, Resource
from flask_cors import CORS
import jwt;
from multiprocessing import Pool;
import datetime;
import cPickle;
import time;
import subprocess;

app = Flask(__name__)
CORS(app)
api = Api(app)

global RequestQueue, ResponseQueue, Workflow, Stamps, TransactionNumber, THREADS_PER_TRANSACTION, hashkey, MaxMemoryConsumption_KB, \
       MaxHistReqQ, ResponseCache, STATUS200, STATUS404

hashkey = "yourhashkeygoeshere";

RequestQueue = [];
ResponseQueue = [];
THREADS_PER_TRANSACTION = 1;
REQUEST = None;
Stamps = [];
TransactionNumber = 0;
MaxMemoryConsumption_KB = 50;
MaxHistReqQ = 0;
ResponseCache = {};
STATUS200 = 1;
STATUS404 = 1;

def shell_runner(cmds):
    try:
        proc = subprocess.Popen([cmds],shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,) ; stdout_value = proc.communicate()
        return stdout_value[0]
    except Exception as Error:
        return str(Error)

def MemoryUsed():
	mem = 0;
	for resource in [RequestQueue,ResponseQueue,Stamps,ResponseCache]:
		mem+=(len(cPickle.dumps(resource)));
	# get in Kilobytes
	return '{}K'.format(round((mem/1000),2));

def AddToResponseCache(job):
	# make transaction response available (persistent)
	global ResponseCache
	try:
		ResponseCache[job.job_id] = job.response;
	except:
		AddToResponseCache(job);

class Job:
	# create a job wrapper around a request
	def __init__(self):
		self.timestamp = str(datetime.datetime.today()); # job creation time
		self.caller = None; # the job caller
		self.request = None; # job request
		self.response = None; # job response
		self.state = 0;  # job binary state
		self.job_id = None; # JobID

def JobProcessor(job):
	# pull job request
	request = job.request;

	# multi-tasking

	if job.caller == 'FetchToken_Get':
		JSON = {};
		JSON['owner'] = "Monty Dimkpa";
		JSON['Your IP'] = request;
		# set job response and state
		job.response = JSON;
		job.state = 1;

	if job.caller == 'FetchToken_Post':
		JSON = {};
		JSON['token'] = jwt.encode(request, hashkey, algorithm='HS256')
		# set job response and state
		job.response = JSON;
		job.state = 1;

	if job.state == 0:
		# log processing error
		print "JobShop API: Error processing this Job: descriptors :: Caller=";job.caller;", Queued=";job.timestamp
	else:
		AddToResponseCache(job); # make job response available
	return job

def StateVerified():
	# verify system integrity
	return (len(Stamps) - len(RequestQueue)) == len(ResponseQueue) == len(ResponseCache);  # system integrity rule

def Producer(request,caller,job_id):
	global RequestQueue, Stamps
	job = Job();
	job.job_id = job_id; # map JobID
	job.caller = caller; # map caller to job object
	job.request = request; # map request to job object
	RequestQueue.append(job); # add job to RequestQueue
	Stamps.append(job.timestamp); # stamp this job
	return None,(RequestQueue, ResponseQueue,Stamps,MaxHistReqQ,ResponseCache);      # send nonce + state to Callback

def Consumer(job_id):
	global RequestQueue, ResponseQueue
	try:
		# target the JobID
		job_index = [job.job_id for job in RequestQueue].index(job_id);
		ResponseQueue.append(JobProcessor(RequestQueue.pop(job_index)));    # force the target job through the job processor
		return [job.job_id for job in ResponseQueue].index(job_id),(RequestQueue, ResponseQueue,Stamps,MaxHistReqQ,ResponseCache);   # send processed job + state to Callback
	except:
		Consumer(job_id);  # try again if something goes wrong

def CheckAndUpdateState(feedback):

	global RequestQueue, ResponseQueue, Stamps, MaxHistReqQ, ResponseCache, TransactionNumber

	result, STATE = feedback;

	RequestQueue, ResponseQueue,Stamps,MaxHistReqQ, ResponseCache = STATE;

	RequestQueue = RequestQueue;
	ResponseQueue = ResponseQueue;
	Stamps = Stamps;
	MaxHistReqQ = MaxHistReqQ;
	ResponseCache = ResponseCache;

	if result != None:
		AddToResponseCache(result);    # make job response available (failover)
		if StateVerified():
			TransactionNumber+=1;
			if len(RequestQueue)>MaxHistReqQ:
				MaxHistReqQ = len(RequestQueue);
			print "[JobShop API] Call#: "+str(TransactionNumber)+" :: Stmps:"+str(len(Stamps))+"|ReqQ:"+str(len(RequestQueue))+"("+str(MaxHistReqQ)+")|ResQ:"+str(len(ResponseQueue))+"|RC:"+str(len(ResponseCache))+"|QoS:"+'{}%'.format(round((100*STATUS200/(STATUS404+STATUS200)),2))+"|Mem:"+MemoryUsed();
	else:
		if StateVerified()==False:
			# print error message
			print "[JobShop API] Error: Problem with system state, check API logs.";

class FetchToken(Resource):

	global RequestQueue, ResponseQueue,Stamps, MaxHistReqQ,ResponseCache, STATUS200, STATUS404

	def get(self):

		global RequestQueue,ResponseQueue,Stamps,MaxHistReqQ,ResponseCache, STATUS200, STATUS404

		# manage process memory
		shell_runner('sudo bash;echo 3 > /proc/sys/vm/drop_caches');

		# manage object memory
		memory_used = float(MemoryUsed().split('K')[0]);
		if memory_used > MaxMemoryConsumption_KB:

			# reset object stores
			for resource in [RequestQueue,ResponseQueue,Stamps,ResponseCache]:
				del resource;
			
			RequestQueue=[];
			ResponseQueue=[];
			Stamps=[];
			ResponseCache={};
		
		REQUEST = request.remote_addr # Your Request Here;
		CALLER = 'FetchToken_Get';
		JOB_ID = CALLER+"_"+str(datetime.datetime.today());

		Workflow = Pool(THREADS_PER_TRANSACTION);

		producer = Workflow.apply_async(Producer,args=(REQUEST,CALLER,JOB_ID,),callback=CheckAndUpdateState);
		consumer = Workflow.apply_async(Consumer,args=(),callback=CheckAndUpdateState);

		producer.get(); # best-effort create job
		consumer.get(); # best-effort process job

		Workflow.close();
		Workflow.join();

		# succeed or fail

		try:
			STATUS200+=1;
			return ResponseCache[JOB_ID];
		except:
			STATUS404+=1;
			return {};

	def post(self):

		global RequestQueue,ResponseQueue,Stamps, MaxHistReqQ, ResponseCache, STATUS200, STATUS404

		# manage process memory
		shell_runner('sudo bash;echo 3 > /proc/sys/vm/drop_caches');

		# manage object memory
		memory_used = float(MemoryUsed().split('K')[0]);
		if memory_used > MaxMemoryConsumption_KB:
			
			# reset object stores
			for resource in [RequestQueue,ResponseQueue,Stamps,ResponseCache]:
				del resource;
			
			RequestQueue=[];
			ResponseQueue=[];
			Stamps=[];
			ResponseCache={};
		
		REQUEST = request.get_json(force=True);
		CALLER = 'FetchToken_Post';
		JOB_ID = CALLER+"_"+str(datetime.datetime.today());

		Workflow = Pool(THREADS_PER_TRANSACTION);

		producer = Workflow.apply_async(Producer,args=(REQUEST,CALLER,JOB_ID,),callback=CheckAndUpdateState);
		consumer = Workflow.apply_async(Consumer,args=(JOB_ID),callback=CheckAndUpdateState); # send JobID to consumer to force right job selection

		producer.get(); # best-effort create job
		consumer.get(); # best-effort process job

		Workflow.close();
		Workflow.join();

		# succeed or fail

		try:
			STATUS200+=1;
			return ResponseCache[JOB_ID];
		except:
			STATUS404+=1;
			return {};

api.add_resource(FetchToken,'/api/v1/get_token');

if __name__ == '__main__':
	app.run();
