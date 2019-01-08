# Image URL to use all building/pushing image targets
IMG ?= registry.gitlab.com/triggermesh/gitlabsource/controller:latest
RA_IMG ?= gcr.io/triggermesh/gitlab-receive-adapter:latest

all: test manager

# Run tests
test: generate fmt vet manifests
	go test ./cmd/... -coverprofile cover.out

# Build manager binary
manager: generate fmt vet
	go build -o bin/manager gitlab.com/triggermesh/gitlabsource/cmd/manager

# Run against the configured Kubernetes cluster in ~/.kube/config
run: generate fmt vet
	go run ./cmd/manager/main.go

# Install CRDs into a cluster
install: manifests
	kubectl apply -f config/crds

# Deploy controller in the configured Kubernetes cluster in ~/.kube/config
deploy: manifests
	kubectl apply -f config/crds
	kustomize build config/default | kubectl apply -f -

# Generate manifests e.g. CRD, RBAC etc.
manifests:
	go run vendor/sigs.k8s.io/controller-tools/cmd/controller-gen/main.go all

# Run go fmt against code
fmt:
	go fmt ./pkg/... ./cmd/...

# Run go vet against code
vet:
	go vet ./pkg/... ./cmd/...

# Generate code
generate:
	go generate ./pkg/... ./cmd/...

# Build the docker image
docker-build: test
	docker build . -t ${IMG}
	@echo "updating kustomize image patch file for manager resource"
	sed -i'' -e 's@image: .*@image: '"${IMG}"'@' ./config/default/manager_image_patch.yaml

# Build the recieve adapater image
docker-build-ra: test
	docker build . -f Dockerfile.receive_adapter -t ${RA_IMG}

# Push the manager docker image
docker-push:
	docker push ${IMG}

docker-push-ra:
	docker push ${RA_IMG}
