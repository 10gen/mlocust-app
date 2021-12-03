## Distribute Load Testing Using GKE

**The original online instructions can be found here: https://cloud.google.com/architecture/distributed-load-testing-using-gke
It has diagrams and is more suited for copying/pasting etc. But PLEASE follow along this README too as steps have been optimized from much testing. The major difference is that the Google lab uses a sample AppEngine app to load test against (as opposed to testing against MDB) and their Git repo is dated using Locust 0.7 and isn't optimized for higher scale performance.**

## SA Approach before diving in

1. Test your Locust script locally on your machine to make sure it's working so you do less debugging in GKE.
2. Run a sniff test in GKE on a single node cluster with just 1 master and 1 worker and figure out how many simulated users a single worker can support. This will dictate how many workers/VMs you need for your final test. You need to make sure the Locust CPU metrics are decent and the RPS doesn't plateau.
3. Run the final load with enough hardware to hit your RPS target.

## Introduction

Load testing is key to the development of any backend infrastructure because load tests demonstrate how well the system functions when faced with real-world demands. An important aspect of load testing is the proper simulation of user and device behavior to identify and understand any possible system bottlenecks, well in advance of deploying applications to production.

However, dedicated test infrastructure can be expensive and difficult to maintain because it is not needed on a continuous basis. Moreover, dedicated test infrastructure is often a one-time capital expense with a fixed capacity, which makes it difficult to scale load testing beyond the initial investment and can limit experimentation. This can lead to slowdowns in productivity for development teams and lead to applications that are not properly tested before production deployments.

## Way before you begin!

Do all of your development and testing locally on your laptop before pushing codes out to GKE. It takes too long and is sometimes hard troubleshooting issues in GKE because you need to constantly rebuild your containers and debug logs don't always make it to the GKE pod logs.

## Now, let's begin...

Open Cloud Shell to execute the commands listed in this tutorial.

Define environment variables for the project id, region and zone you want to use for this tutorial.

**TODO: Specify the region you want your GKE cluster deployed to, e.g. us-east1**

**TODO: The default quota for compute optimized VM's is 2. You can either increase the instance size, e.g. c2-standard-30, to get more CPU's to launch more workers for 2 machines or you can increase your quota limit by going to https://cloud.google.com/compute/quotas. Each CPU is equivalent to 1 Locust worker.**

```
PROJECT=$(gcloud config get-value project)
REGION=us-central1
ZONE=${REGION}-b
CLUSTER=mlocust-app
gcloud config set compute/region $REGION 
gcloud config set compute/zone $ZONE
```

Note: Following services should be enabled in your project:
Cloud Build
Kubernetes Engine
Cloud Storage

```
gcloud services enable \
   cloudbuild.googleapis.com \
   compute.googleapis.com \
   container.googleapis.com \
   containeranalysis.googleapis.com \
   containerregistry.googleapis.com 
```

## Load testing tasks

To deploy the load testing tasks, you first deploy a load testing master and then deploy a group of load testing workers. With these load testing workers, you can create a substantial amount of traffic for testing purposes. 

Note: Keep in mind that generating excessive amounts of traffic to external systems can resemble a denial-of-service attack. Be sure to review the Google Cloud Platform Terms of Service and the Google Cloud Platform Acceptable Use Policy.

## Load testing master

The first component of the deployment is the Locust master, which is the entry point for executing the load testing tasks described above. The Locust master is deployed with a single replica because we need only one master. 

The configuration for the master deployment specifies several elements, including the ports that need to be exposed by the container (`8089` for web interface, `5557` and `5558` for communicating with workers). This information is later used to configure the Locust workers. The following snippet contains the configuration for the ports:

    ports:
       - name: loc-master-web
         containerPort: 8089
         protocol: TCP
       - name: loc-master-p1
         containerPort: 5557
         protocol: TCP
       - name: loc-master-p2
         containerPort: 5558
         protocol: TCP

Next, we would deploy a Service to ensure that the exposed ports are accessible to other pods via `hostname:port` within the cluster, and referenceable via a descriptive port name. The use of a service allows the Locust workers to easily discover and reliably communicate with the master, even if the master fails and is replaced with a new pod by the deployment. The Locust master service also includes a directive to create an external forwarding rule at the cluster level (i.e. type of LoadBalancer), which provides the ability for external traffic to access the cluster resources. 

After you deploy the Locust master, you can access the web interface using the public IP address of the external forwarding rule. After you deploy the Locust workers, you can start the simulation and look at aggregate statistics through the Locust web interface.

## Load testing workers

The next component of the deployment includes the Locust workers, which execute the load testing tasks described above. The Locust workers are deployed by a single deployment that creates multiple pods. The pods are spread out across the Kubernetes cluster. Each pod uses environment variables to control important configuration information such as the hostname of the system under test and the hostname of the Locust master. 

After the Locust workers are deployed, you can return to the Locust master web interface and see that the number of slaves corresponds to the number of deployed workers.

## Setup

1. Create GKE cluster.

