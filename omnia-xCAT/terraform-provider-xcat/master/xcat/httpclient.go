package xcat

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"io/ioutil"
	"net/http"
	"net/url"
	"strconv"
)

type HttpClient struct {
	Client  *http.Client
	Headers http.Header
}

func (s *HttpClient) request(method, url string, headers *http.Header, token interface{}, body io.Reader) (req *http.Request, err error) {
	req, err = http.NewRequest(method, url, body)
	if err != nil {
		return nil, err
	}

	if headers == nil && body != nil {
		headers = &http.Header{}
		headers.Add("Content-Type", "application/json")
		req.Header = *headers
	}
	return
}

func (s *HttpClient) Request(method string, url string, params *url.Values, headers *http.Header, token interface{}, body *[]byte, retRaw bool) (data interface{}, err error) {
	// add params to url here
	if params != nil {
		url = url + "?" + params.Encode()
	}

	// Get the body if one is present
	var buf io.Reader
	if body != nil {
		buf = bytes.NewReader(*body)
	}
	req, err := s.request(method, url, headers, token, buf)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", "application/json")
	if token != nil {
		req.Header.Add("Authorization", "token "+token.(string))
	}
	var resp *http.Response
	resp, err = s.Do(req)
	if err != nil {
		return nil, err
	}
	err = CheckHTTPResponseStatusCode(resp)
	if err != nil {
		rbody, _ := ioutil.ReadAll(resp.Body)
		if rbody != nil {
			val := make(map[string]interface{})
			errjson := json.Unmarshal([]byte(rbody), &val)
			if errjson != nil {
				return "No message from response", err
			}
			return val["message"], err
		}
		return nil, err
	}
	rbody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, errors.New("Can not read the message form response")
	}
	if retRaw == true {
		return string(rbody), nil
	}
	if err = json.Unmarshal(rbody, &data); err != nil {
		return nil, err
	}
	return data, nil
}

func (s *HttpClient) Do(req *http.Request) (*http.Response, error) {
	for k := range s.Headers {
		req.Header.Set(k, s.Headers.Get(k))
	}
	resp, err := s.Client.Do(req)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

func (s *HttpClient) Get(url string, params *url.Values, token interface{}, body interface{}, retRaw bool) (interface{}, error) {
	var resp interface{}
	var err error
	if body != nil {
		bodyJson, _ := json.Marshal(body)
		resp, err = s.Request("GET", url, params, nil, token, &bodyJson, retRaw)
	} else {
		resp, err = s.Request("GET", url, params, nil, token, nil, retRaw)
	}
	return resp, err
}

func (s *HttpClient) Post(url string, params *url.Values, token interface{}, body interface{}, retRaw bool) (interface{}, error) {
	bodyJson, err := json.Marshal(body)
	resp, err := s.Request("POST", url, params, nil, token, &bodyJson, retRaw)
	return resp, err
}

func (s *HttpClient) Put(url string, params *url.Values, token interface{}, body interface{}, retRaw bool) (interface{}, error) {
	var resp interface{}
	var err error
	if body != nil {
		bodyJson, _ := json.Marshal(body)
		resp, err = s.Request("PUT", url, params, nil, token, &bodyJson, retRaw)
	} else {
		resp, err = s.Request("PUT", url, params, nil, token, nil, retRaw)
	}
	return resp, err
}

func (s *HttpClient) Delete(url string, params *url.Values, token interface{}, body interface{}, retRaw bool) (interface{}, error) {
	var resp interface{}
	var err error
	if body != nil {
		bodyJson, _ := json.Marshal(body)
		resp, err = s.Request("DELETE", url, params, nil, token, &bodyJson, retRaw)
	} else {
		resp, err = s.Request("DELETE", url, params, nil, token, nil, retRaw)
	}
	return resp, err
}

func (s *HttpClient) Patch(url string, params *url.Values, token interface{}, body interface{}, retRaw bool) (interface{}, error) {
	bodyJson, err := json.Marshal(body)
	resp, err := s.Request("PATCH", url, params, nil, token, &bodyJson, retRaw)
	return resp, err
}

func CheckHTTPResponseStatusCode(resp *http.Response) error {
	switch resp.StatusCode {
	case 200, 201, 202, 204, 206:
		return nil
	default:
		return errors.New(strconv.Itoa(resp.StatusCode))
	}
}
