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



### References

A few links that helped in exploring about Google Cloud Engine (GCE), Kubernetes (K8), and Redis.

* Kubernetes - [Fine Parallel Processing USing a Work Queue](https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/): how to use a K8 'Job' Object and Redis to send jobs to worker nodes..."In this example, as each pod is created, it picks up one unit of work from a task queue, processes it, and repeats until the end of the queue is reached."

* [Redis Documentation](https://redis-py.readthedocs.io/en/latest/): be sure to check out *StrictRedis()* class

* Another [Redis example](https://kubernetes.io/docs/tutorials/stateless-application/guestbook/): especially good for seeing how to start a Redis Demployment + Service on GCE...and also here is the corresponding [GitHub Repo](https://github.com/kubernetes/examples/tree/master/guestbook)

* A bit on [Cloud SQL with Python](https://cloud.google.com/python/getting-started/using-cloud-sql): Be sure to be familiar with SQLAlchemy but don't bother with Flask...the corresponding [GitHub Repo](https://github.com/GoogleCloudPlatform/getting-started-python/tree/master/2-structured-data)
