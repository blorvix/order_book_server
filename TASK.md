Things we value
● Working software!
● Tests
● A working build
● Small atomic commits with good comments
● A simple read me (maybe talk about how to run, trade offs and design decisions)
● Simple code (but not necessarily easy!)
● The less libraries the better, we want to see your code but if you want to use X
then say why in your readme.
● Use whatever LLM tools you find fit. We do encourage extensive LLM usage
in order to speed up our velocity.
● We like functional constructs but also value good domain names and modelling
● Evidence you have thought about errors (either in code or the readme)
Things to expect
● If you get to the next stage we will pair on your code
● We will add some more features
● Maybe refactor some things
● Be prepared to talk about your code
● Understand alternatives of design decisions
● Discussions around input and error handlingEnough talk, the Problem
Description
You're given the task of writing a simple application which builds and maintains a local
Order Book (OB). This will communicate with a separate Order Book server provided with
the assignment. Every Order Book has an ordinal number, along with the best bids and
asks for different price levels. When your solution reaches the OB with a certain ordinal
number, it needs to send its current OB state to the server to be validated. Your OB solution
would be used in a trading application where every deviation from the real OB has high
consequences in terms of trading algorithms losses, so you should keep your OB solution
valid in all scenarios. The OB updates might come with high frequency e.g. 100K/s or even
200K/s so ideally your solution should perform up to these standards.
There are 4 endpoints in the provided local ob server 3 REST endpoints and one
Websocket endpoint.
● POST /start - http://localhost:9090/start
● GET /snapshot?depth=100 - http://localhost:9090/snapshot
● /delta - ws://localhost:9091/delta - WS server is running on a different port
● POST /assertion - http://localhost:9090/assertion
GET /snapshot?depth=3
Returns a snapshot of the current OB in the format below. Bids and asks are represented with
strings of decimals with scale 7. We have the price first and the quantity second in the arrays.
The query parameter depth has a default of 100 and is used to limit how many bids and asks would
there be in the returned OB.
Response format:
{
"lastUpdateId": 5,
"bids": [
["0.0010000", "0.0001000"],
["0.0009000", "0.0002000"],
["0.0008000", "0.0003000"]
],
"asks": [
["0.0011000", "0.0004000"],
["0.0012000", "0.0005000"],
["0.0013000", "0.0006000"]]
} E
ach version of the OB has an ordinal number. In the snapshot json this is represented by the
lastUpdateId .
Websocket endpoint /delta
This endpoint delivers order book delta updates immediately when a client subscribes to it. Each
delta consist of:
● Whether this update is for a bid or an ask
● The ordinal id of this update (corresponding to the lastUpdateId in the OB)
● The price level in the OB this update is for
● The new quantity in the OB for this price level
The websocket sends each update in a 26 bytes binary frame with the following format:
1. 2 bytes for an unsigned integer (a `char` in Java) which would have value 1 for bids
and 0 for asks
2. 8 bytes for a signed 64 bit integer (a `long` in Java) which would be the Ordinal Id
of that update
3. 8 bytes for a signed 64 bit integer (a `long` in Java) which represents the price level
in the OB. E.g. 10000001 represents 1.0000001
4. 8 bytes for a signed 64 bit integer (a `long` in Java) which represents the quantity
at the price level in the OB. E.g. 20000002 represents 2.0000002
You must update your OB with the updated price levels and quantities. If the quantity is 0 the price
level should be removed from the OB.
POST /assertion
The endpoint request body takes an OB in the same format as the /snapshot endpoint. It will
compare the one you send with the expected, asserting on the price levels, quantities and
lastUpdateId . Returns 200 if the OB passed in is correct and 400 if it's not correct along with the
difference to the expected one.
POST /start
The endpoint triggers the server to start serving the /snapshot and /delta endpoints. It does not
expect a request body. You need to call this endpoint before calling /snapshot and /delta . After each
call to /start you have a couple of minutes before the server exhausts all the deltas and stops. You
need to call /start again after that.The task
Create a simple executable which takes a target OB id as a parameter. It should connect to the
server on the appropriate endpoints. It should build and maintain an Order Book with a depth of 100
(it may not necessarily get that large). When your Order Book reaches the target OB id, you need to
send the OB to the /assertion endpoint for validation.
We have provided a zip archive which contains the local server
https://drive.google.com/file/d/1qqDzrC_8JA0ZV9xdzj8KK5iuTwq9QiGP/view?usp=drive_link . It has
the following structure:
● Execute the run-server.sh script to start the local server. It starts a docker container. You can
stop the server using docker.
You can now develop against it and test your solution manually. It contains test data with an
OB built with 10K updates and will send an OB update every 15ms on the websocket. This
takes about 150 seconds to run after the /start endpoint is called.
If you want the server to serve the updates faster then the script takes a delay argument in
microseconds (the default is 15000). As an example ./scripts/run-server.sh 1500 , providing
a value of 1500 would make the updates arrive 10 times faster for your tests. This also
means that the server will run out of events after only 15 seconds so have this in mind.
● You can run validate-server.sh to make sure the server is running correctly but this is not
mandatory.● The target OB id (ordinal number) the server will validate on in the /assertion endpoint is
10000.
● Your executable should take this target ordinal number as a parameter as we will use further
test scenarios to validate your solution e.g.
% teal-solution.sh --ob-id 10000 or just % teal-solution.sh 10000
● If there is a build step please explain in detail how we should build your executable and what
command we should use to run your solution.