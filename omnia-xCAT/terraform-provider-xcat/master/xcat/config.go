package xcat

import (
	"fmt"
)

type Config struct {
	Url      string
	Username string
	Password string

	Token string
}

func (c *Config) loadAndValidate() error {
	_, errcode, errmsg := CheckTokenValidate(c.Url, c.Token)
	if errcode != 0 {
		return fmt.Errorf(errmsg)
	}
	return nil
}