**TODO:
     1) Set the machine type to a valid compute optimized type. Having more CPU's/node is recommended since it means less nodes to manage. But, be mindful of costs...
     2) Set the max nodes accordingly. If you are testing, it can be low, e.g. 1. If you are doing a large scale test, you can estimate the number of nodes needed based on Total # of Requests Per Second Required / (# of CPU's for the given machine type * 1000)**

```
gcloud container clusters create $CLUSTER \
     --zone $ZONE \
     --scopes "https://www.googleapis.com/auth/cloud-platform" \
     --machine-type "c2-standard-4" \
     --num-nodes "1" \
     --enable-autoscaling --min-nodes "1" \
     --max-nodes "10" \
     --addons HorizontalPodAutoscaling,HttpLoadBalancing
```

```
gcloud container clusters get-credentials $CLUSTER \
     --zone $ZONE \
     --project $PROJECT
```

2. Clone tutorial repo in a local directory on your cloud shell environment

```
git clone <this-repository>
```

3. Modify the Locust locustfile.py file to use your MongoDB connection string. This file is where you configure what the load test actually "does." When you run the load test, it will execute this file.

```
vi mlocust-app/docker-image/locust-tasks/locustfile.py
```
In vi, modify the line toward the top of the file to reflect your MongoDB connection string, with username and password (python modern connection string). The original like looks like this:

```
client = pymongo.MongoClient("mongodb+srv://<user>:<pwd>@demo.nndb3.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&readPreference=secondary")
```

4. Build docker image and store it in your project's container registry

```
cd mlocust-app 
gcloud builds submit --tag gcr.io/$PROJECT/locust-tasks:latest docker-image/.
```

5. Note that the following command works for new yaml files with placeholder text. Otherwise, you need to manually make the changes, e.g. the image path for the docker image. Replace [TARGET_HOST] and [PROJECT_ID] in locust-master-controller.yaml and locust-worker-controller.yaml with the deployed endpoint and project-id respectively. Note that the TARGET_HOST is irrelevant since Locust by default was designed to test against web applications.

```
sed -i -e "s/\[TARGET_HOST\]/$TARGET/g" kubernetes-config/locust-master-controller.yaml
sed -i -e "s/\[TARGET_HOST\]/$TARGET/g" kubernetes-config/locust-worker-controller.yaml
sed -i -e "s/\[PROJECT_ID\]/$PROJECT/g" kubernetes-config/locust-master-controller.yaml
sed -i -e "s/\[PROJECT_ID\]/$PROJECT/g" kubernetes-config/locust-worker-controller.yaml
```

6. Deploy Locust master and worker nodes:

```
kubectl apply -f kubernetes-config/locust-master-controller.yaml
kubectl apply -f kubernetes-config/locust-master-service.yaml
kubectl apply -f kubernetes-config/locust-worker-controller.yaml
```

7. Get the external ip of Locust master service so we can access the Locust web interface

```
EXTERNAL_IP=$(kubectl get svc locust-master -o yaml | grep ip | awk -F":" '{print $NF}')
```

8. Starting load testing

The Locust master web interface enables you to execute the load testing tasks against the system under test, as shown in the following image. echo $EXTERNAL_IP and open a new browser window and go to http://<EXTERNAL_IP>:8089.
    
To begin, specify the total number of users to simulate and a rate at which each user should be spawned. Next, click Start swarming to begin the simulation. To stop the simulation, click **Stop** and the test will terminate. The complete results can be downloaded into a spreadsheet. 

**TODO: Figure out how many users each Locust worker can manage. Based on our tests, 1000 simulated users / worker was the sweet spot. At a certain point, the performance degrades because the pods don't have enough CPU to manager more than the simulated worker threshold.**
    
9. [Optional] Scaling clients

**TODO: After you are done testing and are ready for the full scale test, make sure your GKE cluster node pool has enough node capacity and start to scale up the number of worker pods using the following command. Since each worker has been optimized to use 1 CPU, you should only scale out the workers to be total # of CPU's available in your pool - 1 (for the Locust master).**

**Important note! Locust can scale workers up but is not good at scaling workers down. The master will think there are more worker nodes than there really are. The best practice is to scale both the master and workers to 0 replicas, then scale the master to 1 and the workers to n. This way you get a clean slate.**

Scaling up the number of simulated users will require an increase in the number of Locust worker pods. To increase the number of pods deployed by the deployment, Kubernetes offers the ability to resize deployments without redeploying them. For example, the following command scales the pool of Locust worker pods to 20:

```
kubectl scale deployment/locust-worker --replicas=20
```

Below is an example of scaling the master and worker pods down to 0 so you can start your cluster out with a clean slate. This is good when you want to redeploy new code and/or k8s configurations.
    
```
kubectl scale deployment/locust-master --replicas=0
kubectl scale deployment/locust-worker --replicas=0
```

If there are any issues with your deployment, the following commands are helpful:

To view all pod names:
```
kubectl get pods -o wide
```

To view logs:
```
kubectl logs <pod name>
```

To ssh into a given pod for extreme troubleshooting:
```
kubectl exec -ti <pod name> -- /bin/sh
```

## Cleaning up
The easiest way to clean up is to delete your GCP project. Search for "manage resources" and then check the project and hit delete.

```
gcloud container clusters delete $CLUSTER --zone $ZONE
```
