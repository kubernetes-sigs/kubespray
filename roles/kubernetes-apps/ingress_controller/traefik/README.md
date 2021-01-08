# Installation Guide

See Traefik Docs:

 * https://doc.traefik.io/traefik/v2.3/getting-started/install-traefik/
 * https://doc.traefik.io/traefik/providers/kubernetes-ingress/
 * https://doc.traefik.io/traefik/providers/kubernetes-crd/

The default configuration enables both kubernetes regular ingress controller,
as well as traefik custom ingressroutes controller.

The default configuration leaves traefik generating server certificates by
itself, although in some cases you may want to load a custom certificate, signed
by the authority of your choice. In other cases, LetsEncrypt certificates could
be used.

The default configuration disables hostNetwork, and leaves you free to expose
traefik however you want. To enable hostNetwork, set
`traefik_host_network: true`.
