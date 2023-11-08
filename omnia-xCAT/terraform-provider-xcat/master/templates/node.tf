resource "xcat_node" "devnode" {
  selectors {
    //cpucount="128"
    //machinetype = "8335-GTC"
    arch="x86_64"
    vmcpus=1
  }
  count=2
  osimage="rhels7.4-x86_64-netboot-compute"
}

resource "xcat_node" "fvtnode" {
  selectors {
    //cpucount="128"
    //machinetype = "8335-GTC"
    arch="x86_64"
    vmcpus=1
  }
  count=3
  osimage="rhels7.4-x86_64-netboot-compute"
  //osimage="rhels8.1-x86_64-netboot-compute"
}
/*
resource "xcat_node" "node1" {
  name="mid08tor03cn01"
}
*/


output "devnodes" {
  value=[ 
      "${xcat_node.devnode.*.name}"
  ]
}

output "fvtnodes" {
  value=[ 
      "${xcat_node.fvtnode.*.name}"
  ]
}

output "login_credential" {
  value="username: root; password: cluster"
}

