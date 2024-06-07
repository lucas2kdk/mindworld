# Mindworld

Kubernetes Native Gaming Hosting Panel

Mindworld is a powerful and intuitive hosting panel designed to manage gaming servers on a Kubernetes cluster. It provides seamless integration with various Kubernetes features, making it easy to deploy, manage, and scale gaming servers.

## Table of Contents

- [Mindworld](#mindworld)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Requirements](#requirements)
  - [Roadmap](#roadmap)
    - [Things That Need Doing](#things-that-need-doing)
    - [Recently Implemented](#recently-implemented)
    - [Known issues](#known-issues)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Console Access**: Direct access to the server console for management and troubleshooting.
- **Node Overview**: Detailed view of all nodes within the cluster, including resource usage and status.
- **Redis**: In-memory data structure store, used as a database, cache, and message broker.
- **PostgreSQL**: Advanced, open-source relational database.
- **User Authentication**: Secure login and user management.
- **CI/CD**: Continuous Integration and Continuous Deployment pipelines.
- **RBAC**: Role-Based Access Control for fine-grained access management.
- **SSO/OAuth**: Single Sign-On and OAuth support for user authentication.
- **Helm Charts**: Pre-configured Helm charts for easy deployment.

## Requirements

- Kubernetes cluster
- Helm installed on your local machine
- Access to a Redis instance
- Access to a PostgreSQL instance

## Roadmap

### Things That Need Doing

- Redis Integration
- PostgreSQL Integration
- User Authentication
- CI/CD Implementation
- RBAC Configuration
- SSO/OAuth Support
- Helm Charts Creation
- Editing of servers
- File Browser
- File Editor
- SFTP support?
  - Considering if this is the right thing to do, or if there's something smarter.

### Recently Implemented

- Console Access
- Reimplemented Nodes Overview


### Known issues
- Console web socket shutsdown and recloses sometimes
- Console web socket sometimes recieve exit commands
- Console web socket does not close correctly.
  - If running locally, you have to exit via the Process Manager.

## Contributing

We welcome contributions from the community. To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Implement your changes and commit them with clear and concise messages.
4. Submit a pull request with a detailed description of your changes.

## License

MIT License

Copyright (c) [year] Mindworld

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

