# Kubernetes Work Queue for Scaling Jobs

The goal of this is to create the infrastructure to take a containerized program, scale it to a large N number of nodes, but to still retain some sort of communication between resources as to what jobs should be run...super vague (and maybe not properly worded) but that'll further be explained in the next section I'm sure.

## Outline

Right now this is built for scaling the Atmos program (Fortran) and the Python wrapper that triggers and customizes the Atmos run. See [Pyatmos Repo](https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos).

Removing the 'hard science' from the program, Atmos can take in several parameters (molecules or species), say large number P, to describe an input atmosphere composition and concentration; it will output several text files from which we can extract a climate model (say Temperature) and flux values for each parameter. We can further simplify this by reducing the inputs a small number, say n=2, of parameters for which we care most about, and say it outputs only temperature or a binary stable/not-stable response.

Simplify Atmos:
* **input**: 2 molecules (each a float between 0 and 1)
* **output**: a single float for temerature or a binary stable/not-stable

Other words

Check one two

- list
- lists
- listsss

1. numbers
2. numbers

