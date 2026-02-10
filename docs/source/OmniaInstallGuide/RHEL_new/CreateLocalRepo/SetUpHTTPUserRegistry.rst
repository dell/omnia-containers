Set Up an HTTP User Registry
=================================

**Prerequisites**: Ensure that the server has an active internet connection.

To deploy a container registry using Podman, do the following:

1.  Create a registry storage directory. ::

        mkdir -p /root/data 
        chown -R 1000:1000 /root/data

2. Start the registry container. ::
    
    sudo podman run -d --name user_registry  --restart=always -p 3445:5000 -v /root/data:/var/lib/registry:Z docker.io/library/registry:2 

3. Open firewall port. Allow inbound traffic on port 3445. ::

        sudo firewall-cmd --add-port=3445/tcp --permanent 
        sudo firewall-cmd --reload

.. note:: Use a port other than 5000 when exposing the registry (for example, 3445), as port 5000 is already occupied by Omnia containers.

The registry is now accessible at: ``http:// <PUBLIC_IP>:3445/v2/``.


Tag and Push an Image to the Registry
======================================

To pull an image, tag it for your local registry, and push the changes, do the following:

1.  Pull the image. ::

        podman pull docker.io/library/nginx:1.25.2-alpine-slim 

2. Tag the image. Replace <Public_IP> with your server’s Public IP. ::

        podman tag docker.io/library/nginx:1.25.2-alpine-slim <Public_IP>:3445/library/nginx:1.25.2-alpine-slim

3.  Push the image to the registry. Because this is an HTTP registry, disable TLS verification. ::

        podman push <Public_IP>:3445/library/nginx:1.25.2-alpine-slim --tls-verify=false



