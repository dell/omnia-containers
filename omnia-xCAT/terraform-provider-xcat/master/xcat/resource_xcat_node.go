package xcat

import (
	"fmt"
	"github.com/tidwall/gjson"
	"log"
	"reflect"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/hashicorp/terraform/helper/resource"
	"github.com/hashicorp/terraform/helper/schema"
	"github.com/hashicorp/terraform/helper/validation"
)

var systemSyncLock sync.Mutex

func resourceNode() *schema.Resource {
	return &schema.Resource{
		Create: resourceNodeCreate,
		Read:   resourceNodeRead,
		Update: resourceNodeUpdate,
		Delete: resourceNodeDelete,

		Schema: map[string]*schema.Schema{
			"selectors": {
				Type:     schema.TypeList,
				Elem:     &schema.Schema{Type: schema.TypeString},
				Optional: true,
				Computed: false,
				ForceNew: true,
				/*
				   ValidateFunc: func(val interface{}, key string) (warns []string, errs []error) {
				                     v := val.([]string)
				                     re:=regexp.MustCompile(`([^=!~><]+)([=!~><]{1,2})([^=!~><]+)`)
				                     ValidSelectors:=make([]string,0,len(SelectorOpMaps))
				                     for k,_:=range SelectorOpMaps{
				                         ValidSelectors=append(ValidSelectors,k)
				                     }
				                     for _,line:=range v {
				                          match:=re.FindAllStringSubmatch(line, -1)
				                          if match != nil {
				                              attr,op,_:=match[0][1],match[0][2],match[0][3]
				                              if availops,ok:=SelectorOpMaps[attr]; ok{
				                                  if !Contains(availops, op) {
				                                      errs = append(errs,fmt.Errorf("invalid operation in selector \"%s\": the valid operation for selector \"%s\": %s",line,attr,availops))
				                                  }
				                              } else {
				                                      errs = append(errs,fmt.Errorf("invalid selector \"%s\": the valid selectors \"%s\"",line,strings.Join(ValidSelectors,",")))
				                              }
				                          }
				                     }
				                     return
				                   },
				*/
			},
			"name": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"machinetype": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"arch": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"disksize": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"memory": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"cputype": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"cpucount": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"gpu": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"ib": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"ip": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"mac": {
				Type:     schema.TypeList,
				Optional: true,
				Computed: true,
				Elem:     &schema.Schema{Type: schema.TypeString},
			},
			"rack": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"unit": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"room": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"height": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"osimage": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"powerstatus": {
				Type:         schema.TypeString,
				Optional:     true,
				Computed:     true,
				ValidateFunc: validation.StringInSlice([]string{"on", "off"}, true),
			},
			"sshusername": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
			"sshpassword": {
				Type:     schema.TypeString,
				Optional: true,
				Computed: true,
			},
		},
		SchemaVersion: 0,
		//MigrateState: resourceExampleInstanceMigrateState,
		Timeouts: &schema.ResourceTimeout{
			Create: schema.DefaultTimeout(30 * time.Minute),
		},
	}
}

/*
func resourceExampleInstanceMigrateState(v int, inst *terraform.InstanceState, meta interface{}) (*terraform.InstanceState, error) {
    switch v {
    case 0:
        log.Println("[INFO] Found Example Instance State v0; migrating to v1")
        return migrateExampleInstanceStateV0toV1(inst)
    default:
        return inst, fmt.Errorf("Unexpected schema version: %d", v)
    }
}

func migrateExampleInstanceStateV0toV1(inst *terraform.InstanceState) (*terraform.InstanceState, error) {
    if inst.Empty() {
        log.Println("[DEBUG] Empty InstanceState; nothing to migrate.")
        return inst, nil
    }

    if !strings.HasSuffix(inst.Attributes["name"], ".") {
        log.Printf("[DEBUG] Attributes before migration: %#v", inst.Attributes)
        inst.Attributes["name"] = inst.Attributes["name"] + "."
        log.Printf("[DEBUG] Attributes after migration: %#v", inst.Attributes)
    }

    return inst, nil
}
*/

