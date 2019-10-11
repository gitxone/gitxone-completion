package completion

import (
	"fmt"
	"io/ioutil"
	"path/filepath"
	"strings"
)

type Status struct {
	state    int
	values   []string
	optional bool
}

const (
	_ int = iota
	DONE
	SHORT
	WAITING
	OPTIONAL
	INVALID
	REMOVED
)

func Complete(path string, tokens []string) []string {
	lastToken := tokens[len(tokens)-1]
	if len(tokens) < 2 {
		filtered := make([]string, 0)
		for _, c := range gitCommands {
			index := len(lastToken)
			if index <= len(c) && c[0:index] == lastToken {
				filtered = append(filtered, c)
			}
		}
		return filtered
	}

	options, ok := Options[tokens[0]]
	if !ok {
		return []string{}
	}
	result := make([]string, 0)
	for _, suggestion := range suggest(options, tokens[1:len(tokens)-1]) {
		if suggestion == "" {
			continue
		}
		v, marked := ValueTypes[suggestion]
		if !marked {
			result = append(result, suggestion)
			continue
		}
		switch v {
		case "<file>":
			result = append(result, getFiles(path, lastToken)...)
		default:
			result = append(result, v)
		}
	}
	return result
}

func (t *Option) getValues(key string) ([]string, []bool, bool) {
	values := make([]string, 0)
	multiple := make([]bool, 0)
	for i, k := range t.Keys {
		if k == key {
			values = append(values, t.Values[i])
			multiple = append(multiple, t.Multiple[i])
		}
	}
	return values, multiple, len(values) != 0
}

func suggest(options []Option, tokens []string) []string {
	done := make(map[int]Status, 0)

	// marking loop
	for serial, option := range options { //options
		multiple := false
		for _, token := range tokens {
			if token == "" {
				continue
			}
			status, marked := done[serial]
			if marked && status.state == DONE {
				break
			}
			if marked && status.state == REMOVED {
				break
			}
			if marked && status.state == OPTIONAL {
				if token[0] != '-' {
					status.state = DONE
					done[serial] = status
					break
				}
			}
			if marked && status.state == SHORT {
				if token[0] == '-' {
					status.state = INVALID
					done[serial] = status
					break
				}
				if multiple {
					status.state = WAITING
				} else {
					status.state = DONE
				}
				done[serial] = status
			}

			values, multiple, found := option.getValues(token)
			if found {
				joined := strings.Join(values, "")
				firstValue := values[0]
				for _, s := range option.InvalidSerials {
					done[s] = Status{REMOVED, values, false}
				}
				if joined == "" {
					if multiple[0] {
						done[serial] = Status{WAITING, values, false}
					} else {
						done[serial] = Status{DONE, values, false}
					}
				} else if firstValue[len(firstValue)-1] == '?' {
					vs := make([]string, 0)
					for _, v := range values {
						vs = append(vs, strings.Trim(v, "?"))
					}
					done[serial] = Status{OPTIONAL, vs, true}
				} else {
					done[serial] = Status{SHORT, values, false}
				}
			}
		}
	}

	result := make([]string, 0)
	// extracting short loop
	for serial := range options {
		status, marked := done[serial]
		if marked && status.state == SHORT {
			for _, v := range status.values {
				result = append(result, formatStringAsValue(v))
			}
			return result
		}
	}
	// removing loop
	group := 0
	trailing := false
	for serial, option := range options {
		if group != option.Group {
			group = option.Group
			trailing = false
		}
		status, marked := done[serial]
		if !trailing && !marked && !option.Optional {
			trailing = true
			continue
		}
		if trailing {
			status.state = REMOVED
			done[serial] = status
		}
	}

	// extracting loop
	for serial, option := range options {
		status, _ := done[serial]
		switch status.state {
		case DONE:
			continue
		case INVALID:
			continue
		case REMOVED:
			continue
		//case SHORT:
		//	result = append(result, status.value)
		//	break
		}
		result = append(result, option.Keys...)
		for index, v := range option.Values {
			if v == "" || option.Keys[index] != "" {
				continue
			}
			if v[len(v)-1] == '?' {
				v = v[:len(v)-1]
			}
			result = append(result, formatStringAsValue(v))
		}
	}
	return result
}

func formatStringAsValue(value string) string {
	if value == "" {
		return ""
	}
	if value[0] == '-' || value[0] == '=' {
		return value[1:]
	}
	values := make([]string, 0)
	for _, s := range strings.Split(value, " ") {
		values = append(values, fmt.Sprintf("<%s>", s))
	}
	return strings.Join(values, " ")
}

func getFiles(path string, lastToken string) []string {
	dirName, bits := filepath.Split(lastToken)
	joinedPath := filepath.Join(path, dirName)

	files, _ := ioutil.ReadDir(joinedPath)
	paths := make([]string, 0)

	for _, f := range files {
		fileName := f.Name()
		p := filepath.Join(dirName, fileName)
		if f.IsDir() {
			p += "/"
		}
		if strings.HasPrefix(fileName, bits) {
			paths = append(paths, p)
		}
	}
	return paths
}

