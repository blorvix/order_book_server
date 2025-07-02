# **Assignment Scripts**

**You are expected to implement your build steps in `build-assignment.sh` and your run steps in `run-assignment.sh`.**

**The scripts in this folder provide:**

- **Running the order-book server** that you will build your solution against
- **Validating server functionality** to verify that the server is working correctly

## **Available Scripts**

### **run-server.sh**
**Starts the Teal assignment server in a Docker container using direct JAR execution.**

- Automatically stops any existing server container
- Uses volume mounting to run the server JAR directly
- Exposes ports 9090 and 9091 for the server

```bash
./run-server.sh
```

### **validate-server.sh**
**Validates the server by running the test implementation against it 
with an optional target ordinal parameter.**

- Requires the server to be running first
- Uses volume mounting to run the test JAR directly
- Fetches and displays assertion results from the server

```bash
./validate-server.sh [target_ordinal]
```

**Parameters:**
- `target_ordinal` (optional): The target ordinal value for order book processing. **Default: 10000**

**Example:**
```bash
./validate-server.sh 15000
```

- Scripts use the base `openjdk:21-jdk-slim` image
- The server automatically stops and restarts if already running