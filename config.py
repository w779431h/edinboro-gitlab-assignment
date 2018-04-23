#!/usr/bin/ssh-agent python3

# contains any global variables for use by multiple files

# the hostname where the GitLab server is hosted
# do not include ending slash '/'
# fqdn means Fully Qualified Domain Name
host_url_just_fqdn = "codestore.cs.edinboro.edu"

# whether SSL is configured on server
use_ssl = False
if use_ssl:
    proto_type = "https://"
else:
    proto_type = "http://"

# this is the regular URL
host_url = proto_type + host_url_just_fqdn
