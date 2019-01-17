# GitLab Event Source for Knative

GitLab Source example shows how to wire GitLab events for consumption
by a Knative Service.

## Deploy the GitLab source controller

You will need to do two things:

* Create a new kind of API by creating a Custom Resource Definiton Object that defines what a GitLabSource is
* Deploy the controller which watches GitLabSource objects and creates GitLab webhook.

Usually these steps are performed by a Cluster admin as you need to have the Kubernetes `cluster-admin` role.

Let's create the new API definition:

```shell
kubectl apply -f https://gitlab.com/triggermesh/gitlabsource/raw/master/config/crds/sources_v1alpha1_gitlabsource.yaml
```

And now we can launch the controller and set all the required objects.


```shell
wget -O release.yaml https://gitlab.com/triggermesh/gitlabsource/-/jobs/artifacts/master/raw/release.yaml?job=manifests
kubectl apply -f release.yaml
```

If the deployment goes well you should see the same output as below:

```
namespace "gitlabsource-system" created
clusterrole.rbac.authorization.k8s.io "gitlabsource-manager-role" created
clusterrole.rbac.authorization.k8s.io "gitlabsource-proxy-role" created
clusterrolebinding.rbac.authorization.k8s.io "gitlabsource-manager-rolebinding" created
clusterrolebinding.rbac.authorization.k8s.io "gitlabsource-proxy-rolebinding" created
secret "gitlabsource-webhook-server-secret" created
service "gitlabsource-controller-manager-metrics-service" created
service "gitlabsource-controller-manager-service" created
statefulset.apps "gitlabsource-controller-manager" created
```

At this point you have installed the GitLab Eventing source in your Knative cluster. Check that the manager is running with:

```shell
kubectl get pods -n gitlabsource-system
NAME                                READY     STATUS    RESTARTS   AGE
gitlabsource-controller-manager-0   2/2       Running   0          27s
```

With the controller running you can now move on to a user persona and setup a GitLab webhook as well as a function that will consume GitLab events.

## Using the GitLab Event Source

You are now ready to use the Source and trigger functions based on GitLab projects events.

We will:

* Create a Knative service which will receive the events. To keep things simple this service will simply dump the events to `stdout`, this is the so-called: _message_dumper_
* Create a GitLab access token and a random secret token used to secure the webhooks.
* Create the event source by posting a GitLab source object manifest to Kubernetes

### Create a Knative Service

Create a simple Knative `Service` that dumps incoming messages to its log. The `service.yaml` file
defines this basic service.

This service will receive the GitLab event that you will configure in the GitLabSource object.

```yaml
apiVersion: serving.knative.dev/v1alpha1
kind: Service
metadata:
  name: gitlab-message-dumper
spec:
  runLatest:
    configuration:
      revisionTemplate:
        spec:
          container:
            image: gcr.io/knative-releases/github.com/knative/eventing-sources/cmd/message_dumper
```

Enter the following command to create the service from `service.yaml`:

```shell
kubectl -n default apply -f https://gitlab.com/triggermesh/gitlabsource/raw/master/message-dumper.yaml
```

### Create GitLab Tokens

Create a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
for GitLab that the GitLab source can use to register webhooks with
the GitLab API. Also decide on a secret token that your code will use
to authenticate the incoming webhooks from GitLab ([_secretToken_](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#secret-token)).

GitLab webhooks can be created and configured with the [Hook API](https://docs.gitlab.com/ee/api/projects.html#hooks)

Here's an example for a token named "knative-test" with the
recommended scopes:

![GitLab UI](personal_access_token.png "GitLab personal access token screenshot")

Update `gitlabsecret.yaml` with those values. If your generated access
token is `'personal_access_token_value'` and you choose your _secretToken_
as `'asdfasfdsaf'`, you'd modify `gitlabsecret.yaml` like so:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gitlabsecret
type: Opaque
stringData:
  accessToken: personal_access_token_value
  secretToken: asdfasfdsaf
```

Hint: you can makeup a random _secretToken_ with:

```shell
head -c 8 /dev/urandom | base64
```

Then, apply the gitlabsecret using `kubectl`:

```shell
kubectl --n default apply -f https://gitlab.com/triggermesh/gitlabsource/raw/master/gitlabsecret.yaml
```

### Create Event Source for GitLab Events

In order to receive GitLab events, you have to create a concrete Event
Source for a specific namespace. Be sure to replace the
`ownerAndRepository` value with a valid GitLab public repository owned
by your GitLab user.

```yaml
apiVersion: sources.eventing.triggermesh.dev/v1alpha1
kind: GitLabSource
metadata:
  name: gitlabsample
spec:
  eventTypes:
    - pull_request
  ownerAndRepository: <YOUR USER>/<YOUR REPO>
  accessToken:
    secretKeyRef:
      name: gitlabsecret
      key: accessToken
  secretToken:
    secretKeyRef:
      name: gitlabsecret
      key: secretToken
  sink:
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    name: gitlab-message-dumper
```

Then, apply that yaml using `kubectl`:

```shell
kubectl -n default apply -f https://gitlab.com/triggermesh/gitlabsource/raw/master/gitlabeventbinding.yaml
```

### Verify

Verify the GitLab webhook was created by looking at the list of
webhooks under the Settings/Integrations tab in your GitLab repository. A hook
should be listed that points to your Knative cluster.

Create a push event and check the logs of the Pod backing the `message-dumper`. You will see the GitLab event.