func resourceNodeCreate(d *schema.ResourceData, meta interface{}) error {
	config := meta.(*Config)
	selectors := Intf2Map(d.Get("selectors"))
	log.Printf("----------------%v", selectors)

	nodename := d.Get("name")
	if nodename != nil && nodename != "" {
		selectors["name"] = nodename.(string)
	}

	token := config.Token
	url := config.Url
	systemSyncLock.Lock()
	out, errcode, errmsg := ApplyNodes(url, token, selectors)
	systemSyncLock.Unlock()
	if errcode != 0 {
		return fmt.Errorf(errmsg)
	}

	node := out

	osimage := d.Get("osimage")
	provisioned := 0
	if osimage != nil && osimage != "" {

		_, errcode, errmsg := ProvisionNode(node, url, token, osimage.(string))
		if errcode != 0 {
			log.Printf("releasenode %s", node)
			ReleaseNode(node, url, token)
			out := "Failed to provision node " + node + ":" + errmsg
			return fmt.Errorf(out)
		}

		log.Printf("%v", resource.Retry(d.Timeout(schema.TimeoutCreate), func() *resource.RetryError {
			status, errcode, errmsg := ListNodeStatus(node, url, token)

			if errcode != 0 {
				log.Printf("Error to get status of node %s: %s", node, errmsg)
				return resource.NonRetryableError(fmt.Errorf("Error to get status of node %s: %s", node, errmsg))
			}

			if status != "booted" {
				log.Printf("Expected instance to be \"booted\" but was in state %s", status)
				return resource.RetryableError(fmt.Errorf("Expected instance to be \"booted\" but was in state %s", status))
			}

			provisioned = 1
			log.Printf("instance %s provisioned!", node)
			return resource.NonRetryableError(fmt.Errorf("instance %s provisioned!", node))
		}))

		if provisioned == 0 {
			ReleaseNode(node, url, token)
			return fmt.Errorf("node instance %s provision timeout!", node)
		}
	}

	powerstatus := d.Get("powerstatus")
	powered := 0
	var statusstring string
	if powerstatus != nil && powerstatus != "" {
		statusstring = powerstatus.(string)
		_, errcode, errmsg := SetPowerStatus(node, url, token, statusstring)
		if errcode != 0 {
			ReleaseNode(node, url, token)
			return fmt.Errorf("Fail to set powerstatus of instance  %s to %s: %s!", node, statusstring, errmsg)
		}
		log.Printf("%v", resource.Retry(d.Timeout(schema.TimeoutCreate), func() *resource.RetryError {
			status, errcode, errmsg := ListNodePowerStatus(node, url, token)
			if errcode != 0 {
				log.Printf("Error to get status of node %s: %s", node, errmsg)
				return resource.NonRetryableError(fmt.Errorf("Error to get status of node %s: %s", node, errmsg))
			}
			if status != statusstring {
				log.Printf("Expected instance to be \"%s\" but was in state %s", statusstring, status)
				return resource.RetryableError(fmt.Errorf("Expected instance to be \"%s\" but was in state %s", statusstring, status))
			}
			powered = 1
			log.Printf("instance %s powered!", node)
			return resource.NonRetryableError(fmt.Errorf("instance %s powered!", node))
		}))
		if powered == 0 {
			ReleaseNode(node, url, token)
			return fmt.Errorf("node instance %s powered timeout!", node)
		} else {
			d.Set("powerstatus", statusstring)
		}
	}

	d.SetId(node)
	d.Set("name", node)
	return resourceNodeRead(d, meta)
}

func resourceNodeRead(d *schema.ResourceData, meta interface{}) error {
	node := d.Get("name").(string)
	config := meta.(*Config)
	token := config.Token
	url := config.Url

	info, err, errmsg := ListNodeDetail(node, url, token)
	if err != 0 {
		log.Printf("Failed to read node resource " + node + " from xcat: " + errmsg)
	}

	status, errcode, errmsg := ListNodePowerStatus(node, url, token)
	if errcode != 0 {
		log.Printf("Failed to read node power status " + node + " from xcat: " + errmsg)
	}

	NodeInv2Res(info, d, node, status)
	return nil
}

func resourceNodeUpdate(d *schema.ResourceData, meta interface{}) error {
	config := meta.(*Config)
	node := d.Get("name").(string)
	token := config.Token
	url := config.Url

	d.Partial(true)
	if d.HasChange("osimage") {
		oldOsimage_v, newOsimage_v := d.GetChange("osimage")
		oldOsimage := oldOsimage_v.(string)
		newOsimage := newOsimage_v.(string)
		log.Printf("%s=========%s", oldOsimage, newOsimage)
		osimage := newOsimage
		if osimage != "" {

			_, errcode, errmsg := ProvisionNode(node, url, token, osimage)
			if errcode != 0 {
				out := "Failed to provision node " + node + ":" + errmsg
				return fmt.Errorf(out)
			}

			provisioned := 0

			log.Printf("%v", resource.Retry(d.Timeout(schema.TimeoutCreate), func() *resource.RetryError {
				status, errcode, errmsg := ListNodeStatus(node, url, token)

				if errcode != 0 {
					log.Printf("Error to get status of node %s: %s", node, errmsg)
					return resource.NonRetryableError(fmt.Errorf("Error to get status of node %s: %s", node, errmsg))
				}

				if status != "booted" {
					log.Printf("Expected instance to be \"booted\" but was in state %s", status)
					return resource.RetryableError(fmt.Errorf("Expected instance to be \"booted\" but was in state %s", status))
				}

				provisioned = 1
				log.Printf("instance %s provisioned!", node)
				return resource.NonRetryableError(fmt.Errorf("instance %s provisioned!", node))
			}))

			if provisioned == 0 {
				return fmt.Errorf("node instance %s provision timeout!", node)
			}
			d.SetPartial("osimage")
		}
	}

	if d.HasChange("powerstatus") {
		//oldPowerStatus_v, newPowerStatus_v := d.GetChange("powerstatus")
		_, newPowerStatus_v := d.GetChange("powerstatus")
		//oldPowerStatus:=oldPowerStatus_v.(string)
		newPowerStatus := newPowerStatus_v.(string)
		powered := 0

		_, errcode, errmsg := SetPowerStatus(node, url, token, newPowerStatus)
		if errcode != 0 {
			return fmt.Errorf("Fail to set powerstatus of instance  %s to %s: %s!", node, newPowerStatus, errmsg)
		}
		log.Printf("%v", resource.Retry(d.Timeout(schema.TimeoutCreate), func() *resource.RetryError {
			status, errcode, errmsg := ListNodePowerStatus(node, url, token)
			if errcode != 0 {
				log.Printf("Error to get status of node %s: %s", node, errmsg)
				return resource.NonRetryableError(fmt.Errorf("Error to get status of node %s: %s", node, errmsg))
			}
			if status != newPowerStatus {
				log.Printf("Expected instance to be \"%s\" but was in state %s", newPowerStatus, status)
				return resource.RetryableError(fmt.Errorf("Expected instance to be \"%s\" but was in state %s", newPowerStatus, status))
			}
			powered = 1
			log.Printf("instance %s powered!", node)
			return resource.NonRetryableError(fmt.Errorf("instance %s powered!", node))
		}))
		if powered == 0 {
			return fmt.Errorf("node instance %s powered timeout!", node)
		}
		d.SetPartial("powerstatus")
	}

	d.Partial(false)
	return resourceNodeRead(d, meta)
}

