package analyzer

import (
	"bytes"
	"fmt"
	"sync"
	"time"
)

type LRUMap struct {
	mutex 		sync.Mutex
	timeout		time.Duration
	size 		int
	capacity	int
	cache		map[uint64]*LRUNode
	timeList	*LRUList
}

func (lru *LRUMap) TimeList() string {
	return lru.timeList.String()
}

func NewLRUMap(timeout time.Duration) *LRUMap {
	return &LRUMap{
		mutex:    sync.Mutex{},
		timeout:  timeout,
		size:     0,
		capacity: 0,
		cache:    make(map[uint64]*LRUNode),
		timeList: NewLRUList(),
	}
}

func (lru *LRUMap) Size() int {
	return lru.size
}

func (lru *LRUMap) Put(key uint64, flow *FlowRecord) {
	lru.mutex.Lock()
	defer lru.mutex.Unlock()

	_, ok := lru.cache[key]
	if !ok {
		node := NewLRUNode(key, flow)
		lru.cache[key] = &node
		lru.timeList.insertToFront(&node)
	}

	lru.size++
}

func (lru *LRUMap) Get(key uint64) (*FlowRecord, bool) {
	lru.mutex.Lock()
	defer lru.mutex.Unlock()

	node, ok := lru.cache[key]
	if !ok {
		return nil, false
	}

	lru.updateTime(node)
	return node.flow, true
}

func (lru *LRUMap) internalRemove(key uint64) *FlowRecord {
	node, ok := lru.cache[key]
	if !ok {
		return nil
	}

	lru.timeList.remove(node)
	delete(lru.cache, key)
	lru.size--

	return node.flow
}

func (lru *LRUMap) Remove(key uint64) *FlowRecord {
	lru.mutex.Lock()
	defer lru.mutex.Unlock()

	return lru.internalRemove(key)
}

func (lru *LRUMap) RemoveByTime() []*FlowRecord {
	lru.mutex.Lock()
	defer lru.mutex.Unlock()

	if lru.size < 1 {
		return nil
	}

	flows := make([]*FlowRecord, 0)
	now := time.Now()
	node := lru.timeList.tail
	for node != nil {
		tmp := node.prev
		if now.Sub(node.visit) >= lru.timeout {
			flow := lru.internalRemove(node.key)
			flows = append(flows, flow)
		}
		node = tmp
	}

	return flows
}


func (lru *LRUMap) updateTime(node *LRUNode) {
	node.visit = time.Now()

	lru.timeList.remove(node)
	lru.timeList.insertToFront(node)
}


type LRUList struct {
	size		int
	head		*LRUNode
	tail 		*LRUNode
}

func NewLRUList() *LRUList {
	return &LRUList{
		head: nil,
		tail: nil,
	}
}

func (l *LRUList) Size() int {
	return l.size
}

func (l *LRUList) insertToFront(node *LRUNode) {
	if node.next != nil || node.prev != nil {
		return
	}

	if l.head != nil {
		node.next = l.head
		l.head.prev = node
	}
	l.head = node
	if l.tail == nil {
		l.tail = node
	}

	l.size++
}

func (l *LRUList) remove(node *LRUNode) {
	prev := node.prev
	next := node.next
	if prev != nil {
		prev.next = node.next
	} else {
		l.head = next
	}

	if next != nil {
		next.prev = node.prev
	} else {
		l.tail = prev
	}

	node.next = nil
	node.prev = nil
	l.size--
}

func (l *LRUList) String() string {
	var buffer bytes.Buffer
	buffer.WriteString("front line: ")
	node := l.head
	for node != nil {
		buffer.WriteString(fmt.Sprintf("%d => ", node.key))
		node = node.next
	}
	buffer.WriteString("\n")

	buffer.WriteString("back line:  ")
	node = l.tail
	for node != nil {
		buffer.WriteString(fmt.Sprintf("%d => ", node.key))
		node = node.prev
	}
	buffer.WriteString("\n")

	return buffer.String()
}


type LRUNode struct {
	key		uint64
	flow	*FlowRecord
	next	*LRUNode
	prev	*LRUNode
	visit	time.Time
}

func NewLRUNode(key uint64, flow *FlowRecord) LRUNode {
	return LRUNode{
		key:	key,
		flow: flow,
		next: nil,
		prev: nil,
		visit:time.Now(),
	}
}