# Polite

Polite is a modern, lightweight Insurance Policy Management platform.  
This repo is the React frontend web client for Polite

## Features

- User authentication
- Continue as a guest user
- Create policies
- View and ediit policies
- Responsive, user-friendly UI

## Live Demo

Visit the deployed frontend app:  
**[https://polite-client-web.pages.dev](https://polite-client-web.pages.dev)**


## Backend API

This frontend connects to the Polite FastAPI server  
For API documentation and setup instructions refer to the repo:  
[polite-server](https://github.com/vineetsarpal/polite-server)


## Getting Started

1. **Clone the repository**
    ```
    git clone https://github.com/vineetsarpal/polite-client-web.git
    cd polite-client-web
    ```

2. **Install dependencies**
    ```
    npm install
    ```

3. **Configure environment**
    - Copy `.env.example` to `.env` and set the backend API's base URL.

4. **Run the app**
    ```
    npm start
    ```

5. **Access the app**
    - Open [http://localhost:3000](http://localhost:3000) in your browser.


6. **Extract types from OpenAPI**
    Keep the types in sync with the API
    ```
    npm install -D openapi-typescript
    ```
    
    e.g. If a local backend API is runnning on port 8000, run:
    ```
    npx openapi-typescript http://localhost:8000/openapi.json -o src/types/openapi.ts
    ```