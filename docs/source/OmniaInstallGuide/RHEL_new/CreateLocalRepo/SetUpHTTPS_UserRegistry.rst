Set Up an HTTPS User Registry
===============================

**Prerequisites**: Ensure that the server has an active internet connection.

To configure a secure (HTTPS) container registry using Podman, do the following:

1. Generate TLS certificates. Create a directory for certificates. ::

    mkdir -p /root/data/certs

 ::

        cd /root/data/certs

 Generate a self-signed certificate (replace <Public_IP> with your server’s Public IP). ::

    openssl req -x509 -nodes -newkey rsa:4096 -days 365 -sha256 \
        -keyout domain.key \
        -out domain.crt \
        -subj "/CN=<PUBLIC_IP>" \
        -addext "subjectAltName=IP:<PUBLIC_IP>"


 Verify the Subject Alternative Name. ::

    openssl x509 -in domain.crt -noout -text | grep -A2 "Subject Alternative Name"

2. Create registry configuration file. Create ``/root/data/config.yml``. ::

    version: 0.1
    log:
        fields:
            service: registry
    storage:
        filesystem:
            rootdirectory: /var/lib/registry
    http:
        addr: :2727
        tls:
            certificate: /certs/domain.crt
            key: /certs/domain.key
        headers:
            X-Content-Type-Options: [nosniff]
    health:
        storagedriver:
            enabled: true

3. Start the HTTPS registry container. ::

    podman run -d \
        --name user_registry \
        --restart=always \
        --network host \
        -v /root/data:/var/lib/registry:Z \
        -v /root/data/config.yml:/etc/docker/registry/config.yml:Z \
        -v /root/data/certs:/certs:Z \
        docker.io/library/registry:2

4. Open firewall port. ::

    sudo firewall-cmd --add-port=2727/tcp --permanent 
    sudo firewall-cmd --reload

.. note:: Use a port other than 5000 when exposing the registry (for example, 3445), as port 5000 is already occupied by Omnia containers.

 The registry is now accessible at: ``https:// <PUBLIC_IP>:2727/v2/``.

5. Configure Podman to trust the registry certificate. Create the certificate directory. ::

    sudo mkdir -p /etc/containers/certs.d/<Public_IP>:2727 

 Copy the certificate. ::
    
    sudo cp /root/data/certs/domain.crt /etc/containers/certs.d/<Public_IP>:2727/ca.crt


Tag and Push an Image to the HTTPS Registry
==============================================

1. Pull an image. ::
    
    podman pull docker.io/library/nginx:1.25.2-alpine-slim 

2. Tag the image. ::
    
    podman tag docker.io/library/nginx:1.25.2-alpine-slim <Public_IP>:2727/library/nginx:1.25.2-alpine-slim 

3. Push the image. ::
    
    podman push <Public_IP>:2727/library/nginx:1.25.2-alpine-slim







