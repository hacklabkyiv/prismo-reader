Communication protocol


{
    "type": "request",
    "id": "BigMill",
    "key": "123534"
}

"type" field can be: 
 - "request": ask from reader to server
 - "response": response from server
 - "heartbeat": keepalive heatbeat from reader to server.
 
"id": identifier of device. It is name of reader, which is usually is the same as the name of machine it is installed, or "server".


{
    "type": "request",
    "operation": "unlock",
    "id": "BigMill",
    "key": "123534"
}

{
    "type": "response",
    "result": "grant"
}

'result' variants
    'grant'
    'deny'
    'usernotfound'

    
{
    "type": "heartbeat",
    "id": "BigMill"
}
