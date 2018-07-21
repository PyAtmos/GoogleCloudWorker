# Kubernetes Work Queue for Scaling Jobs

The goal of this is to create the infrastructure to take a containerized program, scale it to a large N number of nodes, but to still retain some sort of communication between resources as to what jobs should be run...super vague (and maybe not properly worded) but that'll further be explained in the next section I'm sure.

### Outline

Right now this is built for scaling the Atmos program (Fortran) and the Python wrapper that triggers and customizes the Atmos run. See [**Pyatmos** repo](https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos).

Removing the 'hard science' from the program, Atmos can take in several parameters (molecules or species), say large number P, to describe an input atmosphere composition and concentration; it will output several text files from which we can extract a climate model (say Temperature) and flux values for each parameter. We can further simplify this by reducing the inputs a small number, say n=2, of parameters for which we care most about, and say it outputs only temperature or a binary stable/not-stable response.

Simplify Atmos:
* **input**: 2 molecules (each a float between 0 and 1)
* **output**: a single float for temerature or a binary stable/not-stable

We want to search the parameter space that will give us stable or unstable (or say high vs low temp). At first we will keep the parameter space in low dimension (say 2 or 3) but ideally we'd eventually move to scale that up to 5+.

We'd also like to be a bit careful with how we start our search...We can start at an 'Earth-like' condition where the input parameters best reflect the current Earth model; then we'd slightly permutate our parameters and explore outwardly from there. This makes the problem of scaling to multiple nodes interesting because we want to use the output from one state to decide whether further exploration is desired around that state or not.

### The Strategy

1. Have 1 pod to host a Redis server for the 'task_queue'. Workers will grab the next job from the task_queue. The queue will store and pass a hash value corresponding to the input parameters for that state.
2. ~~Have 1 pod to host a Redis server for the 'platform_queue'. Workers will submit the state they just submited to the platform_queue for some master node to process and generate mor jobs for the task_queue.~~ **UPDATE**: Adrian (Google) had the idea to just have the worker do all the processing that the master would do. Let the worker decide if it should find the neighbors of that point, and add those neighbors to the task_queue.
3. Create a Cloud SQL database so that we can have a global log of all activity and to prevent redundancy in our runs. Store the following:
   * unique hash built from a dictionary of the input parameters
   * input parameter values
   * current state (queue, running, error, completed)
   * start_time (updates after entering queue and after starting run)
   * error_msg (if it errored, give a short descriptive error message)
   * complete_msg (if it completed, what was the output...stable/unstable, # temp value)
   * run_time (updates after erroring or completing)
   * out_path (directory/url path to the copied output files from the run if completed)

4. Replicated workers nodes with the Pyatmos image and an additional python file to allow communication to the task_queue and SQL database. Complete with a K8 Job Object or not? [Preemptible Instances](https://cloud.google.com/compuhttps://cloud.google.com/kubernetes-engine/docs/how-to/preemptible-vms)?

#### Redis Task Queue

*See **References** Section bellow for any links + code mentioned*

Will need a *Pod* (or *Demployment*?) K8 Object and a *Service* Object for the Redis Task Queue.

* Following taken from **Reference 4**...
* redis-deployment.yaml
* redis-service.yaml

Start service with...

```kubectl create -f ./redis-pod.yaml
kubectl create -f ./redis-service.yaml
```

### References

A few links that helped in exploring about Google Cloud Engine (GCE), Kubernetes (K8), and Redis.

1. Kubernetes [Concepts](https://kubernetes.io/docs/concepts/): A lot to read there and a lot to learn; especially the *Workloads* Section.

2. Kubernetes - [Fine Parallel Processing USing a Work Queue](https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/): how to use a K8 'Job' Object and Redis to send jobs to worker nodes..."In this example, as each pod is created, it picks up one unit of work from a task queue, processes it, and repeats until the end of the queue is reached."

3. [Redis Documentation](https://redis-py.readthedocs.io/en/latest/): be sure to check out *StrictRedis()* class

4. Another [Redis example](https://kubernetes.io/docs/tutorials/stateless-application/guestbook/): especially good for seeing how to start a Redis Demployment + Service on GCE...and also here is the corresponding [GitHub Repo](https://github.com/kubernetes/examples/tree/master/guestbook)

5. A bit on [Cloud SQL with Python](https://cloud.google.com/python/getting-started/using-cloud-sql): Be sure to be familiar with SQLAlchemy but don't bother with Flask...the corresponding [GitHub Repo](https://github.com/GoogleCloudPlatform/getting-started-python/tree/master/2-structured-data)
