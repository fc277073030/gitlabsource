/*
Copyright 2019 The TriggerMesh Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// GitLabSourceSpec defines the desired state of GitLabSource
type GitLabSourceSpec struct {
	// ServiceAccountName holds the name of the Kubernetes service account
	// as which the underlying K8s resources should be run. If unspecified
	// this will default to the "default" service account for the namespace
	// in which the GitLabSource exists.
	// +optional
	ServiceAccountName string `json:"serviceAccountName,omitempty"`

	// OwnerAndRepository is the GitLab owner/org and repository to
	// receive events from. The repository may be left off to receive
	// events from an entire organization.
	// Examples:
	//  myuser/project
	//  myorganization
	// +kubebuilder:validation:MinLength=1
	OwnerAndRepository string `json:"ownerAndRepository"`

	// EventType is the type of event to receive from Gitlab. These
	// correspond to supported events to the add project hook
	// https://docs.gitlab.com/ee/api/projects.html#add-project-hook
	// +kubebuilder:validation:MinItems=1
	// +kubebuilder:validation:Enum=push_events,push_events_branch_filter,issues_events,confidential_issues_events,merge_requests_events,tag_push_events,note_events,job_events,pipeline_events,wiki_page_events
	EventTypes []string `json:"eventTypes"`

	// AccessToken is the Kubernetes secret containing the GitLab
	// access token
	AccessToken SecretValueFromSource `json:"accessToken"`

	// SecretToken is the Kubernetes secret containing the GitLab
	// secret token
	SecretToken SecretValueFromSource `json:"secretToken"`

	// SslVerify if true configure webhook so the ssl verification is done when triggering the hook
	SslVerify bool `json:"sslverify,omitempty"`

	// Sink is a reference to an object that will resolve to a domain
	// name to use as the sink.
	// +optional
	Sink *corev1.ObjectReference `json:"sink,omitempty"`
}

// SecretValueFromSource represents the source of a secret value
type SecretValueFromSource struct {
	// The Secret key to select from.
	SecretKeyRef *corev1.SecretKeySelector `json:"secretKeyRef,omitempty"`
}

// GitLabSourceStatus defines the observed state of GitLabSource
type GitLabSourceStatus struct {
	// ID of the project hook registered with GitLab
	Id string `json:"Id,omitempty"`

	// SinkURI is the current active sink URI that has been configured
	// for the GitHubSource.
	// +optional
	SinkURI string `json:"sinkUri,omitempty"`
}

// MarkSink sets the sink fot GitLabSource
func (s *GitLabSourceStatus) MarkSink(uri string) {
	s.SinkURI = uri
}

// +genclient
// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// GitLabSource is the Schema for the gitlabsources API
// +k8s:openapi-gen=true
type GitLabSource struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   GitLabSourceSpec   `json:"spec,omitempty"`
	Status GitLabSourceStatus `json:"status,omitempty"`
}

// +k8s:deepcopy-gen:interfaces=k8s.io/apimachinery/pkg/runtime.Object

// GitLabSourceList contains a list of GitLabSource
type GitLabSourceList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []GitLabSource `json:"items"`
}

func init() {
	SchemeBuilder.Register(&GitLabSource{}, &GitLabSourceList{})
}
