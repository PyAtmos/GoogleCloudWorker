# Kubernetes Work Queue for Scaling Jobs

[Astrobiology 1 GCE Dashboard](https://console.cloud.google.com/home/dashboard?project=i-agility-205814)

The goal of this is to create the infrastructure to take a containerized program, scale it to a large N number of nodes, but to still retain some sort of communication between resources as to what jobs should be run...super vague (and maybe not properly worded) but that'll further be explained in the next section I'm sure.

NOTE: **Atmos Image** using the 'old' version of Atmos...

**Atmos**: gcr.io/i-agility-205814/pyatmos_docker <-bad name but indeed is Atmos

**Worker + PyAtmos**: gcr.io/i-agility-205814/pyatmos_worker

How to build the Pyatmos worker image:

 * create vm instance with docker installed (instance 1 should have it)
 * git clone kuber-master repo
 * cd into kuber-master
 * git clone pyatmos repo
 * $ gcloud auth login
 * $ gcloud builds submit --tag gcr.io/i-agility-205814/pyatmos_worker .
 * boom done



**MISC NOTES**: should document somewhere how if you run worker.py (or more specifically pyatmos) and end it, the next restart might error. you'll see something like iterations[-1] out of range; just exit and reopen the instance.


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



### Worker Node

**SERVICE ACCOUNTS**: these are very important to make sure permissions are granted accross all nodes. For everything related worker related, please use the **ultron** service account.

Set up a 'model' VM Instance that can be converted into an 'image' or 'snapshot' to be thrown into a 'vm instance group'

Open a fresh VM Instance with **Debian** (assumed 9.5 stretch) and run the following...use sudo for EVERYTHING:

    $ cd /home

Let's get Docker first:

    $ sudo apt-get update
    $ sudo apt-get install \
     apt-transport-https \
     ca-certificates \
     curl \
     gnupg2 \
     software-properties-common
    $ curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
    # Verify that you now have the key with the fingerprint 9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88
    $ sudo apt-key fingerprint 0EBFCD88
    $ sudo add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/debian \
      $(lsb_release -cs) \
      stable"
    $ sudo apt-get update
    $ sudo apt-get install docker-ce
    # verify that docker is installed
    $ sudo docker run hello-world
    # note that it likely won't work without sudo


Now go get 'git', 'python', 'pip':

    $ sudo apt-get update
    $ sudo apt install git-all
    $ sudo apt update
    $ sudo apt install python python-dev python3 python3-dev
    $ sudo wget https://bootstrap.pypa.io/get-pip.py
    $ sudo python get-pip.py
    $ sudo python3 get-pip.py

And now get git repos

    $ sudo git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/kuber-master
    $ cd /home/kuber-master/
    $ export KUBERDIR=$PWD
    $ cd /home/
    $ sudo git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos
    $ cd /home/pyatmos/
    $ export PYATMOSDIR=$PWD
    $ cd /home/

Install python script dependencies

    $ sudo pip3 install -r $KUBERDIR/requirements.txt
    $ sudo pip3 install $PYATMOSDIR/.

Make sure you got google cloud auth for docker

    $ gcloud auth configure-docker




### Prep nodes

First delete any lingering lists from the server from old runs

    $ sudo python3 /home/kuber-master/kill.py -r 1

Launch the sql-client-1 and the sql-client-master-1 instances and run the respective lines. First line is for the first sql client and it also resets the table schema listed in the config.py file.

    $ sudo python3 /home/kuber-master/sql_client.py -r 1

If it's the first time you are creating the table then run

    $ sudo python3 /home/kuber-master/sql_client.py -c 1

And then run the master sql client

    $ sudo python3 /home/kuber-master/sql_client.py -m 1

Then launch the sql-listen node to have an easy way to query the table for updates

    $ gcloud sql connect sql-server --user=root
    #enter password
    MySQL [(none)]> Use DBNAME;
    MySQL [db name]> Select * from TABLENAME;


Start the process by adding the first point...

    $ sudo python3 starter.py


And as an option, you can run a kill server to automatically kill the workers (doesn't yet kill the node) if it sees things are empty. You can set the forgive threshold with -f...the max number of times you'll forgive the redis queue for being empty.

    $ sudo python3 /home/kuber-master/kill.py -f 2

Or you can start a node and just do a kill switch to instantly kill all workers

    $ sudo python3 /home/kuber-master/kill.py -k 1






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

Write over any local changes with whatever is at remote-origin

    git fetch origin
    git reset --hard origin/master

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

Server: [**Link**](https://console.cloud.google.com/sql/instances?project=i-agility-205814)

Connection Name: **i-agility-205814:us-west1:sql-server**

Database Name: **pyatmos**

Server IP Address: **35.233.245.129**

Standard MySQL port: **3306**


1. Set up Cloud SQL Server

 * Check out the first part of the page; [Section - Create a Cloud SQL instance](https://cloud.google.com/sql/docs/mysql/quickstart)
 * Then go to 'Databases' tab to initialize a database
 * Note: the instructions above are for a SQL Server configured for mysql

2. Set up VM Instance to be 'SQL Client'

 * Install real [mysql client](https://cloud.google.com/sql/docs/mysql/connect-admin-ip)
 * Go to Compute Engine -> VM Instance, and create a new instance with Linux Debian

Notes on connecting with mysql for a quick view...

    $ gcloud sql connect SERVERNAME --user=root
    #enter password
    MySQL [(none)]> Use DBNAME;
    MySQL [db name]> Select * from TABLENAME;


And here is how to connect via python and sqlalchemy:

    Base = declarative_base()
    dbFilePath = 'mysql+pymysql://root:PASSWORD@SQLSERVERIP:3306/DBNAME'
    engine = create_engine(dbFilePath, echo=False)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    class custom_class_name(Base):
        __tablename__ = 'TABLENAME'
        #...
    Base.metadata.create_all(engine)

3. Configure both to speak to each other.

 * We need to authorize the IP from the client to speak to the server. Check out the [video from this page](https://cloud.google.com/sql/docs/mysql/connect-compute-engine).
 * Basically grab the External IP from the Client and add it to the Networks tab of the Server
 * Go to VPC Network -> External IP Address, and change the IP Address Types from Ephemeral to Static for the SQL Client.



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
