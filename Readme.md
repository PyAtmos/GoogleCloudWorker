# Kubernetes Work Queue for Scaling Jobs

[Astrobiology 1 GCE Dashboard](https://console.cloud.google.com/home/dashboard?project=i-agility-205814)

The goal of this is to create the infrastructure to take a containerized program, scale it to a large N number of nodes, but to still retain some sort of communication between resources as to what jobs should be run...super vague (and maybe not properly worded) but that'll further be explained in the next section I'm sure.

## Outline

Right now this is built for scaling the Atmos program (Fortran) and the Python wrapper that triggers and customizes the Atmos run. See [**Pyatmos** repo](https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos).

Removing the 'hard science' from the program, Atmos can take in several parameters (molecules or species), say large number P, to describe an input atmosphere composition and concentration; it will output several text files from which we can extract a climate model (say Temperature) and flux values for each parameter. We can further simplify this by reducing the inputs a small number, say n=2, of parameters for which we care most about, and say it outputs only temperature or a binary stable/not-stable response.

Simplify Atmos:
* **input**: 2 molecules (each a float between 0 and 1)
* **output**: a single float for temerature or a binary stable/not-stable

We want to search the parameter space that will give us stable or unstable (or say high vs low temp). At first we will keep the parameter space in low dimension (say 2 or 3) but ideally we'd eventually move to scale that up to 5+.

We'd also like to be a bit careful with how we start our search...We can start at an 'Earth-like' condition where the input parameters best reflect the current Earth model; then we'd slightly permutate our parameters and explore outwardly from there. This makes the problem of scaling to multiple nodes interesting because we want to use the output from one state to decide whether further exploration is desired around that state or not.

## The Strategy

**UPDATED:** June 23, 2018

1. Redis Server (1 node + pod) to host the queues and lists. There will be several lists, all holding a string representing the input parameters, and each serving a very specific purpose.
2. Cloud SQL Database to keep track of all runs.
3. SQL Client (1 node + pod) to read queues/lists from Redis server to look for what to write/update to the Cloud SQL Database.
4. Job K8 Objects running all the individual jobs read from a Redis queue.
5. Master Node (1 node + pod) to search the neighbors of the completed runs, and add those points to a redis queue/line to see if it already exists on a server. (maybe put this under responsiblities of SQL Client) -> **UPDATE**: have a second SQL Client node but have it perform a different set of tasks (those of the master)

Sample WorkFlow:

* starter.py adds point to *main_sql_Q*;
* sql client (master) adds to *main_Q*
* sql client (non-master) takes item off *main_sql_Q* and adds it as a new point to DB; also adds to *main_Q*
* worker node takes item off *main_Q* and adds to *processing_Q* (lease function); adds to *running_sql_Q*; starts the run
* worker finishes the run; adds to *error_sql_Q* if it errored; adds to *complete_sql_Q* if completed; 0 if stable, 1 if unstable; searches for neighbors if stable
* sql_client takes item off *error_sql_Q* (non master) and *complete0_sql_Q* (non master) and *complete1_sql_Q* (master) and updates DB respecitvely.
* sql_client then cheks for *main_sql_Q* items again to add to *main_Q*
* loop continues until the kill_switch is turned on (see kill.py)

Cloud SQL database...Store the following:
   * unique hash built from a dictionary of the input parameters
   * input parameter values
   * current state (queue, running, error, completed)
   * start_time (updates after entering queue and after starting run)
   * error_msg (if it errored, give a short descriptive error message)
   * complete_msg (if it completed, what was the output...stable/unstable, # temp value)
   * run_time (updates after erroring or completing)
   * out_path (directory/url path to the copied output files from the run if completed)

NOTE: Complete with a K8 Job Object or not? [Preemptible Instances](https://cloud.google.com/compuhttps://cloud.google.com/kubernetes-engine/docs/how-to/preemptible-vms)?

### Redis Task Queue

**Install Redis Server**
[Link](https://cloud.google.com/community/tutorials/setting-up-redis)

Create VM Instance and SSH into it...

    $ sudo apt-get update #update Debian
    $ sudo apt-get -y install redis-server #install Redis
    $ ps -f -u redis #verify it is running
    #currently will only accept connections from 127.0.0.1 - the local machine

    $ sudo nano /etc/redis/redis.conf #edit redis config to allow remote acess
    #change bind 127.0.0.1 to bind 0.0.0.0
    #now any IP Address can touch the redis instance
    #Redis accepts remote connections on TCP port 6379

    #restart the service:
    $ sudo service redis-server restart


Try and 'ping' the Redis server...
First find the "REDIS_IPV4_ADDRESS" by finding the "external* IP address" of the Redis VM Instance. *I tried 'external' and it didn't work; but 'internal IP address' did.

    $ redis-cli -h 10.138.0.21 ping
    #did you get pong?


Install and use **git**:

    sudo apt install git-all
    git clone URL


Install **pip**:

    sudo apt update
    sudo apt install python python-dev python3 python3-dev
    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py

Install other python packages:

    # google cloud packages 
    sudo pip install google-cloud-storage
    sudo pip install cloudstorage

    # other packages 
    sudo pip install redis
    sudo pip install numpy
    sudo pip install sqlalchemy
    sudo pip install pymysql

Install **pyatmos**:
      
    # First, move to a clean working area, then checkout this package
    git clone git@gitlab.com:frontierdevelopmentlab/astrobiology/pyatmos.git
    
    # install this python package as a module 
    cd pyatmos
    sudo pip install -e . 

Install **docker**:
    # This is needed for pyatmos
    sudo apt install docker.io


Establish Auth from command line

    $ gcloud auth login




*See References Section bellow for any links + code mentioned*

Will need a *Pod* (or *Demployment*?) K8 Object and a *Service* Object for the Redis Task Queue.

* Following taken from *Reference 4*...
* redis-deployment.yaml
* redis-service.yaml

Start service with...

    $ kubectl create -f ./redis/redis-pod.yaml
    $ kubectl create -f ./redis/redis-service.yaml


### Cloud SQL

i-agility-205814:us-west1:kuber-db-test-rodd

mysql+mysqldb://root@/kuber-db-test-rodd?unix_socket=/cloudsql/i-agility-205814:kuber-db-test-rodd

a = ('mysql+pymysql://{user}:{password}@35.197.109.206/{database}').format(
            user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
            database=CLOUDSQL_DATABASE)

Google Cloud documentation to set up [access through IP Address](https://cloud.google.com/sql/docs/mysql/connect-external-app#appaccessIP)

[Other](http://docs.sqlalchemy.org/en/latest/dialects/mysql.html#using-mysqldb-with-google-cloud-sql)

Here is the link to the Database I already made for testing...[**kuber-db-test-rodd**](https://console.cloud.google.com/sql/instances/kuber-db-test-rodd/overview?project=i-agility-205814&duration=PT1H)


Reference 5 gave some hints on how to connect to Cloud SQL but they were also doing it through/with a other python packages (Flask) since they wanted to host a webpage or something. Here is the snippit of code, copy n pasted, that gives the info...Sourced from the config.py file...

    # The CloudSQL proxy is used locally to connect to the cloudsql instance.
    # To start the proxy, use:
    #
    #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
    #
    # Port 3306 is the standard MySQL port. If you need to use a different port,
    # change the 3306 to a different port number.

    # Alternatively, you could use a local MySQL instance for testing.
    LOCAL_SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://{user}:{password}@127.0.0.1:3306/{database}').format(
            user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
            database=CLOUDSQL_DATABASE)

I got this error after trying to connect to the Cloud SQL database...
*"2018/07/24 21:18:24 the default Compute Engine service account is not configured with sufficient permissions to access the Cloud SQL API from this VM. Please create a new VM with Cloud SQL access (scope) enabled under "Identity and API access". Alternatively, create a new "service account key" and specify it using the -credential_file parameter"*


So I still need to figure out the best way to connect the sqlalchemy stuff to the GCE SQL database that is linked above.


## Dictionary

We define the initial input atmosphere to Atmos by defining a **parameter** state. A parameter can be represented in 3 major ways:
1. **Parameter Dictionary**: a key/value relationship is built from molecule/concentration; this is the best way to represent the parameter state we are exploring in understanding the inputs, but it is hard to pass a dictionary object between nodes.
2. **Parameter Code**: a string representation/codification of the Parameter Dictionary; basically it is a comma-separated string only listing the concentrations of each molecule in order of the original 'starting point' from starter.py; this value is encoded from a dictionary and can be decoded back to a dictionary.
3. **Parameter Hash**: a hashed representation of the Parameter Dictionary; concats molecules and concentrations together into a long string and is then hashed; can't be unhashed; good for creating a unique id for the parameter state.



## References/Links

A few links that helped in exploring about Google Cloud Engine (GCE), Kubernetes (K8), and Redis.

1. Kubernetes [Concepts](https://kubernetes.io/docs/concepts/): A lot to read there and a lot to learn; especially the *Workloads* Section.

2. Kubernetes - [Fine Parallel Processing USing a Work Queue](https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/): how to use a K8 'Job' Object and Redis to send jobs to worker nodes..."In this example, as each pod is created, it picks up one unit of work from a task queue, processes it, and repeats until the end of the queue is reached."

3. [Redis Documentation](https://redis-py.readthedocs.io/en/latest/): be sure to check out *StrictRedis()* class

4. Another [Redis example](https://kubernetes.io/docs/tutorials/stateless-application/guestbook/): especially good for seeing how to start a Redis Demployment + Service on GCE...and also here is the corresponding [GitHub Repo](https://github.com/kubernetes/examples/tree/master/guestbook)

5. A bit on [Cloud SQL with Python](https://cloud.google.com/python/getting-started/using-cloud-sql): Be sure to be familiar with SQLAlchemy but don't bother with Flask...the corresponding [GitHub Repo](https://github.com/GoogleCloudPlatform/getting-started-python/tree/master/2-structured-data)
