Release Note for version 0.4.0
------------------------------

- This is the first public release of cloudlet-discovery project.
- it is currentlyunder rapid development, so this release includes only stable and essential
parts of the cloudlet-discovery code.
- We also checked the code compatibility with our [OpenStack-cloudlet extension](https://github.com/cmusatyalab/elijah-openstack)

- Discovery code is compose of three parts.
  1. Cloudlet-side library for registration and query  
  2. Client library for discovery  
  3. Cloud-side discovery server  

<pre>
<b> elijah-discovery (since v2.0, under developmenet)</b>
     ├─ 1. Library for registration and Cloudlet query  
     │    ├─ <b>Resource monitor</b>
     │    ├─ <b>Registration daemon</b>
     │    └─ Cache monitor
     │
     ├─ 2. <b>Client library for discovery</b>
     │
     └─ 3. Cloud-based discovery server (sources for findcloudlet.org)
          ├─ <b>Registration REST Server</b>
          ├─ Registration web site
          └─ Custom DNS Server

</pre>

- This tree shows overall components of the cloudlet-discovery, and modules without bold emphasis is not included in this release.
- For detail installation guide, please take a look at README file.
