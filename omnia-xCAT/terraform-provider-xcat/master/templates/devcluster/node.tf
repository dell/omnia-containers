resource "xcat_node" "x86node" {
  selectors= [
    "arch=x86_64",
  ]
  count=1
  osimage="rhels7.4-x86_64-netboot-compute"
}

resource "xcat_node" "ppc64lenode" {
  selectors= [
    "arch=ppc64le",
    "gpu=1",
  ]
  count=2
  osimage="rhels7.3-ppc64le-netboot-compute"
}


output "x86nodes" {
  value=[ 
      "${xcat_node.x86node.*.name}"
  ]
}

output "ppc64lenodes" {
  value=[ 
      "${xcat_node.ppc64lenode.*.name}"
  ]
}

output "login_credential" {
  value="username: root; password: cluster"
}

