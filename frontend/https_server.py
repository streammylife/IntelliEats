#!/usr/bin/env python3
import http.server
import ssl

server_address = ('0.0.0.0', 3000)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

# Create SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('../cert.pem', '../key.pem')

# Wrap socket with SSL
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print('Serving HTTPS on port 3000...')
httpd.serve_forever()
