package xcat

import (
	"reflect"
	//    "log"
	//    "strings"
)

//check whether string x is in string list a
func Contains(a []string, x string) bool {
	for _, n := range a {
		if x == n {
			return true
		}
	}
	return false

}

// get value from netsted
func typeof(v interface{}) string {
	return reflect.TypeOf(v).String()
}

//convert
func MapConvInt2Str(data map[string]interface{}) map[string]string {
	form := make(map[string]string)

	for k, v := range data {
		form[k] = v.(string)
	}
	return form
}
