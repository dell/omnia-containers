package main

import (
	"github.com/hashicorp/terraform/plugin"
	"github.com/xcat2/terraform-provider-xcat/xcat"
)

func main() {
	plugin.Serve(&plugin.ServeOpts{
		ProviderFunc: xcat.Provider})
}
