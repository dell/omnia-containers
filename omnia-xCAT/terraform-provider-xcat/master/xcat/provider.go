package xcat

import (
	//"fmt"
	"os"

	"github.com/hashicorp/terraform/helper/schema"
	"github.com/hashicorp/terraform/terraform"
)

func Provider() terraform.ResourceProvider {
	return &schema.Provider{
		Schema: map[string]*schema.Schema{
			"url": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "url of xcat restapi service endpoint",
				DefaultFunc: envDefaultFunc("XCAT_SERVER_URL"),
			},

			"username": {
				Type:        schema.TypeString,
				Optional:    true,
				Description: "The username",
				DefaultFunc: envDefaultFunc("XCAT_USERNAME"),
			},

			"password": {
				Type:        schema.TypeString,
				Optional:    true,
				Description: "The password",
				DefaultFunc: envDefaultFunc("XCAT_PASSWORD"),
			},

			"token": {
				Type:        schema.TypeString,
				Required:    true,
				Description: "The token granted by xcat restapi service for the user",
				Default:     "",
			},
		},

		ResourcesMap: map[string]*schema.Resource{
			//"xcat_site":    resourceSite(),
			//"xcat_policy":  resourcePolicy(),
			//"xcat_network": resourceNetwork(),
			//"xcat_passwd":  resourcePassword(),
			//"xcat_osimage": resourceOsimage(),
			"xcat_node": resourceNode(),
			//"xcat_route":   resourceRoute(),
		},

		ConfigureFunc: configureProvider,
	}
}

func configureProvider(d *schema.ResourceData) (interface{}, error) {
	config := Config{
		Url:      d.Get("url").(string),
		Username: d.Get("username").(string),
		Password: d.Get("password").(string),
		Token:    d.Get("token").(string),
	}

	if err := config.loadAndValidate(); err != nil {
		return nil, err
	}

	return &config, nil
}

func envDefaultFunc(k string) schema.SchemaDefaultFunc {
	return func() (interface{}, error) {
		if v := os.Getenv(k); v != "" {
			return v, nil
		}

		return nil, nil
	}
}

func envDefaultFuncAllowMissing(k string) schema.SchemaDefaultFunc {
	return func() (interface{}, error) {
		v := os.Getenv(k)
		return v, nil
	}
}