func resourceNodeDelete(d *schema.ResourceData, meta interface{}) error {

	config := meta.(*Config)
	url := config.Url
	token := config.Token
	node := d.Get("name").(string)
	_, errorcode, errormessage := ReleaseNode(node, url, token)
	if errorcode != 0 {
		return fmt.Errorf(errormessage)
	}
	return nil
}

func Intf2Map(v interface{}) map[string]string {
	m := v.([]interface{})
	var tags []string
	retmap := make(map[string]string)
	re := regexp.MustCompile(`([^=!~><]+)([=!~><]{1,2})([^=!~><]+)`)
	for _, line := range m {
		match := re.FindAllStringSubmatch(line.(string), -1)
		if match != nil {
			attr, op, value := match[0][1], match[0][2], match[0][3]
			if attr == "gpu" || attr == "ib" {
				if value == "1" {
					tags = append(tags, attr)
				} else if value == "0" {
					tags = append(tags, "-"+attr)
				}
				continue
			}
			if op != "=" {
				value = op + value
			}
			retmap[attr] = value
		}

	}
	if len(tags) != 0 {
		retmap["tags"] = strings.Join(tags, ",")
	}
	return retmap
}

var SelectorOpMaps = map[string][]string{
	"disksize":    []string{"=", ">", ">=", "<", "<="},
	"memory":      []string{"=", ">", ">=", "<", "<="},
	"cpucount":    []string{"=", ">", ">=", "<", "<="},
	"cputype":     []string{"=", "!=", "!~", "=~"},
	"machinetype": []string{"="},
	"name":        []string{"="},
	"rack":        []string{"="},
	"unit":        []string{"="},
	"room":        []string{"="},
	"arch":        []string{"="},
	"gpu":         []string{"="},
	"ib":          []string{"="},
}

var DictRes2Inv = map[string]string{
	"machinetype": "device_info.mtm",
	"arch":        "device_info.arch",
	"disksize":    "device_info.disksize",
	"memory":      "device_info.memory",
	"cputype":     "device_info.cputype",
	"cpucount":    "device_info.cpucount",
	"ip":          "network_info.primarynic.ip",
	"mac":         "network_info.primarynic.mac",
	"rack":        "position_info.rack",
	"unit":        "position_info.unit",
	"room":        "position_info.room",
	"height":      "position_info.height",
	"osimage":     "engines.netboot_engine.engine_info.osimage",
	"tags":        "obj_info.description",
}

func Res2DefAttr(resattr string) string {
	if resattr == "machinetype" {
		return "mtm"
	}
	return resattr
}

func NodeInv2Res(myjson string, d *schema.ResourceData, node string, status string) int {
	keys := reflect.ValueOf(DictRes2Inv).MapKeys()
	tagmatch := regexp.MustCompile(`tags:\[(.*)\]`)
	for _, kres := range keys {
		kinv := DictRes2Inv[kres.String()]
		val := gjson.Get(myjson, "spec."+kinv).String()
		if val != "" {
			if strings.Contains(val, "tags:") {
				tags := tagmatch.FindStringSubmatch(val)
				tags_list := strings.Split(tags[1], ",")
				for _, v := range tags_list {
					d.Set(v, 1)
				}
			} else {
				d.Set(kres.String(), val)
			}
		} else {
			d.Set(kres.String(), nil)
		}
	}
	if status != "" {
		d.Set("powerstatus", status)
	}
	return 0
}
