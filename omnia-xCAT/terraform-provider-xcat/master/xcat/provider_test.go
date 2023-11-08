package xcat

import (
	"os"
	"testing"

	"github.com/hashicorp/terraform/helper/schema"
	"github.com/hashicorp/terraform/terraform"
)

var testAccxCATProviders map[string]terraform.ResourceProvider
var testAccxCATProvider *schema.Provider

func init() {
	testAccxCATProvider = Provider().(*schema.Provider)
	testAccxCATProviders = map[string]terraform.ResourceProvider{
		"xcat": testAccxCATProvider,
	}
}

func TestProvider(t *testing.T) {
	if err := Provider().(*schema.Provider).InternalValidate(); err != nil {
		t.Fatalf("err: %s", err)
	}
}

func TestProvider_impl(t *testing.T) {
	var _ terraform.ResourceProvider = Provider()
}

func testAccxCATPreCheck(t *testing.T) {
	v := os.Getenv("XCAT_SERVER_USERNAME")
	if v == "" {
		t.Fatal("XCAT_SERVER_USERNAME must be set for acceptance tests.")
	}

	v = os.Getenv("XCAT_SERVER_PASSWORD")
	if v == "" {
		t.Fatal("XCAT_SERVER_PASSWORD must be set for acceptance tests.")
	}

	v = os.Getenv("XCAT_SERVER_URL")
	if v == "" {
		t.Fatal("XCAT_SERVER_URL must be set for acceptance tests.")
	}
}
