# Product Design Specification
## Kubernetes-Based Game Server Hosting Panel

### Project Overview
The project aims to create a Kubernetes-based game server hosting panel similar to Pterodactyl. The panel will allow users to create, manage, and interact with game servers seamlessly. The primary features will include:
- Creating new game servers using different Docker images.
- Managing game servers with functionalities such as start, stop, edit settings, TTY console access, and file management.
- Providing a user-friendly interface for easy navigation and server management.
- Ensuring secure authentication and authorization mechanisms.
- Planning for future enhancements and scalability.

### Features

#### Create New Game Servers
**Functionality:** Users can create game servers by selecting from different Docker images.  
**Details:** Users will define Kubernetes Pod specifications for each game server, including CPU, memory, and storage requirements.

**Test Requirements:**
1. Verify that users can select from a list of available Docker images.
2. Ensure that users can specify CPU, memory, and storage requirements.
3. Validate that the game server is created with the specified Kubernetes Pod configurations.

#### Manage Game Servers
- **TTY Console Access:** Provide direct console access to each game server.
- **Start/Stop Servers:** Enable starting and stopping of game servers.
- **Edit Settings:** Allow users to modify game server configurations and settings.
- **File Management:** Provide functionalities to read, view, and edit files within game servers.
- **Delete Servers:** Allow users to delete game servers when they are no longer needed.

**Test Requirements:**
1. Verify TTY console access functionality for each game server.
2. Ensure that users can start and stop game servers.
3. Validate that users can edit and save game server settings.
4. Check file management capabilities, including reading, viewing, and editing files.
5. Confirm that users can delete game servers and that the resources are freed up.

#### User-Friendly Interface
**Frontend Framework:** Use TailwindCSS for developing a modern and intuitive interface.  
**API Integration:** Ensure seamless integration between the frontend and backend API for efficient server management.

**Test Requirements:**
1. Ensure that the user interface is responsive and intuitive.
2. Validate that the frontend correctly communicates with the backend API.
3. Verify that all user actions in the frontend result in the appropriate backend operations.

#### Future Enhancements
**Scalability:** Plan for future scalability to accommodate more users and game servers.  
**New Features:** Consider adding advanced features like automated backups, performance monitoring, and alert systems.

### Application Architecture

#### Architectural Diagram
```plaintext
+-------------------+      +--------------------+      +-------------------+
|   User Interface  | <--> |   Backend API      | <--> |   Kubernetes      |
| (React + Tailwind)|      | (Node.js, Express) |      |   Cluster         |
+-------------------+      +--------------------+      +-------------------+
        |                        |                          |
        v                        v                          v
+-------------------+    +--------------------+      +-------------------+
| Authentication    |    |    Database        |      | Docker Images     |
| Service (OAuth2)  |    |  (PostgreSQL)      |      +-------------------+
+-------------------+    +--------------------+
```
#### Component Descriptions

- User Interface: A React application styled with TailwindCSS, providing an intuitive and responsive user experience.
- Backend API: A Node.js application using Express framework, handling requests from the frontend and interacting with the Kubernetes cluster.
- Kubernetes Cluster: Manages the lifecycle of game server pods using predefined specifications.
- Authentication Service: OAuth2-based service for secure user authentication and authorization.
- Database: PostgreSQL database to store user data, game server configurations, and other relevant information.
- Docker Images: Predefined Docker images for different game servers, pulled from a container registry.

### Backend API Development
#### Main Endpoints
- Create Game Server
    - Endpoint: POST /api/game-servers
    - Description: Create a new game server with specified configurations.
- Start Game Server
    - Endpoint: POST /api/game-servers/:id/start
    - Description: Start the specified game server.
- Stop Game Server
    - Endpoint: POST /api/game-servers/:id/stop
    - Description: Stop the specified game server.
- Edit Game Server
    - Endpoint: PUT /api/game-servers/:id
    - Description: Update settings and configurations of the specified game server.
- Delete Game Server
    - Endpoint: DELETE /api/game-servers/:id
    - Description: Delete the specified game server.
- TTY Console Access
    - Endpoint: GET /api/game-servers/:id/tty
    - Description: Provide TTY console access to the specified game server.
- File Management
    - Endpoint: GET /api/game-servers/:id/files
    - Description: Retrieve files from the specified game server.
    - Endpoint: POST /api/game-servers/:id/files
    - Description: Upload files to the specified game server.
    - Endpoint: PUT /api/game-servers/:id/files
    - Description: Edit files within the specified game server.

###Frontend Development
#### Best Practices
- Component-Based Architecture: Develop reusable and modular components.
- State Management: Use a state management library like Redux or Context API for efficient state handling.
- Responsive Design: Ensure the interface is responsive and works well on various devices.
- Accessibility: Follow accessibility best practices to make the application usable for all users.
- Example Component: Create Game Server

``` javascript
import React, { useState } from 'react';
import axios from 'axios';

const CreateGameServer = () => {
    const [name, setName] = useState('');
    const [image, setImage] = useState('');
    const [cpu, setCpu] = useState('');
    const [memory, setMemory] = useState('');
    const [storage, setStorage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/game-servers', {
                name,
                image,
                cpu,
                memory,
                storage,
            });
            alert('Game server created successfully!');
        } catch (error) {
            console.error('Error creating game server:', error);
            alert('Failed to create game server.');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Server Name" required />
            <input type="text" value={image} onChange={(e) => setImage(e.target.value)} placeholder="Docker Image" required />
            <input type="text" value={cpu} onChange={(e) => setCpu(e.target.value)} placeholder="CPU" required />
            <input type="text" value={memory} onChange={(e) => setMemory(e.target.value)} placeholder="Memory" required />
            <input type="text" value={storage} onChange={(e) => setStorage(e.target.value)} placeholder="Storage" required />
            <button type="submit">Create Server</button>
        </form>
    );
};

export default CreateGameServer;

```

### Test Requirements

#### Create New Game Servers
1. Verify that users can select from a list of available Docker images.
2. Ensure that users can specify CPU, memory, and storage requirements.
3. Validate that the game server is created with the specified Kubernetes Pod configurations.

#### Manage Game Servers
1. Verify TTY console access functionality for each game server.
2. Ensure that users can start and stop game servers.
3. Validate that users can edit and save game server settings.
4. Check file management capabilities, including reading, viewing, and editing files.
5. Confirm that users can delete game servers and that the resources are freed up.

#### User-Friendly Interface
1. Ensure that the user interface is responsive and intuitive.
2. Validate that the frontend correctly communicates with the backend API.
3. Verify that all user actions in the frontend result in the appropriate backend operations.

#### Authentication and Authorization
1. Verify that only authenticated users can access the application.
2. Ensure that users have appropriate permissions for the actions they perform.
3. Validate that unauthorized access is properly restricted.
