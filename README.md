# Directory Authority Proxy

A proxy server for accessing Tor Directory Authority information.

## Server Information

The proxy server is publicly accessible at:
```
https://tor-directory-proxy-tunnel-6uy8hl51.devinapps.com
```

### Authentication
Basic authentication is required:
- Username: `user`
- Password: `0f476a25c8233dbbbd1c5acd0ba06a60`

## Available Endpoints

### Health Check
```
GET /healthz
```
Returns the server's health status.

### Get Tor Nodes
```
GET /nodes
```
Returns a list of current Tor nodes with their information including:
- Nickname
- Fingerprint
- Address
- Ports (OR and Dir)
- Flags
- Bandwidth

## Example Usage

Using curl:
```bash
# Health check
curl -u user:0f476a25c8233dbbbd1c5acd0ba06a60 https://tor-directory-proxy-tunnel-6uy8hl51.devinapps.com/healthz

# Get nodes
curl -u user:0f476a25c8233dbbbd1c5acd0ba06a60 https://tor-directory-proxy-tunnel-6uy8hl51.devinapps.com/nodes
```

Using JavaScript fetch:
```javascript
const auth = btoa('user:0f476a25c8233dbbbd1c5acd0ba06a60');

fetch('https://tor-directory-proxy-tunnel-6uy8hl51.devinapps.com/nodes', {
  headers: {
    'Authorization': `Basic ${auth}`
  }
})
.then(response => response.json())
.then(nodes => console.log(nodes));
```
